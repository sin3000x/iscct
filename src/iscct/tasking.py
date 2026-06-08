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

    CREATED = "created"  # 已创建，尚未分发。
    DISPATCHED = "dispatched"  # 已分发给执行方。
    IN_PROGRESS = "in_progress"  # 正在处理中。
    AWAITING_HUMAN = "awaiting_human"  # 正等待人工介入。
    COMPLETED = "completed"  # 已完成。
    FAILED = "failed"  # 执行失败。
    CANCELLING = "cancelling"  # 正在取消中。
    CANCELLED = "cancelled"  # 已取消。
    ROLLING_BACK = "rolling_back"  # 正在回滚中。
    ROLLED_BACK = "rolled_back"  # 已回滚。


class AssigneeType(str, Enum):
    """任务可分配给的执行主体类型。"""

    AGENT = "agent"  # 普通智能体。
    HUMAN = "human"  # 人类执行者。
    CT_AGENT = "ct_agent"  # CT 专用智能体。
    SYSTEM = "system"  # 系统内部执行主体。


@dataclass(frozen=True, slots=True)
class TaskProgressEvent:
    """描述一次任务进度上报。"""

    progress_id: str = field(default_factory=lambda: str(uuid4()))  # 进度事件 ID。
    task_id: str = ""  # 所属任务 ID。
    trace_id: str = ""  # 链路追踪 ID。
    source_type: AssigneeType = AssigneeType.SYSTEM  # 上报来源类型。
    source_id: str = ""  # 上报来源 ID。
    stage: str = ""  # 当前阶段名称。
    message: str = ""  # 进度说明文本。
    progress_percent: int | None = None  # 当前进度百分比。
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))  # 事件发生时间。
    metadata: dict[str, Any] = field(default_factory=dict)  # 扩展元数据。


@dataclass(frozen=True, slots=True)
class Task:
    """表示一个可调度、可追踪的任务对象。"""

    task_id: str = field(default_factory=lambda: str(uuid4()))  # 任务 ID。
    parent_event_id: str = ""  # 父事件 ID。
    task_type: str = ""  # 任务类型。
    status: TaskStatus = TaskStatus.CREATED  # 当前状态。
    priority: int = 0  # 优先级，数值越大优先级越高。
    trace_id: str = field(default_factory=lambda: str(uuid4()))  # 链路追踪 ID。
    assigned_to: str = ""  # 分配对象标识。
    assignee_type: AssigneeType = AssigneeType.SYSTEM  # 分配对象类型。
    assignee_id: str = ""  # 分配对象 ID。
    assignee_display_name: str = ""  # 分配对象显示名。
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))  # 创建时间。
    started_at: datetime | None = None  # 开始时间。
    completed_at: datetime | None = None  # 完成时间。
    deadline_at: datetime | None = None  # 截止时间。
    input_payload: dict[str, Any] = field(default_factory=dict)  # 输入参数。
    result_payload: dict[str, Any] = field(default_factory=dict)  # 结果数据。
    policy_version: str = ""  # 策略版本。
    current_stage: str = ""  # 当前执行阶段。
    progress_percent: int | None = None  # 当前进度百分比。

    def elapsed_seconds(self, now: datetime | None = None) -> int:
        """计算任务已持续的秒数。

        如果任务尚未开始，则以创建时间作为起点；如果外部传入当前时间，
        则使用该时间进行计算，便于测试和回放。
        """
        baseline = self.started_at or self.created_at
        current = now or datetime.now(timezone.utc)
        return max(int((current - baseline).total_seconds()), 0)
