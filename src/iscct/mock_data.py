from __future__ import annotations

from datetime import datetime, timezone, timedelta

APP_TITLE = "控制塔演示"
APP_SUBTITLE = "面向人工的一线 CT 运营工作台"

NOW = datetime.now(timezone.utc)

MOCK_AGENTS = [
    {
        "agent_id": "agent_ops_001",
        "display_name": "运营 智能体",
        "status": "健康",
        "capability": "路由并监控异常事件",
    },
    {
        "agent_id": "agent_support_001",
        "display_name": "客服 Agent",
        "status": "健康",
        "capability": "负责人机沟通与通知",
    },
    {
        "agent_id": "ct_agent",
        "display_name": "CT Agent",
        "status": "就绪",
        "capability": "人工接管与审批处理",
    },
]

MOCK_TASKS = [
    {
        "task_id": "task_1001",
        "title": "排查延误激增",
        "status": "进行中",
        "assignee": "运营 Agent",
        "stage": "检查外部系统状态",
        "started_at": NOW - timedelta(minutes=18),
        "last_progress_at": NOW - timedelta(minutes=2),
        "progress_percent": 62,
    },
    {
        "task_id": "task_1002",
        "title": "确认恢复方案",
        "status": "等待人工",
        "assignee": "CT Agent",
        "stage": "等待审批",
        "started_at": NOW - timedelta(minutes=7),
        "last_progress_at": NOW - timedelta(minutes=1),
        "progress_percent": 40,
    },
    {
        "task_id": "task_1003",
        "title": "关闭已解决工单",
        "status": "已完成",
        "assignee": "客服 Agent",
        "stage": "已发送最终摘要",
        "started_at": NOW - timedelta(hours=1, minutes=12),
        "last_progress_at": NOW - timedelta(minutes=25),
        "progress_percent": 100,
    },
]

MOCK_EVENTS = [
    {
        "event_id": "evt_9001",
        "event_type": "异常.延误激增",
        "severity": "高优先级",
        "source": "人工上报",
        "occurred_at": NOW - timedelta(minutes=20),
        "summary": "前台上报出现大范围延误激增。",
    }
]

MOCK_PROGRESS = [
    {
        "task_id": "task_1001",
        "stage": "检查外部系统状态",
        "message": "已收集第一批信号，并对受影响项目完成分组。",
        "occurred_at": NOW - timedelta(minutes=16),
    },
    {
        "task_id": "task_1001",
        "stage": "复核影响范围",
        "message": "已交叉校验受影响群体，并定位到可能的根因。",
        "occurred_at": NOW - timedelta(minutes=8),
    },
    {
        "task_id": "task_1002",
        "stage": "等待审批",
        "message": "已准备恢复方案，正在等待人工确认。",
        "occurred_at": NOW - timedelta(minutes=1),
    },
]


def format_elapsed(started_at: datetime) -> int:
    return max(int((NOW - started_at).total_seconds()), 0)
