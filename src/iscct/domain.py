from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


class QueueDeliveryStatus(str, Enum):
    ACKED = "acked"
    NACKED = "nacked"


@dataclass(frozen=True, slots=True)
class QueueMessage:
    topic: str
    payload: dict[str, Any]
    headers: dict[str, str] = field(default_factory=dict)
    message_id: str = field(default_factory=lambda: str(uuid4()))
    schema_version: str = "v1"
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def with_headers(self, **extra_headers: str) -> "QueueMessage":
        merged = {**self.headers, **extra_headers}
        return QueueMessage(
            topic=self.topic,
            payload=dict(self.payload),
            headers=merged,
            message_id=self.message_id,
            schema_version=self.schema_version,
            occurred_at=self.occurred_at,
        )


@dataclass(frozen=True, slots=True)
class AgentCapability:
    name: str
    description: str = ""


@dataclass(frozen=True, slots=True)
class AgentCard:
    agent_id: str
    display_name: str
    version: str = "1.0.0"
    capabilities: tuple[AgentCapability, ...] = ()
    endpoint: str | None = None
    webhook_path: str | None = None
    data_scopes: tuple[str, ...] = ()
    max_concurrent_tasks: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)

    def capability_names(self) -> tuple[str, ...]:
        return tuple(cap.name for cap in self.capabilities)
