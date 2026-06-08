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

    topic: str  # 消息所属的主题名称。
    payload: dict[str, Any]  # 消息承载的业务数据。
    headers: dict[str, str] = field(default_factory=dict)  # 消息头信息，用于传递追踪或路由元数据。
    message_id: str = field(default_factory=lambda: str(uuid4()))  # 消息唯一标识。
    schema_version: str = "v1"  # 消息结构版本号。
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))  # 消息发生时间（UTC）。

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

    name: str  # 能力名称。
    description: str = ""  # 能力说明。


@dataclass(frozen=True, slots=True)
class AgentCard:
    """描述一个可被注册和调度的智能体。"""

    agent_id: str  # 智能体唯一标识。
    display_name: str  # 智能体显示名称。
    version: str = "1.0.0"  # 智能体版本号。
    capabilities: tuple[AgentCapability, ...] = ()  # 智能体能力列表。
    endpoint: str | None = None  # 智能体服务地址。
    webhook_path: str | None = None  # 智能体回调路径。
    data_scopes: tuple[str, ...] = ()  # 智能体可访问的数据范围。
    max_concurrent_tasks: int = 1  # 智能体允许同时处理的任务数上限。
    metadata: dict[str, Any] = field(default_factory=dict)  # 扩展元数据。

    def capability_names(self) -> tuple[str, ...]:
        """返回当前智能体所有能力名称。"""
        return tuple(cap.name for cap in self.capabilities)
