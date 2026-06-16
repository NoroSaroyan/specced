"""Tests for preset application and MCP composition."""

from __future__ import annotations

import json
from pathlib import Path

from specced import detect, scaffold


def _mcp(repo: Path) -> dict:
    return json.loads((repo / ".mcp.json").read_text(encoding="utf-8"))["mcpServers"]


def test_preset_python_fastapi(repo: Path) -> None:
    scaffold.init_repo(repo, preset="python-fastapi")
    makefile = (repo / "Makefile").read_text(encoding="utf-8")
    assert "ruff format ." in makefile
    assert "pytest -q" in makefile
    assert "TODO(specced): wire up your" not in makefile  # placeholders replaced

    assert (repo / ".claude/rules/backend/api.md").exists()
    assert (repo / ".claude/code-review/01-api.md").exists()

    servers = _mcp(repo)
    assert {"postgres", "github", "context7"}.issubset(set(servers))

    cfg = scaffold.read_config(repo)
    assert cfg["preset"] == "python-fastapi"
    assert cfg["tracks"] == ["backend"]


def test_preset_stub_headings(repo: Path) -> None:
    scaffold.init_repo(repo, preset="python-fastapi")
    rule = (repo / ".claude/rules/backend/data-and-migrations.md").read_text(encoding="utf-8")
    assert rule.splitlines()[0] == "# Data and migrations conventions"
    dim = (repo / ".claude/code-review/02-data-and-migrations.md").read_text(encoding="utf-8")
    assert dim.splitlines()[0] == "# 02. Data and migrations"


def test_preset_auto_none_on_empty(repo: Path) -> None:
    report = scaffold.init_repo(repo, preset="auto")
    assert report["preset"] is None


def test_preset_auto_picks_from_detection(repo: Path) -> None:
    (repo / "go.mod").write_text("module example.com/x\n", encoding="utf-8")
    report = scaffold.init_repo(repo, preset="auto")
    assert report["preset"] == "go"
    assert (repo / ".claude/rules/go/conventions.md").exists()


def test_compose_mcp_add_unknown_and_skip(repo: Path) -> None:
    scaffold.init_repo(repo)
    res = scaffold.compose_mcp(repo, ["postgres", "github", "bogus"])
    assert "postgres" in res["added"]
    assert "bogus" in res["unknown"]
    assert "postgres" in _mcp(repo)

    res2 = scaffold.compose_mcp(repo, ["postgres"])
    assert "postgres" in res2["skipped"]


def test_compose_mcp_records_config(repo: Path) -> None:
    scaffold.init_repo(repo)
    scaffold.compose_mcp(repo, ["qdrant"])
    assert "qdrant" in scaffold.read_config(repo)["mcp_servers"]


def test_presets_have_core_anchors() -> None:
    names = {p["name"] for p in scaffold.list_presets()}
    assert {"go", "python-fastapi", "node-next", "tauri"}.issubset(names)  # anchors
    assert len(names) >= 13


def test_every_detectable_preset_is_reachable() -> None:
    """Each preset with a `detect` block is selected when its own markers appear.

    Property-based so a new auto-detected preset is verified automatically — adding one
    is a JSON file with no code change and no test enumeration to update.
    """
    for p in scaffold.list_presets():
        data = scaffold.load_preset(p["name"])
        det = data.get("detect")
        if det is None:
            continue
        assert isinstance(det.get("any_frameworks", []), list)
        assert isinstance(det.get("priority", 0), int)
        language = det.get("language") or data.get("language")
        fake = {"languages": [language], "frameworks": list(det.get("any_frameworks") or [])}
        assert detect.suggest_preset(fake) == p["name"], f"{p['name']} not reachable"


def test_every_preset_has_required_fields() -> None:
    for p in scaffold.list_presets():
        data = scaffold.load_preset(p["name"])
        assert data is not None
        assert "make" in data and {"fmt", "lint", "test", "build"} <= set(data["make"])
        for server in data.get("mcp_servers", []):
            assert server in scaffold.mcp_catalog(), (
                f"{p['name']} references unknown mcp '{server}'"
            )


def test_mcp_catalog_valid() -> None:
    catalog = scaffold.mcp_catalog()
    assert "postgres" in catalog and "github" in catalog and "context7" in catalog


def test_two_level_verify_gate(repo: Path) -> None:
    scaffold.init_repo(repo, preset="python-fastapi")
    makefile = (repo / "Makefile").read_text(encoding="utf-8")
    assert "verify:" in makefile and "verify-full:" in makefile
    checks = json.loads((repo / ".specced/checks.json").read_text(encoding="utf-8"))
    assert checks["all"] == "make verify"
    assert checks["all_full"] == "make verify-full"


def test_tauri_preset_two_tracks(repo: Path) -> None:
    scaffold.init_repo(repo, preset="tauri")
    assert (repo / ".claude/rules/frontend/components.md").exists()
    assert (repo / ".claude/rules/src-tauri/tauri-ipc.md").exists()
    assert (repo / ".claude/code-review/04-sqlx-and-migrations.md").exists()
    cfg = scaffold.read_config(repo)
    assert cfg["tracks"] == ["frontend", "src-tauri"]
