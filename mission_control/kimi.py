from __future__ import annotations

import json

import requests

from mission_control.models import ManagerPlan
from mission_control.ollama import OllamaClient
from mission_control.vault import slugify


MANAGER_SYSTEM = (
    "You are a manager-only planner. Return compact JSON only. "
    "No code blocks, no prose, no markdown."
)


class KimiManager:
    def __init__(self, base_url: str, api_key: str, model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    def plan(self, message: str, context_refs: list[str]) -> ManagerPlan:
        user_prompt = (
            "Create a strict compact JSON plan with keys: intent, project, tasks, summary_for_user. "
            "summary_for_user must have 3-6 short bullets."
            f"\nContext refs: {context_refs}\nUser message: {message}"
        )
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": MANAGER_SYSTEM},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.1,
            "max_tokens": 500,
            "response_format": {"type": "json_object"},
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        resp = requests.post(f"{self.base_url}/chat/completions", json=payload, headers=headers, timeout=45)
        resp.raise_for_status()
        text = resp.json()["choices"][0]["message"]["content"].strip()
        return ManagerPlan.model_validate_json(text)


class LocalManager:
    def __init__(self, ollama: OllamaClient) -> None:
        self.ollama = ollama

    def plan(self, message: str, context_refs: list[str]) -> ManagerPlan:
        prompt = (
            "Return only minified JSON matching schema with intent, project|null, tasks[], summary_for_user[3-6]. "
            "No markdown. "
            f"Message: {message}. Context refs: {context_refs}"
        )
        text = self.ollama.generate("qwen2.5:7b", prompt, system=MANAGER_SYSTEM, json_mode=True, max_tokens=500)
        try:
            return ManagerPlan.model_validate_json(text)
        except Exception:
            fallback = {
                "intent": "create_tasks",
                "project": None,
                "tasks": [
                    {
                        "title": message[:80],
                        "description": message,
                        "priority": 3,
                        "model_hint": "auto",
                        "memory_reads": [],
                        "memory_writes": [],
                        "tools": ["vault.read"],
                        "dispatch_now": False,
                    }
                ],
                "summary_for_user": [
                    "Parsed request into actionable task.",
                    "Assigned auto model hint for router selection.",
                    "Ready for dispatch via mc run <task_id>.",
                ],
            }
            if "project" in message.lower():
                fallback["project"] = {"name": "Auto Project", "slug": slugify("Auto Project")}
            return ManagerPlan.model_validate(fallback)


def parse_plan_json(raw_text: str) -> ManagerPlan:
    return ManagerPlan.model_validate(json.loads(raw_text))
