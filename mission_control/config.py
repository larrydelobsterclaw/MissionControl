from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


@dataclass(slots=True)
class Settings:
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    vault_path: Path = Path(os.getenv("MC_VAULT_PATH", "./vault"))
    db_path: Path = Path(os.getenv("MC_DB_PATH", "./mission_control.sqlite"))
    kimi_base_url: str | None = os.getenv("KIMI_BASE_URL") or None
    kimi_api_key: str | None = os.getenv("KIMI_API_KEY") or None
    kimi_model: str = os.getenv("KIMI_MODEL", "moonshot/kimi-k2.5")
    telegram_bot_token: str | None = os.getenv("TELEGRAM_BOT_TOKEN") or None
    telegram_chat_id: str | None = os.getenv("TELEGRAM_CHAT_ID") or None


def get_settings() -> Settings:
    return Settings()
