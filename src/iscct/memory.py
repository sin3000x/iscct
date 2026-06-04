from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .domain import AgentCard, QueueMessage
from .ports import AgentRegistry, AgentRuntime, EventBus, QueueHandler


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
