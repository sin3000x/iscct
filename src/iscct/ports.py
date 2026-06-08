from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from .domain import AgentCard, QueueMessage


QueueHandler = Callable[[QueueMessage], Any]


class EventBus(ABC):
    """事件总线的抽象接口。

    统一抽象发布、订阅、确认和死信处理能力，便于替换不同消息中间件。
    """

    @abstractmethod
    def publish(self, topic: str, message: dict[str, Any], headers: dict[str, str] | None = None) -> str:
        """发布一条消息到指定主题。"""
        raise NotImplementedError

    @abstractmethod
    def subscribe(
        self,
        topic: str,
        handler: QueueHandler,
        consumer_group: str | None = None,
    ) -> None:
        """订阅指定主题的消息。"""
        raise NotImplementedError

    @abstractmethod
    def ack(self, delivery: Any) -> None:
        """确认一条消息已被成功处理。"""
        raise NotImplementedError

    @abstractmethod
    def nack(self, delivery: Any, requeue: bool = True) -> None:
        """拒绝一条消息，并按需重新入队。"""
        raise NotImplementedError

    @abstractmethod
    def publish_to_dlq(self, message: dict[str, Any], reason: str) -> str:
        """将消息写入死信队列。"""
        raise NotImplementedError


class AgentRuntime(ABC):
    """智能体运行时的抽象接口。"""

    @abstractmethod
    def accept_task(self, task: dict[str, Any]) -> str:
        """接收并开始处理一个任务。"""
        raise NotImplementedError

    @abstractmethod
    def report_progress(self, task_id: str, progress: dict[str, Any]) -> None:
        """上报任务进度。"""
        raise NotImplementedError

    @abstractmethod
    def submit_result(self, task_id: str, result: dict[str, Any]) -> None:
        """提交任务结果。"""
        raise NotImplementedError

    @abstractmethod
    def heartbeat(self) -> None:
        """发送运行心跳。"""
        raise NotImplementedError


class AgentRegistry(ABC):
    """智能体注册表的抽象接口。"""

    @abstractmethod
    def register(self, agent: AgentCard) -> AgentCard:
        """注册一个智能体。"""
        raise NotImplementedError

    @abstractmethod
    def get(self, agent_id: str) -> AgentCard | None:
        """按 ID 查询智能体。"""
        raise NotImplementedError

    @abstractmethod
    def list(self) -> tuple[AgentCard, ...]:
        """返回所有已注册智能体。"""
        raise NotImplementedError
