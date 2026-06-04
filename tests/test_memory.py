from __future__ import annotations

from iscct.domain import AgentCard, AgentCapability
from iscct.memory import InMemoryAgentRegistry, InMemoryEventBus, InMemoryTaskStore, TaskDispatchService
from iscct.tasking import AssigneeType, TaskStatus


def test_agent_registry_registers_and_lists_agents() -> None:
    registry = InMemoryAgentRegistry()
    agent = AgentCard(
        agent_id="agent_001",
        display_name="Demo Agent",
        capabilities=(AgentCapability(name="tasking"),),
        metadata={"team": "ops"},
    )

    registry.register(agent)

    assert registry.get("agent_001") == agent
    assert registry.list() == (agent,)


def test_task_dispatch_service_creates_and_dispatches_task() -> None:
    registry = InMemoryAgentRegistry()
    agent = registry.register(
        AgentCard(
            agent_id="agent_001",
            display_name="Demo Agent",
        )
    )
    store = InMemoryTaskStore()
    bus = InMemoryEventBus()
    service = TaskDispatchService(task_store=store, agent_registry=registry, event_bus=bus)

    task = service.create_task(
        parent_event_id="evt_001",
        task_type="investigate_delay",
        input_payload={"order_id": "o-1"},
        assignee_id=agent.agent_id,
        assignee_display_name=agent.display_name,
        assignee_type=AssigneeType.AGENT,
        trace_id="trace_001",
    )

    assert task.status == TaskStatus.CREATED
    assert task.assignee_id == "agent_001"
    assert store.get(task.task_id) == task

    dispatched = service.dispatch(task.task_id)

    assert dispatched.status == TaskStatus.DISPATCHED
    assert store.get(task.task_id).status == TaskStatus.DISPATCHED
    assert bus.published[-1].topic == "task.dispatched"
    assert bus.published[-1].payload["task_id"] == task.task_id
    assert bus.published[-1].payload["assignee_display_name"] == "Demo Agent"


def test_task_store_appends_progress_and_updates_task_snapshot() -> None:
    store = InMemoryTaskStore()
    task = store.create(
        TaskDispatchService(
            task_store=store,
            agent_registry=InMemoryAgentRegistry(),
        ).create_task(
            parent_event_id="evt_001",
            task_type="investigate_delay",
            input_payload={},
            assignee_id="agent_001",
            assignee_display_name="Demo Agent",
        )
    )

    progress_event = store.append_progress(
        __import__("iscct.tasking", fromlist=["TaskProgressEvent"]).TaskProgressEvent(
            task_id=task.task_id,
            trace_id=task.trace_id,
            source_type=AssigneeType.AGENT,
            source_id="agent_001",
            stage="checking_status",
            message="checked carrier status",
            progress_percent=42,
        )
    )

    assert progress_event.task_id == task.task_id
    assert store.task_progress(task.task_id)[0] == progress_event
    updated = store.get(task.task_id)
    assert updated.current_stage == "checking_status"
    assert updated.progress_percent == 42
