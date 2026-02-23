from __future__ import annotations

from mission_control.models import Run
from mission_control.ollama import OllamaClient


def build_digest(runs: list[Run], ollama: OllamaClient) -> str:
    if not runs:
        return "Mission Control Daily Digest\n\nNo runs in the last 24 hours."
    lines = [f"- Task {run.task_id}: {run.output_summary}" for run in runs[:20]]
    prompt = (
        "Summarize these run notes into concise operational bullets (max 8) and short next actions.\n"
        + "\n".join(lines)
    )
    summary = ollama.generate("llama3.1:8b", prompt, max_tokens=500)
    return "Mission Control Daily Digest\n\n" + summary.strip()
