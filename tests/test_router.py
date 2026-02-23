from mission_control.models import Task
from mission_control.router import execution_chain_for, select_model


def test_router_coder_hint():
    task = Task(project_slug="x", title="Fix tests", description="repo code", priority=1, model_hint="coder")
    model, fallback = select_model(task)
    assert model == "qwen2.5-coder:7b"
    assert fallback == "deepseek-coder:6.7b"


def test_router_auto_summary():
    task = Task(project_slug="x", title="Create digest", description="summarize runs", priority=2, model_hint="auto")
    model, _ = select_model(task)
    assert model == "llama3.1:8b"


def test_execution_chain_is_sequential_for_coder():
    task = Task(project_slug="x", title="Implement feature", description="repo code changes", priority=2, model_hint="coder")
    chain = execution_chain_for(task)
    assert [s.role for s in chain.steps] == ["analyze", "do", "compress"]
    assert chain.steps[1].model == "qwen2.5-coder:7b"
