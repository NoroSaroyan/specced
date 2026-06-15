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

SPECCED_VERSION = "0.1.0"

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
        "gates": {name: f"make {name}" for name in ("fmt", "lint", "test", "build")},
        "raw_commands": {k: make[k] for k in ("fmt", "lint", "test", "build") if make.get(k)},
        "note": "Run `all` for the full gate. Gates map to Makefile targets; the verifier reruns them.",
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
    return warnings


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
