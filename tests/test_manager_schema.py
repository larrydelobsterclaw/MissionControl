import pytest

from mission_control.models import ManagerPlan


def test_manager_plan_validates():
    payload = {
        "intent": "create_tasks",
        "project": {"name": "Test", "slug": "test"},
        "tasks": [
            {
                "title": "Do x",
                "description": "desc",
                "priority": 2,
                "model_hint": "coder",
                "memory_reads": ["vault/projects/test/brief.md"],
                "memory_writes": [],
                "tools": ["vault.read"],
                "dispatch_now": False,
            }
        ],
        "summary_for_user": ["a", "b", "c"],
    }
    plan = ManagerPlan.model_validate(payload)
    assert plan.intent == "create_tasks"


def test_summary_bounds():
    with pytest.raises(Exception):
        ManagerPlan.model_validate(
            {
                "intent": "status",
                "project": None,
                "tasks": [],
                "summary_for_user": ["one", "two"],
            }
        )
