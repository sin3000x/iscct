from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

from .domain import AgentCard, QueueMessage
from .ports import AgentRegistry, AgentRuntime, EventBus, QueueHandler
from .tasking import AssigneeType, Task, TaskProgressEvent, TaskStatus


@dataclass(slots=True)
class InMemoryEventBus(EventBus):
    published: list[QueueMessage] = field(default_factory=list)
    subscriptions: dict[str, list[QueueHandler]] = field(default_factory=dict)

    def publish(self, topic: str, message: dict[str, Any], headers: dict[str, str] | None = None) -> str:
        queue_message = QueueMessage(topic=topic, payload=message, headers=headers or {})
        self.published.append(queue_message)
        for handler in self.subscriptions.get(topic, []):
            handler(queue_message)
        return queue_message.message_id

    def subscribe(self, topic: str, handler: QueueHandler, consumer_group: str | None = None) -> None:
        self.subscriptions.setdefault(topic, []).append(handler)

    def ack(self, delivery: Any) -> None:
        return None

    def nack(self, delivery: Any, requeue: bool = True) -> None:
        return None

    def publish_to_dlq(self, message: dict[str, Any], reason: str) -> str:
        return self.publish("ct.dlq", {**message, "reason": reason})


@dataclass(slots=True)
class InMemoryAgentRegistry(AgentRegistry):
    agents: dict[str, AgentCard] = field(default_factory=dict)

    def register(self, agent: AgentCard) -> AgentCard:
        self.agents[agent.agent_id] = agent
        return agent

    def get(self, agent_id: str) -> AgentCard | None:
        return self.agents.get(agent_id)

    def list(self) -> tuple[AgentCard, ...]:
        return tuple(self.agents.values())


@dataclass(slots=True)
class AgentRegistrationService:
    registry: AgentRegistry

    def register(self, agent: AgentCard) -> AgentCard:
        return self.registry.register(agent)


@dataclass(slots=True)
class InMemoryAgentRuntime(AgentRuntime):
    accepted_tasks: list[dict[str, Any]] = field(default_factory=list)
    progress_events: list[dict[str, Any]] = field(default_factory=list)
    results: list[dict[str, Any]] = field(default_factory=list)
    heartbeats: int = 0

    def accept_task(self, task: dict[str, Any]) -> str:
        self.accepted_tasks.append(task)
        return str(task.get("task_id", ""))

    def report_progress(self, task_id: str, progress: dict[str, Any]) -> None:
        self.progress_events.append({"task_id": task_id, **progress})

    def submit_result(self, task_id: str, result: dict[str, Any]) -> None:
        self.results.append({"task_id": task_id, **result})

    def heartbeat(self) -> None:
        self.heartbeats += 1


@dataclass(slots=True)
class InMemoryTaskStore:
    tasks: dict[str, Task] = field(default_factory=dict)
    progress: dict[str, list[TaskProgressEvent]] = field(default_factory=dict)

    def create(self, task: Task) -> Task:
        self.tasks[task.task_id] = task
        return task

    def get(self, task_id: str) -> Task | None:
        return self.tasks.get(task_id)

    def list(self) -> tuple[Task, ...]:
        return tuple(self.tasks.values())

    def update(self, task: Task) -> Task:
        self.tasks[task.task_id] = task
        return task

    def append_progress(self, event: TaskProgressEvent) -> TaskProgressEvent:
        self.progress.setdefault(event.task_id, []).append(event)
        task = self.tasks.get(event.task_id)
        if task is None:
            return event
        updated = replace(task, current_stage=event.stage, progress_percent=event.progress_percent)
        self.tasks[event.task_id] = updated
        return event

    def task_progress(self, task_id: str) -> tuple[TaskProgressEvent, ...]:
        return tuple(self.progress.get(task_id, []))


@dataclass(slots=True)
class TaskDispatchService:
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
            trace_id=trace_id or Task().trace_id,
        )
        return self.task_store.create(task)

    def dispatch(self, task_id: str) -> Task:
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
