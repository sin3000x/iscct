from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

from .domain import AgentCard, QueueMessage
from .ports import AgentRegistry, AgentRuntime, EventBus, QueueHandler
from .tasking import AssigneeType, Task, TaskProgressEvent, TaskStatus


@dataclass(slots=True)
class InMemoryEventBus(EventBus):
    """用于测试和本地开发的内存事件总线。

    该实现会把所有发布过的消息保存在 ``published`` 中，并在发布时
    立即同步调用同主题的订阅处理器，方便单元测试和本地调试。
    """

    published: list[QueueMessage] = field(default_factory=list)  # 已发布消息列表。
    subscriptions: dict[str, list[QueueHandler]] = field(default_factory=dict)  # 主题到订阅处理器的映射。

    def publish(self, topic: str, message: dict[str, Any], headers: dict[str, str] | None = None) -> str:
        """发布消息并同步触发已订阅处理器。

        :param topic: 目标主题名称。
        :param message: 消息负载数据。
        :param headers: 可选的消息头信息。
        :return: 新生成的消息 ID。
        """
        queue_message = QueueMessage(topic=topic, payload=message, headers=headers or {})
        self.published.append(queue_message)
        for handler in self.subscriptions.get(topic, []):
            handler(queue_message)
        return queue_message.message_id

    def subscribe(self, topic: str, handler: QueueHandler, consumer_group: str | None = None) -> None:
        """记录订阅关系，当前实现不区分消费组。

        :param topic: 需要订阅的主题。
        :param handler: 接收到消息后的回调函数。
        :param consumer_group: 预留的消费组名称参数，当前不生效。
        """
        self.subscriptions.setdefault(topic, []).append(handler)

    def ack(self, delivery: Any) -> None:
        """内存实现不需要显式确认消息。

        :param delivery: 待确认的投递对象。
        """
        return None

    def nack(self, delivery: Any, requeue: bool = True) -> None:
        """内存实现不模拟拒绝和重试语义。

        :param delivery: 待拒绝的投递对象。
        :param requeue: 是否重新入队，当前实现不处理该参数。
        """
        return None

    def publish_to_dlq(self, message: dict[str, Any], reason: str) -> str:
        """将消息转发到死信主题。

        :param message: 原始消息负载。
        :param reason: 进入死信队列的原因。
        :return: 新生成的死信消息 ID。
        """
        return self.publish("ct.dlq", {**message, "reason": reason})


@dataclass(slots=True)
class InMemoryAgentRegistry(AgentRegistry):
    """使用字典保存智能体注册信息的内存实现。"""

    agents: dict[str, AgentCard] = field(default_factory=dict)  # 智能体 ID 到智能体卡片的映射。

    def register(self, agent: AgentCard) -> AgentCard:
        """写入或覆盖指定智能体。

        :param agent: 需要注册的智能体对象。
        :return: 保存后的智能体对象。
        """
        self.agents[agent.agent_id] = agent
        return agent

    def get(self, agent_id: str) -> AgentCard | None:
        """按智能体 ID 获取注册信息。

        :param agent_id: 智能体唯一标识。
        :return: 找到则返回智能体信息，否则返回 ``None``。
        """
        return self.agents.get(agent_id)

    def list(self) -> tuple[AgentCard, ...]:
        """返回全部已注册智能体，保持插入顺序。

        :return: 所有智能体组成的不可变元组。
        """
        return tuple(self.agents.values())


@dataclass(slots=True)
class AgentRegistrationService:
    """封装智能体注册流程的轻量服务。"""

    registry: AgentRegistry

    def register(self, agent: AgentCard) -> AgentCard:
        """将智能体交给注册表保存。

        :param agent: 待注册的智能体。
        :return: 注册结果。
        """
        return self.registry.register(agent)


@dataclass(slots=True)
class InMemoryAgentRuntime(AgentRuntime):
    """记录运行时交互痕迹的内存实现。"""

    accepted_tasks: list[dict[str, Any]] = field(default_factory=list)  # 已接收任务列表。
    progress_events: list[dict[str, Any]] = field(default_factory=list)  # 已记录的进度事件列表。
    results: list[dict[str, Any]] = field(default_factory=list)  # 已提交结果列表。
    heartbeats: int = 0  # 心跳计数。

    def accept_task(self, task: dict[str, Any]) -> str:
        """接收任务并返回任务 ID。

        :param task: 任务请求数据。
        :return: 从任务数据中读取到的任务 ID。
        """
        self.accepted_tasks.append(task)
        return str(task.get("task_id", ""))

    def report_progress(self, task_id: str, progress: dict[str, Any]) -> None:
        """记录任务进度上报。

        :param task_id: 任务 ID。
        :param progress: 进度数据。
        """
        self.progress_events.append({"task_id": task_id, **progress})

    def submit_result(self, task_id: str, result: dict[str, Any]) -> None:
        """记录任务结果提交。

        :param task_id: 任务 ID。
        :param result: 结果数据。
        """
        self.results.append({"task_id": task_id, **result})

    def heartbeat(self) -> None:
        """累计一次心跳。"""
        self.heartbeats += 1


@dataclass(slots=True)
class InMemoryTaskStore:
    """用于保存任务和进度事件的内存仓库。"""

    tasks: dict[str, Task] = field(default_factory=dict)
    progress: dict[str, list[TaskProgressEvent]] = field(default_factory=dict)

    def create(self, task: Task) -> Task:
        """创建并保存任务。

        :param task: 待保存的任务对象。
        :return: 保存后的任务对象。
        """
        self.tasks[task.task_id] = task
        return task

    def get(self, task_id: str) -> Task | None:
        """按任务 ID 获取任务。

        :param task_id: 任务唯一标识。
        :return: 找到则返回任务，否则返回 ``None``。
        """
        return self.tasks.get(task_id)

    def list(self) -> tuple[Task, ...]:
        """返回全部任务。

        :return: 所有任务组成的不可变元组。
        """
        return tuple(self.tasks.values())

    def update(self, task: Task) -> Task:
        """覆盖保存任务。

        :param task: 更新后的任务对象。
        :return: 更新后的任务对象。
        """
        self.tasks[task.task_id] = task
        return task

    def append_progress(self, event: TaskProgressEvent) -> TaskProgressEvent:
        """追加任务进度，并同步更新任务的摘要字段。

        :param event: 进度事件。
        :return: 原始进度事件，便于链式调用。
        """
        self.progress.setdefault(event.task_id, []).append(event)
        task = self.tasks.get(event.task_id)
        if task is None:
            return event
        updated = replace(task, current_stage=event.stage, progress_percent=event.progress_percent)
        self.tasks[event.task_id] = updated
        return event

    def task_progress(self, task_id: str) -> tuple[TaskProgressEvent, ...]:
        """获取指定任务的全部进度事件。

        :param task_id: 任务唯一标识。
        :return: 任务对应的全部进度事件元组。
        """
        return tuple(self.progress.get(task_id, []))


@dataclass(slots=True)
class TaskDispatchService:
    """负责创建任务并将任务分发给对应智能体。"""

    task_store: InMemoryTaskStore
    agent_registry: AgentRegistry
    event_bus: EventBus | None = None

    def create_task(
        self,
        *,
        parent_event_id: str,
        task_type: str,
        input_payload: dict[str, Any],
        assignee_id: str,
        assignee_type: AssigneeType = AssigneeType.AGENT,
        assignee_display_name: str = "",
        priority: int = 0,
        policy_version: str = "",
        trace_id: str = "",
    ) -> Task:
        """创建任务并写入任务仓库。

        :param parent_event_id: 上游事件 ID。
        :param task_type: 任务类型。
        :param input_payload: 任务输入数据。
        :param assignee_id: 任务接收者 ID。
        :param assignee_type: 任务接收者类型。
        :param assignee_display_name: 任务接收者显示名。
        :param priority: 任务优先级。
        :param policy_version: 任务策略版本。
        :param trace_id: 链路追踪 ID，未传入时会自动生成。
        :return: 创建并保存后的任务对象。
        """
        trace_id_value = trace_id or Task().trace_id
        task = Task(
            parent_event_id=parent_event_id,
            task_type=task_type,
            input_payload=input_payload,
            assigned_to=assignee_id,
            assignee_type=assignee_type,
            assignee_id=assignee_id,
            assignee_display_name=assignee_display_name,
            priority=priority,
            policy_version=policy_version,
            trace_id=trace_id_value,
        )
        return self.task_store.create(task)

    def dispatch(self, task_id: str) -> Task:
        """将任务标记为已分发，并在需要时发出领域事件。

        :param task_id: 待分发的任务 ID。
        :return: 更新状态后的任务对象。
        :raises KeyError: 当任务或对应智能体不存在时抛出。
        """
        task = self.task_store.get(task_id)
        if task is None:
            raise KeyError(task_id)
        agent = self.agent_registry.get(task.assignee_id)
        if agent is None:
            raise KeyError(task.assignee_id)
        updated = replace(task, status=TaskStatus.DISPATCHED, started_at=task.started_at or task.created_at)
        self.task_store.update(updated)
        if self.event_bus is not None:
            self.event_bus.publish(
                "task.dispatched",
                {
                    "task_id": updated.task_id,
                    "task_type": updated.task_type,
                    "assignee_id": updated.assignee_id,
                    "assignee_display_name": agent.display_name,
                    "assignee_type": updated.assignee_type.value,
                },
            )
        return updated
