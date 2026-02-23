from __future__ import annotations

import json
import time

import requests


class OllamaClient:
    def __init__(self, base_url: str, timeout: int = 60) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def generate(
        self,
        model: str,
        prompt: str,
        system: str | None = None,
        json_mode: bool = False,
        max_tokens: int = 600,
        retries: int = 2,
    ) -> str:
        prompt = prompt[:6000]
        payload = {
            "model": model,
            "prompt": prompt,
            "system": system or "",
            "stream": False,
            "options": {"num_predict": max_tokens},
        }
        if json_mode:
            payload["format"] = "json"
        last_error: Exception | None = None
        for attempt in range(retries + 1):
            try:
                resp = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=self.timeout)
                resp.raise_for_status()
                data = resp.json()
                text = data.get("response", "").strip()
                if json_mode:
                    json.loads(text)
                return text
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                time.sleep(0.7 * (attempt + 1))
        raise RuntimeError(f"Ollama generation failed: {last_error}")
