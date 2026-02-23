from __future__ import annotations

from mission_control.models import ExecutionChain, ExecutionStep, Task


ROUTING = {
    "coder": ("qwen2.5-coder:7b", "deepseek-coder:6.7b"),
    "ops": ("llama3.1:8b", None),
    "writer": ("qwen2.5:7b", None),
    "fast": ("mistral:7b", None),
}


def select_model(task: Task) -> tuple[str, str | None]:
    if task.model_hint in ROUTING:
        return ROUTING[task.model_hint]
    text = f"{task.title} {task.description}".lower()
    if any(tok in text for tok in ["code", "repo", "test", "file", "bug", "refactor"]):
        return ROUTING["coder"]
    if any(tok in text for tok in ["digest", "summary", "extract", "compress"]):
        return ROUTING["ops"]
    if any(tok in text for tok in ["json", "checklist", "spec"]):
        return ROUTING["writer"]
    return ROUTING["fast"]


def toolchain_for(task: Task) -> list[str]:
    primary, _ = select_model(task)
    if "coder" in primary:
        return ["vault.read", "vault.write", "fs.read", "fs.write", "cmd.run", "git.*"]
    if "llama" in primary:
        return ["vault.read", "vault.write"]
    return ["vault.read", "fs.read"]


def execution_chain_for(task: Task) -> ExecutionChain:
    primary, fallback = select_model(task)
    text = f"{task.title} {task.description}".lower()
    steps: list[ExecutionStep] = []

    if "coder" in primary:
        steps.append(
            ExecutionStep(
                role="analyze",
                model="mistral:7b",
                purpose="Create a terse execution checklist from task goal and memory refs.",
                max_tokens=220,
            )
        )
        steps.append(
            ExecutionStep(
                role="do",
                model=primary,
                purpose="Execute coding/repo actions with concise outputs only.",
                max_tokens=700,
            )
        )
        if fallback:
            steps.append(
                ExecutionStep(
                    role="compress",
                    model="llama3.1:8b",
                    purpose="Compress run result into short durable notes and next steps.",
                    max_tokens=340,
                )
            )
    elif any(tok in text for tok in ["digest", "summary", "extract", "compress"]):
        steps = [
            ExecutionStep(
                role="analyze",
                model="mistral:7b",
                purpose="Extract key points to summarize.",
                max_tokens=180,
            ),
            ExecutionStep(
                role="do",
                model="llama3.1:8b",
                purpose="Produce concise operational digest.",
                max_tokens=500,
            ),
        ]
    elif any(tok in text for tok in ["json", "checklist", "spec"]):
        steps = [
            ExecutionStep(
                role="analyze",
                model="mistral:7b",
                purpose="Normalize requirements to strict structured outline.",
                max_tokens=180,
            ),
            ExecutionStep(
                role="do",
                model="qwen2.5:7b",
                purpose="Produce strict JSON/checklist format.",
                max_tokens=420,
            ),
        ]
    else:
        steps = [
            ExecutionStep(
                role="do",
                model=primary,
                purpose="Complete quick utility transformation.",
                max_tokens=320,
            )
        ]

    return ExecutionChain(steps=steps, toolchain=toolchain_for(task))
