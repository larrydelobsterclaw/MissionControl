from pathlib import Path

from mission_control.vault import ensure_structure, run_bridge_path, safe_join, slugify


def test_slugify():
    assert slugify("Mission Control!") == "mission-control"
    assert slugify("   ") == "project"


def test_safe_join_blocks_escape(tmp_path: Path):
    ensure_structure(tmp_path)
    ok = safe_join(tmp_path, "ops/models.md")
    assert ok.exists()
    try:
        safe_join(tmp_path, "../etc/passwd")
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")


def test_run_bridge_path(tmp_path: Path):
    ensure_structure(tmp_path)
    path = run_bridge_path(tmp_path, task_id=42, step_index=2, role="do")
    assert "42.step-02-do.md" in str(path)
    assert path.parent.exists()
