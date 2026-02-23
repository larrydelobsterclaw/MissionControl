from __future__ import annotations

from typing import Optional

import typer
from rich import print

from mission_control import db
from mission_control.config import get_settings
from mission_control.digest import build_digest
from mission_control.kimi import KimiManager, LocalManager
from mission_control.models import ManagerPlan, Project, Task
from mission_control.ollama import OllamaClient
from mission_control.runner import execute_task
from mission_control.telegram import send_message
from mission_control.vault import append, ensure_project_files, ensure_structure, slugify


app = typer.Typer(help="Mission Control v1 CLI")
project_app = typer.Typer()
task_app = typer.Typer()
schedule_app = typer.Typer()
app.add_typer(project_app, name="project")
app.add_typer(task_app, name="task")
app.add_typer(schedule_app, name="schedule")


def _conn():
    s = get_settings()
    conn = db.connect(s.db_path)
    db.migrate(conn)
    return conn


def _ollama() -> OllamaClient:
    return OllamaClient(get_settings().ollama_base_url)


@app.command()
def init() -> None:
    s = get_settings()
    conn = db.connect(s.db_path)
    db.migrate(conn)
    ensure_structure(s.vault_path)
    print(f"[green]Initialized[/green] DB at {s.db_path} and vault at {s.vault_path}")


@project_app.command("create")
def project_create(name: str, goal: str = "") -> None:
    s = get_settings()
    conn = _conn()
    slug = slugify(name)
    pid = db.create_project(conn, Project(name=name, slug=slug, goal=goal or None))
    ensure_project_files(s.vault_path, slug, goal or None)
    print(f"Created project {name} ({slug}) id={pid}")


@project_app.command("list")
def project_list() -> None:
    conn = _conn()
    for p in db.list_projects(conn):
        print(f"- {p.slug}: {p.name} (goal={p.goal or 'n/a'})")


@task_app.command("create")
def task_create(
    project: str = typer.Option(...),
    title: str = typer.Option(...),
    desc: str = typer.Option(...),
    priority: int = typer.Option(3, min=1, max=5),
    model_hint: str = typer.Option("auto"),
) -> None:
    conn = _conn()
    task = Task(project_slug=project, title=title, description=desc, priority=priority, model_hint=model_hint)  # type: ignore[arg-type]
    tid = db.create_task(conn, task)
    append(get_settings().vault_path, f"projects/{project}/tasks.md", f"- [ ] #{tid} P{priority} {title}: {desc}\n")
    print(f"Created task id={tid}")


@task_app.command("next")
def task_next(project: Optional[str] = None) -> None:
    conn = _conn()
    tasks = [t for t in db.list_tasks(conn, project_slug=project, limit=3) if t.status == "pending"]
    for t in tasks:
        print(f"#{t.id} [{t.priority}] {t.title} ({t.model_hint})")


@app.command()
def run(task_id: int) -> None:
    conn = _conn()
    run_obj = execute_task(conn, get_settings().vault_path, _ollama(), task_id)
    print(f"Run complete id={run_obj.id} model={run_obj.model_used} note={run_obj.notes_path}")


@app.command()
def status(project: Optional[str] = None) -> None:
    conn = _conn()
    tasks = db.list_tasks(conn, project_slug=project)
    by_status: dict[str, int] = {}
    for t in tasks:
        by_status[t.status] = by_status.get(t.status, 0) + 1
    print(f"Tasks total={len(tasks)} breakdown={by_status}")
    for t in tasks[:10]:
        print(f"- #{t.id} {t.status} P{t.priority} {t.title}")


@app.command()
def digest(send_telegram: bool = typer.Option(False, "--send-telegram")) -> None:
    s = get_settings()
    conn = _conn()
    runs = db.recent_runs(conn, hours=24)
    report = build_digest(runs, _ollama())
    print(report)
    if send_telegram and s.telegram_bot_token and s.telegram_chat_id:
        send_message(s.telegram_bot_token, s.telegram_chat_id, report)
        print("Telegram sent")


@app.command()
def chat(message: str, dispatch: bool = typer.Option(False, "--dispatch")) -> None:
    s = get_settings()
    conn = _conn()
    manager = (
        KimiManager(s.kimi_base_url, s.kimi_api_key, s.kimi_model)
        if s.kimi_base_url and s.kimi_api_key
        else LocalManager(_ollama())
    )
    plan: ManagerPlan = manager.plan(message, context_refs=["vault/ops/routing.md", "vault/ops/models.md"])
    if plan.project:
        try:
            db.create_project(conn, Project(name=plan.project.name, slug=plan.project.slug))
            ensure_project_files(s.vault_path, plan.project.slug)
        except Exception:
            pass
    for mt in plan.tasks:
        project_slug = plan.project.slug if plan.project else "inbox"
        ensure_project_files(s.vault_path, project_slug)
        tid = db.create_task(
            conn,
            Task(
                project_slug=project_slug,
                title=mt.title,
                description=mt.description,
                priority=mt.priority,
                model_hint=mt.model_hint,
            ),
        )
        append(s.vault_path, f"projects/{project_slug}/tasks.md", f"- [ ] #{tid} P{mt.priority} {mt.title}\n")
        for mw in mt.memory_writes:
            rel = mw.path.replace("vault/", "", 1)
            if mw.mode == "append":
                append(s.vault_path, rel, mw.content + "\n")
            else:
                from mission_control.vault import write

                write(s.vault_path, rel, mw.content)
        if dispatch or mt.dispatch_now:
            execute_task(conn, s.vault_path, _ollama(), tid)
    print("Manager summary:")
    for bullet in plan.summary_for_user:
        print(f"- {bullet}")


@schedule_app.command("install")
def schedule_install() -> None:
    print("Add this to crontab (adjust timezone/environment as needed):")
    print("30 7 * * * cd /path/to/MissionControl && mc digest --send-telegram >> mc_digest.log 2>&1")


if __name__ == "__main__":
    app()
