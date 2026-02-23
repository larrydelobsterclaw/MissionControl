from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


ModelHint = Literal["auto", "coder", "ops", "writer", "fast"]
TaskStatus = Literal["pending", "running", "done", "failed"]
Intent = Literal["create_tasks", "dispatch", "status"]


class Project(BaseModel):
    id: int | None = None
    name: str
    slug: str
    goal: str | None = None
    created_at: datetime | None = None


class Task(BaseModel):
    id: int | None = None
    project_slug: str
    title: str
    description: str
    priority: int = Field(ge=1, le=5)
    model_hint: ModelHint = "auto"
    status: TaskStatus = "pending"
    created_at: datetime | None = None


class Run(BaseModel):
    id: int | None = None
    task_id: int
    status: TaskStatus
    model_used: str
    notes_path: str
    output_summary: str
    created_at: datetime | None = None


class Artifact(BaseModel):
    id: int | None = None
    run_id: int
    kind: str
    path: str


class MemoryWrite(BaseModel):
    path: str
    mode: Literal["append", "write"]
    content: str

    @field_validator("path")
    @classmethod
    def must_be_vault_path(cls, value: str) -> str:
        if not value.startswith("vault/"):
            raise ValueError("memory write path must start with vault/")
        return value


class ManagerTask(BaseModel):
    title: str
    description: str
    priority: int = Field(ge=1, le=5)
    model_hint: ModelHint
    memory_reads: list[str] = Field(default_factory=list)
    memory_writes: list[MemoryWrite] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    dispatch_now: bool = False


class ManagerProject(BaseModel):
    name: str
    slug: str


class ManagerPlan(BaseModel):
    intent: Intent
    project: ManagerProject | None = None
    tasks: list[ManagerTask] = Field(default_factory=list)
    summary_for_user: list[str] = Field(min_length=3, max_length=6)

    @field_validator("summary_for_user")
    @classmethod
    def concise_bullets(cls, value: list[str]) -> list[str]:
        for bullet in value:
            if "```" in bullet or len(bullet) > 220:
                raise ValueError("summary bullet violates compact constraints")
        return value


class ExecutionStep(BaseModel):
    role: Literal["analyze", "do", "compress"]
    model: str
    purpose: str
    max_tokens: int = Field(default=500, ge=80, le=1800)


class ExecutionChain(BaseModel):
    steps: list[ExecutionStep] = Field(min_length=1, max_length=4)
    toolchain: list[str] = Field(default_factory=list)
