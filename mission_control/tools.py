from __future__ import annotations

import shlex
import subprocess
from pathlib import Path


ALLOWED_PREFIXES = {
    "git",
    "pytest",
    "ruff",
    "python",
    "echo",
    "cat",
    "ls",
}


def fs_read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def fs_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def fs_diff(path: Path, new_content: str) -> str:
    old = path.read_text(encoding="utf-8") if path.exists() else ""
    if old == new_content:
        return "No changes"
    return f"--- old\n+++ new\n- {old[:200]}\n+ {new_content[:200]}"


def cmd_run(command: str, cwd: Path | None = None) -> tuple[int, str, str]:
    parts = shlex.split(command)
    if not parts:
        raise ValueError("empty command")
    if parts[0] not in ALLOWED_PREFIXES:
        raise PermissionError(f"command not allowed: {parts[0]}")
    proc = subprocess.run(parts, capture_output=True, text=True, cwd=cwd, check=False)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def git_status(cwd: Path) -> str:
    _, out, err = cmd_run("git status --short", cwd)
    return out or err


def git_diff(cwd: Path) -> str:
    _, out, err = cmd_run("git diff", cwd)
    return out or err


def git_commit(cwd: Path, message: str) -> str:
    code, out, err = cmd_run(f"git commit -m {shlex.quote(message)}", cwd)
    if code != 0:
        raise RuntimeError(err or out)
    return out
