# Mission Control v1

Mission Control v1 is a local-first orchestration system with a strict **manager vs doer** split:
- **Manager**: Kimi K2.5 (or local manager fallback) outputs compact task JSON only.
- **Doers**: local Ollama models execute work and summarize outputs.
- **Memory**: Rowboat-style Markdown vault on disk.
- **State**: SQLite stores projects/tasks/runs/artifacts.

## Requirements
- Python 3.11+
- Ollama running locally with:
  - `qwen2.5-coder:7b`
  - `deepseek-coder:6.7b`
  - `llama3.1:8b`
  - `qwen2.5:7b`
  - `mistral:7b`

## Install
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
cp .env.example .env
```

## Quick start
```bash
mc init
mc project create "Mission Control" --goal "Ship v1"
mc task create --project mission-control --title "Scaffold CLI" --desc "build the first command set" --priority 2 --model-hint coder
mc task next --project mission-control
mc run 1
mc digest
```

## CLI commands
- `mc init`
- `mc project create <name> [--goal ...]`
- `mc project list`
- `mc task create --project <slug> --title ... --desc ... --priority 1-5 --model-hint auto|coder|ops|writer|fast`
- `mc task next [--project <slug>]`
- `mc run <task_id>`
- `mc status [--project <slug>]`
- `mc digest [--send-telegram]`
- `mc chat "<message>" [--dispatch]`
- `mc schedule install`

## Mac mini / constrained local hardware mode (recommended)
`mc run` now executes **sequential model chains** (not simultaneous models) to fit limited memory systems.
- Step 1 (`mistral:7b`) creates a compact checklist.
- Step 2 executes with the routed model (for code: `qwen2.5-coder:7b`).
- Step 3 (`llama3.1:8b`) compresses the result into durable notes when applicable.

Each step writes a Rowboat bridge note to:
- `vault/runs/YYYY-MM-DD/<task_id>.step-01-analyze.md`
- `vault/runs/YYYY-MM-DD/<task_id>.step-02-do.md`
- `vault/runs/YYYY-MM-DD/<task_id>.step-03-compress.md`

This lets each model boot independently and hand off state via vault files.

## Kimi + Telegram config
Set in `.env`:
- `KIMI_BASE_URL`, `KIMI_API_KEY`, `KIMI_MODEL`
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`

If Kimi env vars are missing, `mc chat` uses local manager mode (`qwen2.5:7b`) with the same strict schema.

## Routing rules
- Code/repo/tests/files: `qwen2.5-coder:7b` (fallback `deepseek-coder:6.7b`)
- Summaries/digests/extraction/compression: `llama3.1:8b`
- Specs/checklists/strict JSON writing: `qwen2.5:7b`
- Fast utility rewrite/classify: `mistral:7b`

## Adding a new worker model
1. Add mapping and chain behavior in `mission_control/router.py`.
2. Document in `vault/ops/models.md` and `vault/ops/routing.md`.
3. Use `model_hint` in tasks or rely on auto-routing heuristics.

## Schedule digest at 7:30am
Use `mc schedule install` and set local timezone in your shell/cron environment (e.g., `America/New_York`).

## Path to web UI later
- Keep CLI as control plane.
- Expose `db.py`, `runner.py`, and `vault.py` through API endpoints.
- Add Auth0 to web tier without changing core orchestration modules.
- Plug in Codex jobs as additional toolchain handlers in `runner.py`.
