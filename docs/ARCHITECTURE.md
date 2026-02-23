# Mission Control v1 Architecture

## 1) Separation: Manager vs Doers
- **Manager (Kimi K2.5)** accepts user intent and returns compact validated JSON plans only.
- **Doers (local Ollama models)** perform execution, summarization, extraction, and formatting.
- This enforces predictable orchestration and token discipline.

## 2) Token-saving strategy
- Manager prompt is short and schema-bound.
- Retrieval pulls only minimal vault context (brief, decisions, recent run notes).
- System stores compressed run notes and decision logs instead of full transcripts.
- Heavy generation happens locally via Ollama models.

## 3) Vault memory pattern (Rowboat-style)
The Markdown vault is durable long-term memory:

```
vault/
  projects/<slug>/brief.md
  projects/<slug>/decisions.md
  projects/<slug>/tasks.md
  runs/YYYY-MM-DD/<task_id>.md
  runs/YYYY-MM-DD/<task_id>.step-01-analyze.md
  runs/YYYY-MM-DD/<task_id>.step-02-do.md
  runs/YYYY-MM-DD/<task_id>.step-03-compress.md
  ops/models.md
  ops/routing.md
  ops/howto.md
```

SQLite remains the system-of-record for execution state while vault captures human-readable context and decisions.

## 4) Rowboat chaining for constrained machines
For devices like Mac mini M4 16GB, Mission Control uses **sequential model chaining**:
1. Small model (`mistral:7b`) creates compact plan/checklist.
2. Routed doer model executes the main step.
3. Compression model (`llama3.1:8b`) writes concise handoff/output notes.

No concurrent model residency is required. Each step writes bridge markdown so the next model starts from vault state.

## 5) Rowboat mapping
- `memory.read/write/append/search` in `vault.py` provides the core primitives.
- Decisions and evolving project context live in markdown pages.
- Task/runs metadata stays normalized in SQLite for filtering and reporting.

## 6) Extension plan
### Codex jobs later
- Add `toolchain` adapter in `runner.py` for Codex coding jobs.
- Preserve the same task schema and run-record format.
- Route coding-heavy tasks to Codex selectively while keeping local models for summaries.

### Auth0 web UI later
- Add a thin web app over existing modules.
- Secure web routes with Auth0; backend continues to use SQLite + vault.
- CLI remains fully functional for local-first operations.
