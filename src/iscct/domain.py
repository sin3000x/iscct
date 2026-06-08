from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


class QueueDeliveryStatus(str, Enum):
    """队列投递结果状态。

    该枚举用于记录消息在事件总线中的最终处理结果。
    """

    ACKED = "acked"
    NACKED = "nacked"


@dataclass(frozen=True, slots=True)
class QueueMessage:
    """表示队列中的一条消息。

    该对象保留消息的主题、负载、头信息以及生成时的元数据，
    便于在不同处理环节之间稳定传递。
    """

    topic: str
    payload: dict[str, Any]
    headers: dict[str, str] = field(default_factory=dict)
    message_id: str = field(default_factory=lambda: str(uuid4()))
    schema_version: str = "v1"
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def with_headers(self, **extra_headers: str) -> "QueueMessage":
        """返回一个合并了额外头信息的新消息。

        不修改当前实例，适合在中间件层附加追踪信息、链路信息等。
        """
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
    """描述智能体具备的一项能力。"""

    name: str
    description: str = ""


@dataclass(frozen=True, slots=True)
class AgentCard:
    """描述一个可被注册和调度的智能体。"""

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
        """返回当前智能体所有能力名称。"""
        return tuple(cap.name for cap in self.capabilities)
