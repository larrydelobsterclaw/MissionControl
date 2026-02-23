from __future__ import annotations

from pathlib import Path

from mission_control import db
from mission_control.models import Run, Task
from mission_control.ollama import OllamaClient
from mission_control.router import execution_chain_for
from mission_control.vault import read as vault_read
from mission_control.vault import run_bridge_path, run_note_path


def _load_context(vault_path: Path, task: Task) -> tuple[list[str], str]:
    refs = [
        f"projects/{task.project_slug}/brief.md",
        f"projects/{task.project_slug}/decisions.md",
        f"projects/{task.project_slug}/tasks.md",
    ]
    context = ""
    for ref in refs:
        try:
            context += f"\n## {ref}\n" + vault_read(vault_path, ref)[:1600]
        except Exception:
            continue
    return refs, context


def execute_task(conn, vault_path: Path, ollama: OllamaClient, task_id: int) -> Run:
    task = db.get_task(conn, task_id)
    if not task:
        raise ValueError(f"Task {task_id} not found")
    assert isinstance(task, Task)
    db.update_task_status(conn, task_id, "running")

    refs, context = _load_context(vault_path, task)
    chain = execution_chain_for(task)
    bridge_outputs: list[str] = []
    model_trace: list[str] = []

    for idx, step in enumerate(chain.steps, start=1):
        prior = "\n\n".join(bridge_outputs[-2:])
        prompt = (
            f"Task title: {task.title}\n"
            f"Task description: {task.description}\n"
            f"Step role: {step.role}\n"
            f"Step purpose: {step.purpose}\n"
            "Keep output compact and actionable.\n"
            f"Context snippet:\n{context[:3200]}\n"
            f"Prior bridge notes:\n{prior[:2000]}"
        )
        output = ollama.generate(step.model, prompt, max_tokens=step.max_tokens)
        bridge_outputs.append(output)
        model_trace.append(step.model)

        bridge_path = run_bridge_path(vault_path, task_id, idx, step.role)
        bridge_path.write_text(
            (
                f"# Task {task_id} Bridge Step {idx}\n\n"
                f"- Role: {step.role}\n"
                f"- Model: {step.model}\n"
                f"- Purpose: {step.purpose}\n\n"
                f"## Output\n{output.strip()}\n"
            ),
            encoding="utf-8",
        )

    final_output = bridge_outputs[-1] if bridge_outputs else "No output generated."
    note_file = run_note_path(vault_path, task_id)
    note_file.write_text(
        (
            f"# Run Task {task_id}\n\n"
            f"## Goal\n{task.title}: {task.description}\n\n"
            "## Inputs (refs)\n"
            + "\n".join(f"- {ref}" for ref in refs)
            + "\n\n"
            + "## Actions taken\n"
            + "\n".join(f"- Step {i + 1} [{chain.steps[i].role}] via {model_trace[i]}" for i in range(len(model_trace)))
            + "\n\n"
            + "## Outputs/artifacts paths\n"
            + f"- {note_file}\n"
            + "\n".join(
                f"- {run_bridge_path(vault_path, task_id, i + 1, chain.steps[i].role)}" for i in range(len(chain.steps))
            )
            + "\n\n"
            + f"## Next steps\n{final_output[:1200]}\n"
        ),
        encoding="utf-8",
    )

    db.update_task_status(conn, task_id, "done")
    run = Run(
        task_id=task_id,
        status="done",
        model_used=" -> ".join(model_trace),
        notes_path=str(note_file),
        output_summary=final_output[:280],
    )
    run.id = db.create_run(conn, run)
    return run
