from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


class TaskStatus(str, Enum):
    """任务生命周期状态。

    这些状态用于描述任务从创建、分发到完成或回滚的完整生命周期。
    """

    CREATED = "created"
    DISPATCHED = "dispatched"
    IN_PROGRESS = "in_progress"
    AWAITING_HUMAN = "awaiting_human"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLING = "cancelling"
    CANCELLED = "cancelled"
    ROLLING_BACK = "rolling_back"
    ROLLED_BACK = "rolled_back"


class AssigneeType(str, Enum):
    """任务可分配给的执行主体类型。"""

    AGENT = "agent"
    HUMAN = "human"
    CT_AGENT = "ct_agent"
    SYSTEM = "system"


@dataclass(frozen=True, slots=True)
class TaskProgressEvent:
    """描述一次任务进度上报。"""

    progress_id: str = field(default_factory=lambda: str(uuid4()))
    task_id: str = ""
    trace_id: str = ""
    source_type: AssigneeType = AssigneeType.SYSTEM
    source_id: str = ""
    stage: str = ""
    message: str = ""
    progress_percent: int | None = None
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Task:
    """表示一个可调度、可追踪的任务对象。"""

    task_id: str = field(default_factory=lambda: str(uuid4()))
    parent_event_id: str = ""
    task_type: str = ""
    status: TaskStatus = TaskStatus.CREATED
    priority: int = 0
    trace_id: str = field(default_factory=lambda: str(uuid4()))
    assigned_to: str = ""
    assignee_type: AssigneeType = AssigneeType.SYSTEM
    assignee_id: str = ""
    assignee_display_name: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: datetime | None = None
    completed_at: datetime | None = None
    deadline_at: datetime | None = None
    input_payload: dict[str, Any] = field(default_factory=dict)
    result_payload: dict[str, Any] = field(default_factory=dict)
    policy_version: str = ""
    current_stage: str = ""
    progress_percent: int | None = None

    def elapsed_seconds(self, now: datetime | None = None) -> int:
        """计算任务已持续的秒数。

        如果任务尚未开始，则以创建时间作为起点；如果外部传入当前时间，
        则使用该时间进行计算，便于测试和回放。
        """
        baseline = self.started_at or self.created_at
        current = now or datetime.now(timezone.utc)
        return max(int((current - baseline).total_seconds()), 0)
