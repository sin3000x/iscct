from __future__ import annotations

from datetime import datetime, timezone, timedelta

APP_TITLE = "Control Tower Demo"
APP_SUBTITLE = "A simple human-facing front desk for CT operations"

NOW = datetime.now(timezone.utc)

MOCK_AGENTS = [
    {
        "agent_id": "agent_ops_001",
        "display_name": "Ops Agent",
        "status": "Healthy",
        "capability": "Route and monitor incidents",
    },
    {
        "agent_id": "agent_support_001",
        "display_name": "Support Agent",
        "status": "Healthy",
        "capability": "Communicate with humans",
    },
    {
        "agent_id": "ct_agent",
        "display_name": "CT Agent",
        "status": "Ready",
        "capability": "Human handoff and approvals",
    },
]

MOCK_TASKS = [
    {
        "task_id": "task_1001",
        "title": "Investigate delay spike",
        "status": "IN_PROGRESS",
        "assignee": "Ops Agent",
        "stage": "Checking external system status",
        "started_at": NOW - timedelta(minutes=18),
        "last_progress_at": NOW - timedelta(minutes=2),
        "progress_percent": 62,
    },
    {
        "task_id": "task_1002",
        "title": "Confirm recovery plan",
        "status": "AWAITING_HUMAN",
        "assignee": "CT Agent",
        "stage": "Waiting for approval",
        "started_at": NOW - timedelta(minutes=7),
        "last_progress_at": NOW - timedelta(minutes=1),
        "progress_percent": 40,
    },
    {
        "task_id": "task_1003",
        "title": "Close resolved case",
        "status": "COMPLETED",
        "assignee": "Support Agent",
        "stage": "Sent final summary",
        "started_at": NOW - timedelta(hours=1, minutes=12),
        "last_progress_at": NOW - timedelta(minutes=25),
        "progress_percent": 100,
    },
]

MOCK_EVENTS = [
    {
        "event_id": "evt_9001",
        "event_type": "anomaly.delay_spike",
        "severity": "high",
        "source": "manual",
        "occurred_at": NOW - timedelta(minutes=20),
        "summary": "A large delay spike was reported by the front desk.",
    }
]

MOCK_PROGRESS = [
    {
        "task_id": "task_1001",
        "stage": "Checking external system status",
        "message": "Collected the first signal and grouped the affected items.",
        "occurred_at": NOW - timedelta(minutes=16),
    },
    {
        "task_id": "task_1001",
        "stage": "Reviewing impact scope",
        "message": "Cross-checked the impacted population and found a likely root cause.",
        "occurred_at": NOW - timedelta(minutes=8),
    },
    {
        "task_id": "task_1002",
        "stage": "Waiting for approval",
        "message": "Prepared recovery plan and awaiting human confirmation.",
        "occurred_at": NOW - timedelta(minutes=1),
    },
]


def format_elapsed(started_at: datetime) -> int:
    return max(int((NOW - started_at).total_seconds()), 0)
