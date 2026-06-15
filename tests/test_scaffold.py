"""Tests for the deterministic scaffolding (engine, agents, managed blocks, skills)."""

from __future__ import annotations

import json
import re
from pathlib import Path

from specced import scaffold

AGENTS = ("task-spec-freezer", "task-builder", "task-verifier", "task-fixer")


def test_init_creates_core(repo: Path) -> None:
    report = scaffold.init_repo(repo)
    assert (repo / ".claude/skills/repo-task-proof-loop/scripts/task_loop.py").exists()
    for a in AGENTS:
        assert (repo / f".claude/agents/{a}.md").exists()
        assert (repo / f".codex/agents/{a}.toml").exists()
    claude = (repo / "CLAUDE.md").read_text(encoding="utf-8")
    assert scaffold.MANAGED_START in claude
    assert (repo / "AGENTS.md").exists()
    assert (repo / "CONSTITUTION.md").exists()
    assert (repo / ".claude/settings.json").exists()
    assert (repo / "Makefile").exists()
    assert (repo / ".specced/config.json").exists()
    assert report["engine_version"] != "unknown"


def test_init_does_not_clobber_user_content(repo: Path) -> None:
    scaffold.init_repo(repo)
    constitution = repo / "CONSTITUTION.md"
    constitution.write_text(
        constitution.read_text(encoding="utf-8") + "\nEDITED\n", encoding="utf-8"
    )
    scaffold.init_repo(repo)  # no force
    assert "EDITED" in constitution.read_text(encoding="utf-8")


def test_managed_block_is_singular_after_repeat_init(repo: Path) -> None:
    scaffold.init_repo(repo)
    scaffold.init_repo(repo)
    assert (repo / "CLAUDE.md").read_text(encoding="utf-8").count(scaffold.MANAGED_START) == 1
    assert (repo / "AGENTS.md").read_text(encoding="utf-8").count(scaffold.MANAGED_START) == 1


def test_managed_block_preserves_surrounding_content(repo: Path) -> None:
    claude = repo / "CLAUDE.md"
    claude.write_text("# My project\n\nImportant context.\n", encoding="utf-8")
    scaffold.init_repo(repo)
    text = claude.read_text(encoding="utf-8")
    assert "Important context." in text
    assert scaffold.MANAGED_START in text


def test_doctor_green_after_init(repo: Path) -> None:
    scaffold.init_repo(repo)
    assert scaffold.doctor(repo)["ok"] is True


def test_doctor_fails_on_bare_repo(repo: Path) -> None:
    report = scaffold.doctor(repo)
    assert report["ok"] is False
    assert any(not c["ok"] for c in report["checks"])


def test_minimal_skips_layer2(repo: Path) -> None:
    scaffold.init_repo(repo, minimal=True)
    assert (repo / ".claude/agents/task-builder.md").exists()  # engine still installed
    assert not (repo / "CONSTITUTION.md").exists()  # Layer-2 skipped
    assert not (repo / "Makefile").exists()


def test_add_skill_and_unknown(repo: Path) -> None:
    scaffold.init_repo(repo)
    ok = scaffold.add_skill(repo, "code-review")
    assert ok["ok"] is True
    assert (repo / ".claude/skills/code-review/SKILL.md").exists()
    assert "code-review" in scaffold.read_config(repo)["skills"]

    again = scaffold.add_skill(repo, "code-review")  # already present
    assert again["ok"] is False

    bad = scaffold.add_skill(repo, "does-not-exist")
    assert bad["ok"] is False
    assert "available" in bad


def test_sync_restores_removed_agent(repo: Path) -> None:
    scaffold.init_repo(repo)
    (repo / ".claude/agents/task-builder.md").unlink()
    scaffold.sync(repo)
    assert (repo / ".claude/agents/task-builder.md").exists()


def test_library_lists_skills_excluding_engine() -> None:
    skills = scaffold.list_library_skills()
    assert "repo-task-proof-loop" not in skills  # engine is not a library skill
    assert {"code-review", "api-endpoint", "write-tests"}.issubset(set(skills))  # anchors
    assert len(skills) >= 16


def test_all_library_skills_wellformed() -> None:
    """Every skill (including the engine) has valid frontmatter and a matching name.

    Property-based so new skills are validated automatically, no enumeration to update.
    """
    root = scaffold.templates_dir() / "skills"
    for d in sorted(p for p in root.iterdir() if p.is_dir()):
        skill = d / "SKILL.md"
        assert skill.exists(), f"{d.name}: missing SKILL.md"
        text = skill.read_text(encoding="utf-8")
        m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
        assert m, f"{d.name}: missing YAML frontmatter"
        fm = m.group(1)
        name_match = re.search(r"^name:\s*(\S+)", fm, re.MULTILINE)
        assert name_match, f"{d.name}: missing 'name' in frontmatter"
        assert name_match.group(1) == d.name, f"{d.name}: name != directory"
        assert re.search(r"^description:\s*\S", fm, re.MULTILINE), f"{d.name}: missing description"


def test_engine_version_resolves() -> None:
    assert scaffold.engine_version() != "unknown"


def test_init_writes_agent_experience_files(repo: Path) -> None:
    scaffold.init_repo(repo, preset="python-fastapi")

    local = repo / ".claude/settings.local.json"
    assert local.exists()
    data = json.loads(local.read_text(encoding="utf-8"))
    allow = data["permissions"]["allow"]
    assert "Bash(make test:*)" in allow
    assert "Bash(ruff:*)" in allow  # from preset fmt command
    assert "Bash(pytest:*)" in allow  # from preset test command
    assert "postgres" in data["enabledMcpjsonServers"]

    checks = json.loads((repo / ".specced/checks.json").read_text(encoding="utf-8"))
    assert checks["all"] == "make verify"
    assert checks["gates"]["test"] == "make test"

    assert (repo / ".specced/repo-map.md").exists()
    assert scaffold.ORIENTATION_START in (repo / "CLAUDE.md").read_text(encoding="utf-8")
    assert scaffold.ORIENTATION_START in (repo / "AGENTS.md").read_text(encoding="utf-8")


def test_orientation_and_engine_blocks_coexist_singularly(repo: Path) -> None:
    scaffold.init_repo(repo, preset="python-fastapi")
    scaffold.init_repo(repo, preset="python-fastapi")  # idempotent re-run
    text = (repo / "CLAUDE.md").read_text(encoding="utf-8")
    assert text.count(scaffold.MANAGED_START) == 1
    assert text.count(scaffold.ORIENTATION_START) == 1


def test_doctor_reports_content_warnings(repo: Path) -> None:
    scaffold.init_repo(repo, preset="python-fastapi")
    report = scaffold.doctor(repo)
    assert report["ok"] is True  # structure is healthy
    assert isinstance(report["warnings"], list)
    assert any("CONSTITUTION.md" in w for w in report["warnings"])  # stubs unfilled


def test_minimal_skips_agent_experience(repo: Path) -> None:
    scaffold.init_repo(repo, minimal=True)
    assert not (repo / ".claude/settings.local.json").exists()
    assert not (repo / ".specced/checks.json").exists()
    claude = repo / "CLAUDE.md"
    assert claude.exists()  # engine managed block still present
    assert scaffold.ORIENTATION_START not in claude.read_text(encoding="utf-8")
