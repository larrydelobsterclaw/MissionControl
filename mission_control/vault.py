from __future__ import annotations

import re
import subprocess
from datetime import date
from pathlib import Path


SEED_FILES = {
    "ops/models.md": "# Model Routing\n\nSeeded by mc init.\n",
    "ops/routing.md": "# Routing Rules\n\n- coder tasks -> qwen2.5-coder:7b (fallback deepseek-coder:6.7b)\n- digest/summaries -> llama3.1:8b\n- specs/json -> qwen2.5:7b\n- utility -> mistral:7b\n",
    "ops/howto.md": "# Operations How-To\n\nUse `mc` commands to drive workflow.\n",
}


def slugify(name: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "-", name.strip().lower()).strip("-")
    return value or "project"


def safe_join(base: Path, rel: str) -> Path:
    target = (base / rel).resolve()
    if not str(target).startswith(str(base.resolve())):
        raise ValueError("path escapes vault")
    return target


def ensure_structure(vault_path: Path) -> None:
    (vault_path / "projects").mkdir(parents=True, exist_ok=True)
    (vault_path / "runs").mkdir(parents=True, exist_ok=True)
    (vault_path / "ops").mkdir(parents=True, exist_ok=True)
    for rel, content in SEED_FILES.items():
        path = safe_join(vault_path, rel)
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text(content, encoding="utf-8")


def ensure_project_files(vault_path: Path, slug: str, goal: str | None = None) -> None:
    proj = vault_path / "projects" / slug
    proj.mkdir(parents=True, exist_ok=True)
    brief = proj / "brief.md"
    if not brief.exists():
        brief.write_text(f"# {slug} brief\n\nGoal: {goal or 'TBD'}\n", encoding="utf-8")
    for name in ("decisions.md", "tasks.md"):
        p = proj / name
        if not p.exists():
            p.write_text(f"# {name.replace('.md', '').title()}\n\n", encoding="utf-8")


def read(vault_path: Path, rel_path: str) -> str:
    return safe_join(vault_path, rel_path).read_text(encoding="utf-8")


def write(vault_path: Path, rel_path: str, md: str) -> None:
    path = safe_join(vault_path, rel_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(md, encoding="utf-8")


def append(vault_path: Path, rel_path: str, md: str) -> None:
    path = safe_join(vault_path, rel_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(md)


def search(vault_path: Path, query: str) -> list[str]:
    try:
        result = subprocess.run(
            ["rg", "-n", "--no-heading", query, str(vault_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        return [line for line in result.stdout.splitlines() if line.strip()]
    except FileNotFoundError:
        matches: list[str] = []
        for path in vault_path.rglob("*.md"):
            for idx, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                if query.lower() in line.lower():
                    matches.append(f"{path}:{idx}:{line}")
        return matches


def run_note_path(vault_path: Path, task_id: int) -> Path:
    day = date.today().isoformat()
    path = vault_path / "runs" / day / f"{task_id}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def run_bridge_path(vault_path: Path, task_id: int, step_index: int, role: str) -> Path:
    day = date.today().isoformat()
    path = vault_path / "runs" / day / f"{task_id}.step-{step_index:02d}-{role}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path
