"""Tests for `specced adopt` — absorbing an existing hand-built setup (inverse of init)."""

from __future__ import annotations

import json
from pathlib import Path

from specced import scaffold


def _existing_setup(repo: Path) -> None:
    """A repo with a hand-built setup: a real Makefile, CLAUDE.md prose, and a rule —
    but no CONSTITUTION and no `verify` aggregator."""
    (repo / "Makefile").write_text(
        "test:\n\tpytest -q\nlint:\n\truff check .\n\tmypy .\n", encoding="utf-8"
    )
    (repo / "CLAUDE.md").write_text("# My Project\n\nWe value X. Always do Y.\n", encoding="utf-8")
    rule = repo / ".claude" / "rules" / "backend" / "api.md"
    rule.parent.mkdir(parents=True, exist_ok=True)
    rule.write_text("# API conventions\n\nUse versioned routes.\n", encoding="utf-8")


def test_adopt_plan_is_dry_run(repo: Path) -> None:
    _existing_setup(repo)
    res = scaffold.adopt(repo)  # default = plan
    assert res["mode"] == "plan"
    # nothing written
    assert not (repo / ".specced/config.json").exists()
    assert not (repo / ".claude/skills/repo-task-proof-loop").exists()
    assert scaffold.MANAGED_START not in (repo / "CLAUDE.md").read_text(encoding="utf-8")

    steps = {p["step"] for p in res["plan"]}
    assert {"engine", "checks", "rules", "constitution"}.issubset(steps)
    assert any(p["step"] == "checks" and p["action"] == "synthesize" for p in res["plan"])
    # missing layers become interview work
    assert any("CONSTITUTION" in f for f in res["interview_followups"])
    assert any("Align" in f for f in res["interview_followups"])  # existing rule -> align


def test_adopt_apply_is_nondestructive(repo: Path) -> None:
    _existing_setup(repo)
    before_rule = (repo / ".claude/rules/backend/api.md").read_text(encoding="utf-8")
    before_makefile = (repo / "Makefile").read_text(encoding="utf-8")

    res = scaffold.adopt(repo, apply=True)
    assert res["mode"] == "applied"

    # engine + agents installed
    assert (repo / ".claude/skills/repo-task-proof-loop/scripts/task_loop.py").exists()
    assert (repo / ".claude/agents/task-verifier.md").exists()

    # CLAUDE.md prose preserved, block added (managed-block upsert, not clobber)
    claude = (repo / "CLAUDE.md").read_text(encoding="utf-8")
    assert "We value X." in claude
    assert scaffold.MANAGED_START in claude
    assert scaffold.ORIENTATION_START in claude

    # user content untouched
    assert (repo / ".claude/rules/backend/api.md").read_text(encoding="utf-8") == before_rule
    assert (repo / "Makefile").read_text(encoding="utf-8") == before_makefile
    assert not (repo / "CONSTITUTION.md").exists()  # a followup, never auto-authored

    cfg = scaffold.read_config(repo)
    assert cfg["adopted"] is True
    assert cfg["preset"] is None  # adopt never imposes a preset's content


def test_adopt_synthesizes_checks_from_makefile(repo: Path) -> None:
    _existing_setup(repo)  # targets: test, lint (no fmt/build, no verify)
    scaffold.adopt(repo, apply=True)
    checks = json.loads((repo / ".specced/checks.json").read_text(encoding="utf-8"))
    assert checks["gates"] == {"lint": "make lint", "test": "make test"}
    assert checks["all"] == "make lint && make test"  # no verify -> chain present gates
    assert checks["all_full"] is None
    assert checks["raw_commands"]["test"] == "pytest -q"


def test_adopt_permissions_reflect_real_tools(repo: Path) -> None:
    _existing_setup(repo)
    scaffold.adopt(repo, apply=True)
    local = json.loads((repo / ".claude/settings.local.json").read_text(encoding="utf-8"))
    allow = local["permissions"]["allow"]
    assert "Bash(pytest:*)" in allow  # from the test recipe
    assert "Bash(ruff:*)" in allow  # from the lint recipe


def test_adopt_flags_missing_makefile(repo: Path) -> None:
    (repo / "CLAUDE.md").write_text("# Bare repo\n", encoding="utf-8")
    res = scaffold.adopt(repo)
    assert any(
        p["step"] == "checks" and p["action"] == "flag" for p in res["plan"]
    )  # no Makefile -> flagged for the interview
