from __future__ import annotations

import sqlite3
from pathlib import Path

from mission_control.models import Project, Run, Task


MIGRATIONS = [
    """
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        slug TEXT NOT NULL UNIQUE,
        goal TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_slug TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        priority INTEGER NOT NULL,
        model_hint TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(project_slug) REFERENCES projects(slug)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER NOT NULL,
        status TEXT NOT NULL,
        model_used TEXT NOT NULL,
        notes_path TEXT NOT NULL,
        output_summary TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(task_id) REFERENCES tasks(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS artifacts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id INTEGER NOT NULL,
        kind TEXT NOT NULL,
        path TEXT NOT NULL,
        FOREIGN KEY(run_id) REFERENCES runs(id)
    )
    """,
]


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def migrate(conn: sqlite3.Connection) -> None:
    for ddl in MIGRATIONS:
        conn.execute(ddl)
    conn.commit()


def create_project(conn: sqlite3.Connection, project: Project) -> int:
    cur = conn.execute(
        "INSERT INTO projects(name, slug, goal) VALUES (?, ?, ?)",
        (project.name, project.slug, project.goal),
    )
    conn.commit()
    return int(cur.lastrowid)


def list_projects(conn: sqlite3.Connection) -> list[Project]:
    rows = conn.execute("SELECT * FROM projects ORDER BY created_at DESC").fetchall()
    return [Project(**dict(row)) for row in rows]


def create_task(conn: sqlite3.Connection, task: Task) -> int:
    cur = conn.execute(
        """
        INSERT INTO tasks(project_slug, title, description, priority, model_hint, status)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (task.project_slug, task.title, task.description, task.priority, task.model_hint, task.status),
    )
    conn.commit()
    return int(cur.lastrowid)


def list_tasks(conn: sqlite3.Connection, project_slug: str | None = None, limit: int | None = None) -> list[Task]:
    sql = "SELECT * FROM tasks"
    params: list[object] = []
    if project_slug:
        sql += " WHERE project_slug = ?"
        params.append(project_slug)
    sql += " ORDER BY status='pending' DESC, priority ASC, created_at ASC"
    if limit:
        sql += f" LIMIT {int(limit)}"
    rows = conn.execute(sql, params).fetchall()
    return [Task(**dict(row)) for row in rows]


def get_task(conn: sqlite3.Connection, task_id: int) -> Task | None:
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return Task(**dict(row)) if row else None


def update_task_status(conn: sqlite3.Connection, task_id: int, status: str) -> None:
    conn.execute("UPDATE tasks SET status = ? WHERE id = ?", (status, task_id))
    conn.commit()


def create_run(conn: sqlite3.Connection, run: Run) -> int:
    cur = conn.execute(
        "INSERT INTO runs(task_id, status, model_used, notes_path, output_summary) VALUES (?, ?, ?, ?, ?)",
        (run.task_id, run.status, run.model_used, run.notes_path, run.output_summary),
    )
    conn.commit()
    return int(cur.lastrowid)


def recent_runs(conn: sqlite3.Connection, hours: int = 24) -> list[Run]:
    rows = conn.execute(
        """
        SELECT * FROM runs
        WHERE created_at >= datetime('now', ?)
        ORDER BY created_at DESC
        """,
        (f"-{hours} hours",),
    ).fetchall()
    return [Run(**dict(row)) for row in rows]
