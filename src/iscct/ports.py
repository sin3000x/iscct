from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from .domain import AgentCard, QueueMessage


QueueHandler = Callable[[QueueMessage], Any]


class EventBus(ABC):
    @abstractmethod
    def publish(self, topic: str, message: dict[str, Any], headers: dict[str, str] | None = None) -> str:
        raise NotImplementedError

    @abstractmethod
    def subscribe(
        self,
        topic: str,
        handler: QueueHandler,
        consumer_group: str | None = None,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def ack(self, delivery: Any) -> None:
        raise NotImplementedError

    @abstractmethod
    def nack(self, delivery: Any, requeue: bool = True) -> None:
        raise NotImplementedError

    @abstractmethod
    def publish_to_dlq(self, message: dict[str, Any], reason: str) -> str:
        raise NotImplementedError


class AgentRuntime(ABC):
    @abstractmethod
    def accept_task(self, task: dict[str, Any]) -> str:
        raise NotImplementedError

    @abstractmethod
    def report_progress(self, task_id: str, progress: dict[str, Any]) -> None:
        raise NotImplementedError

    @abstractmethod
    def submit_result(self, task_id: str, result: dict[str, Any]) -> None:
        raise NotImplementedError

    @abstractmethod
    def heartbeat(self) -> None:
        raise NotImplementedError


class AgentRegistry(ABC):
    @abstractmethod
    def register(self, agent: AgentCard) -> AgentCard:
        raise NotImplementedError

    @abstractmethod
    def get(self, agent_id: str) -> AgentCard | None:
        raise NotImplementedError

    @abstractmethod
    def list(self) -> tuple[AgentCard, ...]:
        raise NotImplementedError
