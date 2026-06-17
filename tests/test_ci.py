"""Tests for the external CI gate (`specced ci`) and its no-op placeholder guard."""

from __future__ import annotations

from pathlib import Path

from specced import scaffold

# Each preset language maps to a recognizable toolchain-setup action in the workflow.
_SETUP_MARKER = {
    "go": "setup-go",
    "node": "setup-node",
    "python": "setup-uv",
    "rust": "rust-toolchain",
    "java": "setup-java",
    "ruby": "setup-ruby",
}


def test_ci_emits_gate_for_every_preset(tmp_path: Path) -> None:
    """Property-based: every preset yields a valid gate carrying its language's setup.

    Adding a preset is a JSON file; this keeps the CI path reachable with no enumeration
    to update, as long as the preset's language is in the setup table.
    """
    for p in scaffold.list_presets():
        name = p["name"]
        root = tmp_path / name
        root.mkdir()
        scaffold.init_repo(root, preset=name)
        res = scaffold.emit_ci(root)
        assert res["ok"], f"{name}: {res.get('error')}"
        wf = root / ".github/workflows/specced-gate.yml"
        assert wf.exists()
        text = wf.read_text(encoding="utf-8")
        assert "make verify" in text
        assert "make verify-full" in text
        lang = scaffold.load_preset(name)["language"]
        assert _SETUP_MARKER[lang] in text, f"{name}: missing {_SETUP_MARKER[lang]} setup"


def test_ci_refuses_on_placeholder_targets(repo: Path) -> None:
    scaffold.init_repo(repo)  # no preset -> Makefile keeps TODO(specced) placeholders
    res = scaffold.emit_ci(repo)
    assert res["ok"] is False
    assert "placeholder" in res["error"]
    assert not (repo / ".github/workflows/specced-gate.yml").exists()


def test_ci_force_emits_over_placeholders_with_warning(repo: Path) -> None:
    scaffold.init_repo(repo)
    res = scaffold.emit_ci(repo, force=True)
    assert res["ok"] is True
    assert (repo / ".github/workflows/specced-gate.yml").exists()
    assert any("no-op" in w for w in res["warnings"])


def test_ci_pre_commit_and_config(repo: Path) -> None:
    scaffold.init_repo(repo, preset="go")
    res = scaffold.emit_ci(repo, pre_commit=True)
    assert res["ok"] is True
    assert (repo / ".pre-commit-config.yaml").exists()
    ci = scaffold.read_config(repo)["ci"]
    assert ci["github_gate"] is True
    assert ci["pre_commit"] is True


def test_ci_non_clobber_then_force(repo: Path) -> None:
    scaffold.init_repo(repo, preset="go")
    scaffold.emit_ci(repo)
    wf = repo / ".github/workflows/specced-gate.yml"
    wf.write_text(wf.read_text(encoding="utf-8") + "\n# EDITED\n", encoding="utf-8")
    scaffold.emit_ci(repo)  # no force -> skipped, edit preserved
    assert "# EDITED" in wf.read_text(encoding="utf-8")
    scaffold.emit_ci(repo, force=True)  # force -> regenerated
    assert "# EDITED" not in wf.read_text(encoding="utf-8")
