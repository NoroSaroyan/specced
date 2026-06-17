"""Deterministic scaffolding for the specced agentic coding setup.

This module is the mechanical half of specced. It never invents project-specific
content; it installs the vendored proof-loop engine, the project-scoped agents,
the managed guide blocks, and skeletons for the Layer-2 structure. Stack presets
prefill the verification vocabulary, MCP servers, and per-track rule stubs. The
interview (the Claude Code plugin) is what fills the remaining content.

Every public function returns a plain ``dict`` so the CLI can emit JSON that the
interview agent can read back and act on.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import detect as _detect
from ._paths import templates_dir

SPECCED_VERSION = "0.1.3"

# Managed-block markers — kept identical to the vendored engine so a repo that
# already used the engine directly keeps a single managed block, not two.
MANAGED_START = "<!-- repo-task-proof-loop:start -->"
MANAGED_END = "<!-- repo-task-proof-loop:end -->"
ORIENTATION_START = "<!-- specced:orientation:start -->"
ORIENTATION_END = "<!-- specced:orientation:end -->"

ENGINE_NAME = "repo-task-proof-loop"
ENGINE_REL = ("skills", ENGINE_NAME)

CLAUDE_AGENT_TEMPLATES = (
    "task-spec-freezer.md.tmpl",
    "task-builder.md.tmpl",
    "task-verifier.md.tmpl",
    "task-fixer.md.tmpl",
)
CODEX_AGENT_TEMPLATES = (
    "task-spec-freezer.toml.tmpl",
    "task-builder.toml.tmpl",
    "task-verifier.toml.tmpl",
    "task-fixer.toml.tmpl",
)

ENGINE_ATTRIBUTION = {"name": ENGINE_NAME, "source": "OpenAI", "license": "Apache-2.0"}

# One-line "what to use it for" per MCP server, surfaced in the orientation block.
MCP_PURPOSES = {
    "context7": "up-to-date library/framework docs",
    "github": "repos, issues, PRs, CI runs",
    "postgres": "query the DB / inspect schema (don't guess it)",
    "qdrant": "inspect vector collections",
    "supabase": "Supabase project (DB, auth, storage)",
    "playwright": "drive a browser for E2E checks",
    "sentry": "error & issue telemetry",
}


# --------------------------------------------------------------------------- #
# Resource resolution
# --------------------------------------------------------------------------- #
def engine_dir() -> Path:
    return templates_dir().joinpath(*ENGINE_REL)


def engine_assets() -> Path:
    return engine_dir() / "assets" / "templates"


def engine_version() -> str:
    try:
        text = (engine_dir() / "SKILL.md").read_text(encoding="utf-8")
    except OSError:
        return "unknown"
    m = re.search(r'^\s*version:\s*"?([0-9][^"\n]*?)"?\s*$', text, re.MULTILINE)
    return m.group(1).strip() if m else "unknown"


# --------------------------------------------------------------------------- #
# Small helpers
# --------------------------------------------------------------------------- #
def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def discover_repo_root(start: Path) -> Path:
    """Resolve the repo root from ``start`` via git, falling back to a .git walk."""
    start = start.resolve()
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=start,
            check=True,
            capture_output=True,
            text=True,
        )
        root = result.stdout.strip()
        if root:
            return Path(root).resolve()
    except Exception:
        pass

    current = start
    while True:
        if (current / ".git").exists():
            return current
        if current.parent == current:
            return start
        current = current.parent


def _render(text: str, ctx: dict[str, str]) -> str:
    for key, value in ctx.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def _write_file(path: Path, content: str, force: bool, actions: list[dict[str, str]]) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    existed = path.exists()
    if existed and not force:
        actions.append({"path": str(path), "action": "skipped (exists)"})
        return False
    path.write_text(content, encoding="utf-8")
    actions.append({"path": str(path), "action": "overwritten" if existed else "created"})
    return True


def _upsert_managed_block(
    path: Path, block: str, start: str = MANAGED_START, end: str = MANAGED_END
) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = path.read_text(encoding="utf-8") if path.exists() else ""
    if start in content and end in content:
        pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
        new_content = pattern.sub(block.strip(), content).rstrip() + "\n"
        action = "updated"
    elif content.strip():
        new_content = content.rstrip() + "\n\n" + block.strip() + "\n"
        action = "appended"
    else:
        new_content = block.strip() + "\n"
        action = "created"
    path.write_text(new_content, encoding="utf-8")
    return action


def _titleize(rel: str, kind: str) -> str:
    stem = re.sub(r"\.md$", "", rel.rsplit("/", 1)[-1])
    if kind == "code-review":
        m = re.match(r"(\d+)[-_.]?(.*)", stem)
        if m:
            rest = m.group(2).replace("-", " ").replace("_", " ").strip()
            return f"{m.group(1)}. {rest[:1].upper() + rest[1:]}" if rest else m.group(1)
    title = re.sub(r"^\d+[-_.]?", "", stem).replace("-", " ").replace("_", " ").strip()
    return title[:1].upper() + title[1:]


def _stub_from_template(tmpl: str, title: str, kind: str) -> str:
    lines = tmpl.splitlines()
    if lines and lines[0].startswith("#"):
        lines[0] = f"# {title}" if kind == "code-review" else f"# {title} conventions"
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- #
# Presets + MCP catalog
# --------------------------------------------------------------------------- #
def presets_dir() -> Path:
    return templates_dir() / "presets"


def list_presets() -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for path in sorted(presets_dir().glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        out.append(
            {"name": data.get("name", path.stem), "description": data.get("description", "")}
        )
    return out


def load_preset(name: str | None) -> dict[str, Any] | None:
    if not name:
        return None
    path = presets_dir() / f"{name}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def mcp_catalog() -> dict[str, Any]:
    return json.loads((templates_dir() / "mcp" / "servers.json").read_text(encoding="utf-8"))


def compose_mcp(repo_root: Path, names: list[str], *, force: bool = False) -> dict[str, Any]:
    catalog = mcp_catalog()
    path = repo_root / ".mcp.json"
    data: dict[str, Any] = {"mcpServers": {}}
    if path.exists():
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                data = loaded
                data.setdefault("mcpServers", {})
        except json.JSONDecodeError:
            pass

    added, skipped, unknown = [], [], []
    for name in names:
        if name not in catalog:
            unknown.append(name)
        elif name in data["mcpServers"] and not force:
            skipped.append(name)
        else:
            data["mcpServers"][name] = catalog[name]
            added.append(name)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    cfg = read_config(repo_root)
    cfg["mcp_servers"] = sorted(data["mcpServers"].keys())
    cfg["updated_at"] = _now()
    write_config(repo_root, cfg)

    return {
        "added": added,
        "skipped": skipped,
        "unknown": unknown,
        "servers": sorted(data["mcpServers"]),
        "catalog": sorted(catalog),
    }


def detect_repo(repo_root: Path) -> dict[str, Any]:
    return _detect.detect(repo_root)


# --------------------------------------------------------------------------- #
# Install steps
# --------------------------------------------------------------------------- #
def _install_engine(repo_root: Path, actions: list[dict[str, str]], force: bool) -> None:
    dst = repo_root / ".claude" / "skills" / ENGINE_NAME
    if dst.exists() and not force:
        actions.append({"path": str(dst), "action": "skipped (exists)"})
        return
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(engine_dir(), dst)
    actions.append({"path": str(dst), "action": f"installed engine v{engine_version()}"})


def _install_agents(repo_root: Path, actions: list[dict[str, str]]) -> None:
    # Agents are specced-managed, not user content: always refresh to this version.
    for name in CLAUDE_AGENT_TEMPLATES:
        src = engine_assets() / "claude" / name
        dst = repo_root / ".claude" / "agents" / name[: -len(".tmpl")]
        _write_file(dst, src.read_text(encoding="utf-8"), True, actions)
    for name in CODEX_AGENT_TEMPLATES:
        src = engine_assets() / "codex" / name
        dst = repo_root / ".codex" / "agents" / name[: -len(".tmpl")]
        _write_file(dst, src.read_text(encoding="utf-8"), True, actions)


def _install_managed_blocks(repo_root: Path, actions: list[dict[str, str]]) -> None:
    claude_block = (engine_assets() / "managed-block-claude.md.tmpl").read_text(encoding="utf-8")
    agents_block = (engine_assets() / "managed-block-agents.md.tmpl").read_text(encoding="utf-8")
    claude_path = repo_root / "CLAUDE.md"
    agents_path = repo_root / "AGENTS.md"
    actions.append(
        {
            "path": str(claude_path),
            "action": f"managed block {_upsert_managed_block(claude_path, claude_block)}",
        }
    )
    actions.append(
        {
            "path": str(agents_path),
            "action": f"managed block {_upsert_managed_block(agents_path, agents_block)}",
        }
    )


def _copy_skeleton(src: Path, dst: Path, actions: list[dict[str, str]], force: bool) -> None:
    if not src.is_dir():
        return
    for f in sorted(p for p in src.rglob("*") if p.is_file()):
        _write_file(dst / f.relative_to(src), f.read_text(encoding="utf-8"), force, actions)


def _install_layer2(
    repo_root: Path, actions: list[dict[str, str]], force: bool, ctx: dict[str, str]
) -> None:
    proj = templates_dir() / "project"
    _write_file(
        repo_root / "CONSTITUTION.md",
        _render((proj / "CONSTITUTION.md.tmpl").read_text(encoding="utf-8"), ctx),
        force,
        actions,
    )
    _write_file(
        repo_root / ".claude" / "settings.json",
        _render((proj / "settings.json.tmpl").read_text(encoding="utf-8"), ctx),
        force,
        actions,
    )
    _write_file(
        repo_root / ".mcp.json",
        (proj / "mcp.json.tmpl").read_text(encoding="utf-8"),
        force,
        actions,
    )
    _write_file(
        repo_root / "Makefile",
        _render((proj / "Makefile.tmpl").read_text(encoding="utf-8"), ctx),
        force,
        actions,
    )
    _copy_skeleton(templates_dir() / "rules", repo_root / ".claude" / "rules", actions, force)
    _copy_skeleton(
        templates_dir() / "code-review", repo_root / ".claude" / "code-review", actions, force
    )


def _apply_preset_content(
    repo_root: Path, preset: dict[str, Any], actions: list[dict[str, str]], force: bool
) -> None:
    rule_tmpl = (templates_dir() / "rules" / "_template.md").read_text(encoding="utf-8")
    dim_tmpl = (templates_dir() / "code-review" / "_template.md").read_text(encoding="utf-8")
    for rel in preset.get("rules", []):
        _write_file(
            repo_root / ".claude" / "rules" / rel,
            _stub_from_template(rule_tmpl, _titleize(rel, "rules"), "rules"),
            force,
            actions,
        )
    for rel in preset.get("code_review", []):
        _write_file(
            repo_root / ".claude" / "code-review" / rel,
            _stub_from_template(dim_tmpl, _titleize(rel, "code-review"), "code-review"),
            force,
            actions,
        )


# --------------------------------------------------------------------------- #
# Agent-experience layer: permissions, checks, repo map, orientation, warnings
# --------------------------------------------------------------------------- #
def _bash_allow(cmd: str) -> str | None:
    """Turn a shell command into a Claude Code permission prefix.

    'ruff format .' -> 'Bash(ruff:*)'; './mvnw test' -> 'Bash(./mvnw:*)'.
    """
    cmd = (cmd or "").strip()
    if not cmd or cmd.startswith(("@echo", "#")):
        return None
    return f"Bash({cmd.split()[0]}:*)"


def _permission_allowlist(preset_data: dict[str, Any] | None) -> list[str]:
    """Pre-authorize exactly the commands an agent needs to verify its own work,
    so it isn't blocked by approval prompts mid-task. specced knows these because
    they're the project's verification vocabulary."""
    allow = [
        "Bash(make fmt:*)",
        "Bash(make lint:*)",
        "Bash(make test:*)",
        "Bash(make build:*)",
        "Bash(make verify:*)",
        "Bash(git status:*)",
        "Bash(git diff:*)",
        "Bash(git log:*)",
        "Bash(git show:*)",
        "Bash(git branch:*)",
        "Bash(specced:*)",
        "Bash(python3 .claude/skills/repo-task-proof-loop/scripts/task_loop.py:*)",
    ]
    for cmd in (preset_data or {}).get("make", {}).values():
        entry = _bash_allow(cmd)
        if entry and entry not in allow:
            allow.append(entry)
    return allow


def _enabled_mcp(repo_root: Path) -> list[str]:
    path = repo_root / ".mcp.json"
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return sorted((data or {}).get("mcpServers", {}))
        except json.JSONDecodeError:
            pass
    return []


def _install_permissions(
    repo_root: Path, preset_data: dict[str, Any] | None, actions: list[dict[str, str]], force: bool
) -> None:
    path = repo_root / ".claude" / "settings.local.json"
    if path.exists() and not force:
        actions.append({"path": str(path), "action": "skipped (exists)"})
        return
    payload = {
        "permissions": {
            "allow": _permission_allowlist(preset_data),
            "ask": [],
            "additionalDirectories": [],
        },
        "enabledMcpjsonServers": _enabled_mcp(repo_root),
    }
    _write_file(path, json.dumps(payload, indent=2) + "\n", True, actions)


def _write_checks(
    repo_root: Path, preset_data: dict[str, Any] | None, actions: list[dict[str, str]], force: bool
) -> None:
    """Machine-readable acceptance-criteria vocabulary: gate -> command."""
    make = (preset_data or {}).get("make", {})
    payload = {
        "all": "make verify",
        "all_full": "make verify-full",
        "gates": {name: f"make {name}" for name in ("fmt", "lint", "test", "build")},
        "raw_commands": {k: make[k] for k in ("fmt", "lint", "test", "build") if make.get(k)},
        "note": "make verify = fast gate (fmt+lint+test); make verify-full adds build. Gates map to Makefile targets.",
    }
    _write_file(
        repo_root / ".specced" / "checks.json", json.dumps(payload, indent=2) + "\n", force, actions
    )


def _write_repo_map(
    repo_root: Path,
    detection: dict[str, Any] | None,
    preset_data: dict[str, Any] | None,
    actions: list[dict[str, str]],
    force: bool,
) -> None:
    d = detection or {}
    infra = d.get("infra", {})
    lines = [
        f"# {repo_root.name} — repo map",
        "",
        "> Orientation for agents and humans. Generated by specced from detection;",
        "> re-run `specced init --force` when the layout changes.",
        "",
        "## Stack",
        f"- languages: {', '.join(d.get('languages', [])) or 'unknown'}",
    ]
    if d.get("frameworks"):
        lines.append(f"- frameworks: {', '.join(d['frameworks'])}")
    if preset_data:
        lines.append(f"- preset: {preset_data.get('name')}")
    if d.get("tracks"):
        suffix = "  (monorepo)" if d.get("monorepo") else ""
        lines.append(f"- tracks: {', '.join(d['tracks'])}{suffix}")
    if infra.get("databases"):
        supa = "  +supabase" if infra.get("supabase") else ""
        lines.append(f"- data: {', '.join(infra['databases'])}{supa}")
    if infra.get("migrations"):
        lines.append(f"- migrations: {infra['migrations']}")
    lines += [
        "",
        "## Verify your work",
        "- `make verify` — full gate. Individually: `make fmt`, `make lint`, `make test`, `make build`.",
        "- Machine-readable: `.specced/checks.json`. Don't claim done without a green gate.",
        "",
        "## Where things live",
        "- Non-negotiables: `CONSTITUTION.md`",
        "- Conventions: `.claude/rules/<track>/*.md`",
        "- Review dimensions: `.claude/code-review/NN-*.md`",
        "- Task skills: `.claude/skills/`",
        "- Proof-loop artifacts: `.agent/tasks/<id>/`",
        "",
        "> TODO(specced): add entry points, key directories, and 'where do I add X' notes.",
    ]
    _write_file(repo_root / ".specced" / "repo-map.md", "\n".join(lines) + "\n", force, actions)


def _orientation_block(config: dict[str, Any]) -> str:
    tracks = config.get("tracks", []) or []
    track_hint = f" (tracks: {', '.join(tracks)})" if tracks else ""
    body = [
        ORIENTATION_START,
        "## specced orientation",
        "",
        "Before working in this repo, read:",
        "- **Non-negotiables:** `CONSTITUTION.md`",
        f"- **Conventions:** `.claude/rules/`{track_hint}",
        "- **Review lenses:** `.claude/code-review/`",
        "- **Repo map:** `.specced/repo-map.md`",
        "",
        "**Verify before claiming done:** `make verify` (gates in `.specced/checks.json`).",
    ]
    servers = config.get("mcp_servers", []) or []
    if servers:
        body += ["", "**MCP tools available:**"]
        body += [f"- `{s}` — {MCP_PURPOSES.get(s, 'see .mcp.json')}" for s in servers]
    body.append(ORIENTATION_END)
    return "\n".join(body)


def _install_orientation(
    repo_root: Path, config: dict[str, Any], actions: list[dict[str, str]]
) -> None:
    block = _orientation_block(config)
    for guide in ("CLAUDE.md", "AGENTS.md"):
        path = repo_root / guide
        action = _upsert_managed_block(path, block, ORIENTATION_START, ORIENTATION_END)
        actions.append({"path": str(path), "action": f"orientation block {action}"})


def _content_warnings(repo_root: Path) -> list[str]:
    """Non-fatal flags: guidance specced scaffolded but nobody filled in yet — so an
    agent knows which rules/constitution are not authoritative."""
    warnings: list[str] = []
    constitution = repo_root / "CONSTITUTION.md"
    if constitution.exists() and "TODO(specced)" in constitution.read_text(encoding="utf-8"):
        warnings.append("CONSTITUTION.md still has TODO(specced) markers — not yet authoritative")
    rules_dir = repo_root / ".claude" / "rules"
    if rules_dir.is_dir():
        stubs = [
            str(f.relative_to(repo_root))
            for f in sorted(rules_dir.rglob("*.md"))
            if f.name not in ("README.md", "_template.md")
            and "TODO(specced)" in f.read_text(encoding="utf-8")
        ]
        if stubs:
            shown = ", ".join(stubs[:5]) + (" …" if len(stubs) > 5 else "")
            warnings.append(f"{len(stubs)} rule stub(s) still unfilled: {shown}")
    try:
        ignored = subprocess.run(
            ["git", "-C", str(repo_root), "check-ignore", "-q", ".claude/agents"],
            capture_output=True,
        )
        if ignored.returncode == 0:
            warnings.append(
                ".claude/ is git-ignored — specced's agents/rules/engine won't be "
                "version-controlled or shared. Un-ignore .claude/{rules,agents,skills,commands} "
                "(keep .claude/settings.local.json ignored)."
            )
    except Exception:
        pass
    return warnings


# --------------------------------------------------------------------------- #
# CI gate + MCP suggestions (day-2: make the gate external, surface missed servers)
# --------------------------------------------------------------------------- #
CI_GATE_REL = (".github", "workflows", "specced-gate.yml")

# Primary-language -> GitHub Actions toolchain setup steps. Pins track this repo's
# own CI convention (checkout@v6, setup-uv@v8.2.0). specced installs one preset per
# repo; a multi-stack repo (e.g. tauri = node + rust) needs the second block by hand.
_CI_SETUP: dict[str, list[str]] = {
    "go": [
        "      - uses: actions/setup-go@v5",
        "        with:",
        "          go-version: stable",
    ],
    "node": [
        "      - uses: actions/setup-node@v4",
        "        with:",
        "          node-version: lts/*",
        "      - run: npm ci",
    ],
    "python": [
        "      - uses: astral-sh/setup-uv@v8.2.0",
        "      - run: uv sync --all-extras --dev",
    ],
    "rust": [
        "      - uses: dtolnay/rust-toolchain@stable",
    ],
    "cpp": [
        "      - name: Install C++ toolchain",
        "        run: sudo apt-get update && sudo apt-get install -y cmake ninja-build clang clang-format clang-tidy",
    ],
    "java": [
        "      - uses: actions/setup-java@v4",
        "        with:",
        "          distribution: temurin",
        "          java-version: '21'",
    ],
    "ruby": [
        "      - uses: ruby/setup-ruby@v1",
        "        with:",
        "          ruby-version: '3.3'",
        "          bundler-cache: true",
    ],
}


def _default_branch(repo_root: Path) -> str:
    """Best-effort default branch for the ``push`` trigger (falls back to ``main``)."""
    for cmd in (
        ["git", "-C", str(repo_root), "symbolic-ref", "--short", "refs/remotes/origin/HEAD"],
        ["git", "-C", str(repo_root), "branch", "--show-current"],
    ):
        try:
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode == 0 and r.stdout.strip():
                return r.stdout.strip().rsplit("/", 1)[-1]
        except Exception:
            pass
    return "main"


def _ci_targets_are_placeholders(repo_root: Path) -> bool:
    """True if the verify targets are still ``TODO(specced)`` stubs — a CI gate over
    them passes without checking anything (a green no-op). The Makefile carries the
    marker specced plants when no preset wired real commands."""
    makefile = repo_root / "Makefile"
    if not makefile.exists():
        return True
    return "TODO(specced)" in makefile.read_text(encoding="utf-8")


def _resolve_language(repo_root: Path, cfg: dict[str, Any]) -> str | None:
    preset_data = load_preset(cfg.get("preset"))
    if preset_data and preset_data.get("language"):
        return str(preset_data["language"])
    langs = _detect.detect(repo_root).get("languages", [])
    return langs[0] if langs else None


def _write_pre_commit(repo_root: Path, actions: list[dict[str, str]], force: bool) -> None:
    content = (
        "# Managed by `specced ci --pre-commit`. Fast checks only — `make fmt lint`\n"
        "# (tests run in the CI gate; too slow for a commit hook).\n"
        "repos:\n"
        "  - repo: local\n"
        "    hooks:\n"
        "      - id: specced-fast-gate\n"
        "        name: specced fast gate (fmt + lint)\n"
        "        entry: make fmt lint\n"
        "        language: system\n"
        "        pass_filenames: false\n"
        "        always_run: true\n"
    )
    _write_file(repo_root / ".pre-commit-config.yaml", content, force, actions)


def emit_ci(repo_root: Path, *, force: bool = False, pre_commit: bool = False) -> dict[str, Any]:
    """Emit a GitHub Actions workflow that runs the verify gate (the same one the proof
    loop uses), and optionally a fast pre-commit hook. The gate is specced-owned: it
    lives in its own file and never edits the repo's other workflows."""
    cfg = read_config(repo_root)
    language = _resolve_language(repo_root, cfg)
    actions: list[dict[str, str]] = []
    warnings: list[str] = []

    if _ci_targets_are_placeholders(repo_root) and not force:
        return {
            "ok": False,
            "repo_root": str(repo_root),
            "language": language,
            "error": (
                "verify targets are still TODO(specced) placeholders — a CI gate over them "
                "would pass without checking anything. Wire up the Makefile (the interview "
                "does this, or `specced init --preset <name>`), then re-run. --force emits anyway."
            ),
        }
    if _ci_targets_are_placeholders(repo_root):
        warnings.append(
            "emitted over placeholder verify targets — the gate is a green no-op until the "
            "Makefile is wired to real commands."
        )

    if language not in _CI_SETUP:
        warnings.append(
            f"no toolchain-setup template for language '{language}' — emitted a checkout-only "
            "gate; add your stack's setup step(s) to .github/workflows/specced-gate.yml."
        )
    setup_steps = _CI_SETUP.get(language or "", [])

    tmpl = (templates_dir() / "ci" / "github-gate.yml.tmpl").read_text(encoding="utf-8")
    content = _render(
        tmpl,
        {"SETUP_STEPS": "\n".join(setup_steps), "DEFAULT_BRANCH": _default_branch(repo_root)},
    )
    _write_file(repo_root / Path(*CI_GATE_REL), content, force, actions)

    if pre_commit:
        _write_pre_commit(repo_root, actions, force)

    cfg["ci"] = {"github_gate": True, "pre_commit": bool(pre_commit)}
    cfg["updated_at"] = _now()
    write_config(repo_root, cfg)

    return {
        "ok": True,
        "repo_root": str(repo_root),
        "language": language,
        "actions": actions,
        "warnings": warnings,
        "next": (
            "Commit .github/workflows/specced-gate.yml. It runs `make verify` on PRs and "
            "`make verify-full` on the default branch — the same gate the proof loop uses."
        ),
    }


def _mcp_suggestions(repo_root: Path) -> list[str]:
    """Advisory: stack signals (including dependency fingerprints) that map to an MCP
    server not yet enabled in .mcp.json. Surfaced by ``doctor``; never auto-installed."""
    try:
        det = _detect.detect(repo_root)
    except Exception:
        return []
    enabled = set(_enabled_mcp(repo_root))
    return [
        f"detected stack suggests MCP '{m}' (not enabled) — `specced add-mcp {m}`"
        for m in det.get("suggested_mcp", [])
        if m not in enabled
    ]


# --------------------------------------------------------------------------- #
# Adopt: absorb an existing hand-built setup (the inverse of init)
# --------------------------------------------------------------------------- #
_MAKE_TARGET_RE = re.compile(r"^([A-Za-z0-9_][A-Za-z0-9_./-]*)\s*:(?!=)")


def _parse_makefile_targets(repo_root: Path) -> dict[str, str]:
    """Map target -> recipe (commands joined by ' && ') for an existing Makefile, so
    `adopt` can derive the verification vocabulary from what the repo already has rather
    than from a preset. Best-effort: skips ``.PHONY``/pattern rules and ``:=`` assignments."""
    path = repo_root / "Makefile"
    if not path.exists():
        return {}
    targets: dict[str, str] = {}
    current: str | None = None
    recipe: list[str] = []

    def _flush() -> None:
        nonlocal current, recipe
        if current is not None:
            targets[current] = " && ".join(recipe)
        current, recipe = None, []

    for line in path.read_text(encoding="utf-8").splitlines():
        if current is not None and line.startswith("\t"):
            cmd = re.sub(r"^[@\-]+", "", line[1:].strip())
            if cmd and not cmd.startswith("#"):
                recipe.append(cmd)
            continue
        m = _MAKE_TARGET_RE.match(line)
        if m and "%" not in m.group(1) and not m.group(1).startswith("."):
            _flush()
            current = m.group(1)
        else:
            _flush()
    _flush()
    return targets


def _inventory_existing(repo_root: Path) -> dict[str, Any]:
    """Survey the specced-relevant content a repo already has, so `adopt` can plan."""

    def _list_md(rel: tuple[str, ...]) -> list[str]:
        base = repo_root / Path(*rel)
        if not base.is_dir():
            return []
        return sorted(
            str(p.relative_to(base)).replace("\\", "/")
            for p in base.rglob("*.md")
            if p.name not in ("README.md", "_template.md")
        )

    agents_dir = repo_root / ".claude" / "agents"
    skills_dir = repo_root / ".claude" / "skills"
    cmds_dir = repo_root / ".claude" / "commands"
    targets = _parse_makefile_targets(repo_root)
    return {
        "claude_md": (repo_root / "CLAUDE.md").exists(),
        "agents_md": (repo_root / "AGENTS.md").exists(),
        "constitution": (repo_root / "CONSTITUTION.md").exists(),
        "rules": _list_md((".claude", "rules")),
        "code_review": _list_md((".claude", "code-review")),
        "agents": sorted(p.name for p in agents_dir.glob("*.md")) if agents_dir.is_dir() else [],
        "skills": sorted(d.name for d in skills_dir.iterdir() if d.is_dir())
        if skills_dir.is_dir()
        else [],
        "commands": sorted(p.name for p in cmds_dir.glob("*.md")) if cmds_dir.is_dir() else [],
        "makefile": (repo_root / "Makefile").exists(),
        "makefile_targets": targets,
        "makefile_gates_present": [t for t in ("fmt", "lint", "test", "build") if t in targets],
        "has_verify": "verify" in targets,
        "settings_local": (repo_root / ".claude" / "settings.local.json").exists(),
        "mcp_servers": _enabled_mcp(repo_root),
        "ci": (repo_root / ".github" / "workflows").is_dir(),
        "engine_present": (repo_root / ".claude" / "skills" / ENGINE_NAME).is_dir(),
        "specced_present": config_path(repo_root).exists(),
    }


def _synthesize_checks(
    repo_root: Path, targets: dict[str, str], actions: list[dict[str, str]], force: bool
) -> dict[str, Any]:
    """Write .specced/checks.json from the repo's ACTUAL Makefile targets (not a preset).
    Falls back to chaining the present gates when there's no `verify` aggregator."""
    present = [t for t in ("fmt", "lint", "test", "build") if t in targets]
    has_verify = "verify" in targets
    has_full = "verify-full" in targets
    if has_verify:
        all_cmd: str | None = "make verify"
    elif present:
        all_cmd = " && ".join(f"make {t}" for t in present)
    else:
        all_cmd = None
    note = "Synthesized by `specced adopt` from your existing Makefile targets."
    if not has_verify:
        note += " No `verify` target found — `all` chains the present gates; add a `verify`/`verify-full` aggregator (or let the interview)."
    payload = {
        "all": all_cmd,
        "all_full": "make verify-full" if has_full else None,
        "gates": {t: f"make {t}" for t in present},
        "raw_commands": {t: targets[t] for t in present if targets[t]},
        "note": note,
    }
    _write_file(
        repo_root / ".specced" / "checks.json", json.dumps(payload, indent=2) + "\n", force, actions
    )
    return payload


def _adopt_plan(inv: dict[str, Any]) -> list[dict[str, str]]:
    plan: list[dict[str, str]] = [
        {
            "step": "engine",
            "action": "refresh" if inv["engine_present"] else "install",
            "detail": "proof-loop engine + 4 task agents"
            + (" (present — refresh to this version)" if inv["engine_present"] else ""),
        },
        {
            "step": "guide-blocks",
            "action": "upsert",
            "detail": "specced managed + orientation blocks in CLAUDE.md/AGENTS.md (existing prose preserved)",
        },
    ]
    if inv["makefile"]:
        present = ", ".join(inv["makefile_gates_present"]) or "none of fmt/lint/test/build"
        plan.append(
            {
                "step": "checks",
                "action": "synthesize",
                "detail": f".specced/checks.json from your Makefile targets ({present})",
            }
        )
        if not inv["has_verify"]:
            plan.append(
                {
                    "step": "gate",
                    "action": "flag",
                    "detail": "no `verify` aggregator — checks.json chains present gates; add `verify`/`verify-full` or let the interview",
                }
            )
    else:
        plan.append(
            {
                "step": "checks",
                "action": "flag",
                "detail": "no Makefile — the interview must wire a verification vocabulary",
            }
        )
    plan.append(
        {
            "step": "permissions",
            "action": "keep" if inv["settings_local"] else "scaffold",
            "detail": "pre-authorize your Makefile commands in .claude/settings.local.json"
            + (" (exists — left as-is)" if inv["settings_local"] else ""),
        }
    )
    plan.append(
        {"step": "repo-map", "action": "generate", "detail": ".specced/repo-map.md from detection"}
    )
    plan.append(
        {
            "step": "rules",
            "action": "keep" if inv["rules"] else "flag",
            "detail": f"{len(inv['rules'])} existing rule file(s) left as-is — the interview aligns them"
            if inv["rules"]
            else "no .claude/rules — the interview authors conventions",
        }
    )
    if inv["code_review"]:
        plan.append(
            {
                "step": "dims",
                "action": "keep",
                "detail": f"{len(inv['code_review'])} existing review dimension(s) left as-is",
            }
        )
    plan.append(
        {
            "step": "constitution",
            "action": "keep" if inv["constitution"] else "flag",
            "detail": "CONSTITUTION.md left untouched"
            if inv["constitution"]
            else "no CONSTITUTION.md — the interview authors the non-negotiables",
        }
    )
    if inv["mcp_servers"]:
        plan.append(
            {
                "step": "mcp",
                "action": "adopt",
                "detail": f"record existing .mcp.json servers: {', '.join(inv['mcp_servers'])}",
            }
        )
    return plan


def _adopt_followups(inv: dict[str, Any]) -> list[str]:
    """The semantic work adopt leaves to the bootstrap interview (it won't guess)."""
    out: list[str] = []
    if inv["claude_md"]:
        out.append(
            "Classify freeform CLAUDE.md guidance into CONSTITUTION clauses vs `.claude/rules/` vs review dimensions."
        )
    if inv["rules"]:
        out.append(
            f"Align the {len(inv['rules'])} existing rule(s) to specced's one-line, checkable idiom; split any that mix concerns."
        )
    else:
        out.append("Author `.claude/rules/<track>/*.md` conventions from the code.")
    if not inv["constitution"]:
        out.append("Author CONSTITUTION.md — the hard, enforced-today invariants.")
    if not inv["code_review"]:
        out.append("Author review dimensions in `.claude/code-review/NN-*.md`.")
    if inv["makefile"] and not inv["has_verify"]:
        out.append("Add `verify`/`verify-full` aggregator targets so the gate has one entry point.")
    out.append(
        "Run the specced-bootstrap interview to do the above from the code, then `specced doctor`."
    )
    return out


# --------------------------------------------------------------------------- #
# Config (.specced/config.json) — the durable record of what was decided
# --------------------------------------------------------------------------- #
def config_path(repo_root: Path) -> Path:
    return repo_root / ".specced" / "config.json"


def read_config(repo_root: Path) -> dict[str, Any]:
    path = config_path(repo_root)
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def write_config(repo_root: Path, data: dict[str, Any]) -> None:
    path = config_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _engine_record() -> dict[str, str]:
    return {**ENGINE_ATTRIBUTION, "version": engine_version()}


# --------------------------------------------------------------------------- #
# Public commands
# --------------------------------------------------------------------------- #
def init_repo(
    repo_root: Path,
    *,
    minimal: bool = False,
    force: bool = False,
    format_cmd: str | None = None,
    preset: str | None = None,
) -> dict[str, Any]:
    """Install the setup into ``repo_root`` (idempotent). ``preset`` may be a name
    or ``"auto"`` to choose one from stack detection."""
    actions: list[dict[str, str]] = []

    detection = _detect.detect(repo_root) if (not minimal or preset == "auto") else None
    preset_name = preset
    if preset_name == "auto":
        preset_name = (detection or {}).get("suggested_preset")
    preset_data = load_preset(preset_name)
    make = (preset_data or {}).get("make", {})

    ctx = {
        "PROJECT_NAME": repo_root.name,
        "CREATED_AT": _now(),
        "FORMAT_COMMAND": format_cmd or "make fmt lint",
        "FMT_CMD": make.get("fmt") or '@echo "TODO(specced): wire up your formatter"',
        "LINT_CMD": make.get("lint") or '@echo "TODO(specced): wire up your linter"',
        "TEST_CMD": make.get("test") or '@echo "TODO(specced): wire up your tests"',
        "BUILD_CMD": make.get("build") or '@echo "TODO(specced): wire up your build"',
    }

    _install_engine(repo_root, actions, force)
    _install_agents(repo_root, actions)
    _install_managed_blocks(repo_root, actions)
    if not minimal:
        _install_layer2(repo_root, actions, force, ctx)
        if preset_data:
            _apply_preset_content(repo_root, preset_data, actions, force)
            mcp_result = compose_mcp(repo_root, preset_data.get("mcp_servers", []), force=force)
            actions.append(
                {
                    "path": str(repo_root / ".mcp.json"),
                    "action": f"mcp servers: {', '.join(mcp_result['servers'])}",
                }
            )
        _install_permissions(repo_root, preset_data, actions, force)
        _write_checks(repo_root, preset_data, actions, force)
        _write_repo_map(repo_root, detection, preset_data, actions, force)

    cfg = read_config(repo_root)
    cfg.setdefault("created_at", _now())
    cfg.setdefault("skills", [])
    cfg.setdefault("mcp_servers", [])
    if preset_data:
        cfg["preset"] = preset_data.get("name", preset_name)
        cfg["tracks"] = preset_data.get("tracks", [])
    else:
        cfg.setdefault("preset", None)
        cfg.setdefault("tracks", [])
    if format_cmd:
        cfg["format_cmd"] = format_cmd
    cfg["specced_version"] = SPECCED_VERSION
    cfg["engine"] = _engine_record()
    cfg["updated_at"] = _now()
    write_config(repo_root, cfg)
    actions.append({"path": str(config_path(repo_root)), "action": "wrote config"})

    if not minimal:
        _install_orientation(repo_root, cfg, actions)

    report: dict[str, Any] = {
        "repo_root": str(repo_root),
        "minimal": minimal,
        "preset": preset_data.get("name") if preset_data else None,
        "engine_version": engine_version(),
        "actions": actions,
    }
    if detection:
        report["detection_summary"] = detection.get("summary")
    report["next"] = (
        "Fill CONSTITUTION.md, .claude/rules/, and .claude/code-review/ with project "
        "content (the interview does this), then run `specced doctor`."
    )
    return report


def adopt(repo_root: Path, *, apply: bool = False) -> dict[str, Any]:
    """Absorb an existing hand-built setup into specced management — the inverse of init.

    Dry-run by default: the **plan** is the deliverable. ``apply=True`` executes only the
    mechanical, non-destructive steps — it CREATES specced-owned files and UPSERTS managed
    blocks (which preserve surrounding prose), and never rewrites the repo's Makefile,
    CONSTITUTION, rules, dimensions, or .mcp.json. The semantic work (classifying prose,
    aligning rules, authoring missing layers) is handed to the interview as followups."""
    detection = _detect.detect(repo_root)
    inv = _inventory_existing(repo_root)
    found = {k: v for k, v in inv.items() if k != "makefile_targets"}
    found["makefile_targets"] = sorted(inv["makefile_targets"])

    result: dict[str, Any] = {
        "repo_root": str(repo_root),
        "mode": "applied" if apply else "plan",
        "detection_summary": detection.get("summary"),
        "found": found,
        "plan": _adopt_plan(inv),
        "interview_followups": _adopt_followups(inv),
    }

    if not apply:
        result["next"] = (
            "Review the plan, then `specced adopt --apply` to run the mechanical steps. "
            "The interview_followups are authored by the specced-bootstrap interview."
        )
        return result

    actions: list[dict[str, str]] = []
    _install_engine(repo_root, actions, force=True)
    _install_agents(repo_root, actions)
    _install_managed_blocks(repo_root, actions)
    if inv["makefile"]:
        _synthesize_checks(repo_root, inv["makefile_targets"], actions, force=True)
    _install_permissions(repo_root, {"make": inv["makefile_targets"]}, actions, force=False)
    _write_repo_map(repo_root, detection, None, actions, force=True)

    cfg = read_config(repo_root)
    cfg.setdefault("created_at", _now())
    cfg.setdefault("skills", inv["skills"])
    cfg["adopted"] = True
    cfg["adopted_at"] = _now()
    cfg["preset"] = None  # adopt never applies a preset's content over the user's own
    cfg["detected_preset"] = detection.get("suggested_preset")
    cfg["tracks"] = detection.get("tracks", [])
    cfg["mcp_servers"] = inv["mcp_servers"]
    cfg["specced_version"] = SPECCED_VERSION
    cfg["engine"] = _engine_record()
    cfg["updated_at"] = _now()
    write_config(repo_root, cfg)
    actions.append({"path": str(config_path(repo_root)), "action": "wrote config (adopted)"})

    _install_orientation(repo_root, cfg, actions)

    result["actions"] = actions
    result["next"] = (
        "Mechanical adoption done. Run the specced-bootstrap interview for the semantic "
        "steps (see interview_followups), then `specced doctor`."
    )
    return result


def list_library_skills() -> list[str]:
    root = templates_dir() / "skills"
    if not root.is_dir():
        return []
    return sorted(
        d.name
        for d in root.iterdir()
        if d.is_dir() and d.name != ENGINE_NAME and (d / "SKILL.md").exists()
    )


def add_skill(repo_root: Path, name: str, *, force: bool = False) -> dict[str, Any]:
    src = templates_dir() / "skills" / name
    if not (src / "SKILL.md").exists():
        return {
            "ok": False,
            "error": f"unknown library skill '{name}'",
            "available": list_library_skills(),
        }
    dst = repo_root / ".claude" / "skills" / name
    if dst.exists() and not force:
        return {"ok": False, "error": f"already installed at {dst}; pass --force to replace"}
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)

    cfg = read_config(repo_root)
    skills = set(cfg.get("skills", []))
    skills.add(name)
    cfg["skills"] = sorted(skills)
    cfg["updated_at"] = _now()
    write_config(repo_root, cfg)
    return {"ok": True, "skill": name, "installed": str(dst)}


def sync(repo_root: Path) -> dict[str, Any]:
    """Refresh the engine, agents, and managed blocks to this specced version."""
    actions: list[dict[str, str]] = []
    _install_engine(repo_root, actions, True)
    _install_agents(repo_root, actions)
    _install_managed_blocks(repo_root, actions)
    cfg = read_config(repo_root)
    cfg["specced_version"] = SPECCED_VERSION
    cfg["engine"] = _engine_record()
    cfg["updated_at"] = _now()
    write_config(repo_root, cfg)
    return {
        "repo_root": str(repo_root),
        "synced": True,
        "engine_version": engine_version(),
        "actions": actions,
    }


def doctor(repo_root: Path) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def check(name: str, ok: bool, hint: str = "") -> None:
        checks.append({"check": name, "ok": bool(ok), "hint": "" if ok else hint})

    engine = repo_root / ".claude" / "skills" / ENGINE_NAME
    check("engine installed", engine.is_dir(), "run: specced init")
    check(
        "engine runner present",
        (engine / "scripts" / "task_loop.py").exists(),
        "engine copy incomplete: specced init --force",
    )
    for name in CLAUDE_AGENT_TEMPLATES:
        agent = repo_root / ".claude" / "agents" / name[: -len(".tmpl")]
        check(f"claude agent: {name[: -len('.md.tmpl')]}", agent.exists(), "specced sync")
    claude = repo_root / "CLAUDE.md"
    check(
        "CLAUDE.md managed block",
        claude.exists() and MANAGED_START in claude.read_text(encoding="utf-8"),
        "specced init",
    )
    check("specced config", config_path(repo_root).exists(), "specced init")

    ok = all(c["ok"] for c in checks)
    return {
        "repo_root": str(repo_root),
        "ok": ok,
        "checks": checks,
        "warnings": _content_warnings(repo_root),
        "suggestions": _mcp_suggestions(repo_root),
    }


def status(repo_root: Path) -> dict[str, Any]:
    skills_dir = repo_root / ".claude" / "skills"
    installed_skills = (
        sorted(d.name for d in skills_dir.iterdir() if d.is_dir()) if skills_dir.is_dir() else []
    )
    return {
        "repo_root": str(repo_root),
        "specced_version": SPECCED_VERSION,
        "engine_version": engine_version(),
        "engine_installed": (repo_root / ".claude" / "skills" / ENGINE_NAME).is_dir(),
        "installed_skills": installed_skills,
        "library_skills": list_library_skills(),
        "available_presets": [p["name"] for p in list_presets()],
        "mcp_catalog": sorted(mcp_catalog()),
        "config": read_config(repo_root),
    }
