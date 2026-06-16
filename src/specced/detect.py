"""Stack detection for the bootstrap interview.

Pure, dependency-free inspection of a repo: languages, package managers, tracks,
candidate verification commands, data/infra signals, and existing conventions.
The interview reads this so it can *confirm* detections instead of asking blind,
and ``specced init --preset auto`` uses it to pick a preset.

Kept stdlib-only (text + JSON scans, no tomllib) to honor requires-python >= 3.10.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from ._paths import templates_dir

TRACK_DIRS = (
    "backend",
    "frontend",
    "ml",
    "infra",
    "services",
    "api",
    "web",
    "app",
    "apps",
    "packages",
    "server",
    "client",
    "mobile",
)

# Dirs counted as a track even without their own manifest (real monorepo containers).
# Others (app/, src/, lib/, web/, api/) only count as a track if they hold a manifest —
# this keeps a Next.js `app/` router dir from being mistaken for a monorepo track.
STRONG_TRACKS = (
    "backend",
    "frontend",
    "ml",
    "services",
    "packages",
    "apps",
    "server",
    "client",
    "mobile",
    "infra",
)

DB_IMAGES = (
    "postgres",
    "mysql",
    "mariadb",
    "redis",
    "qdrant",
    "mongo",
    "elasticsearch",
    "clickhouse",
)


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _has_manifest(directory: Path) -> bool:
    return any(
        (directory / m).exists()
        for m in (
            "package.json",
            "pyproject.toml",
            "go.mod",
            "Cargo.toml",
            "pom.xml",
            "build.gradle",
            "Gemfile",
        )
    )


COMPOSE_NAMES = ("docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml")


def _compose_files(root: Path) -> list[Path]:
    """docker-compose files at the root and in common infra dirs (deploy/, infra/, …),
    including one level down (e.g. deploy/docker-compose/docker-compose.yml)."""
    found: list[Path] = [root / n for n in COMPOSE_NAMES if (root / n).exists()]
    for d in ("deploy", "infra", "docker", "ops", ".docker"):
        base = root / d
        if base.is_dir():
            for n in COMPOSE_NAMES:
                found.extend(base.glob(n))
                found.extend(base.glob(f"*/{n}"))
    return found


def _load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _manifest_dirs(root: Path) -> list[Path]:
    """Root plus immediate track subdirs — enough to see a backend/+frontend/ monorepo."""
    dirs = [root]
    for name in TRACK_DIRS:
        d = root / name
        if d.is_dir():
            dirs.append(d)
    return dirs


def detect(repo_root: Path) -> dict[str, Any]:
    root = repo_root
    languages: set[str] = set()
    frameworks: set[str] = set()
    tools: set[str] = set()
    node_scripts: dict[str, str] = {}

    for d in _manifest_dirs(root):
        pyproject = _read(d / "pyproject.toml")
        if pyproject or (d / "requirements.txt").exists() or (d / "setup.py").exists():
            languages.add("python")
            for dep in ("fastapi", "django", "flask", "sqlalchemy", "alembic", "pydantic"):
                if re.search(rf"\b{dep}\b", pyproject, re.IGNORECASE):
                    frameworks.add(dep)
            for tool in ("ruff", "black", "mypy", "pytest", "tox", "nox"):
                if re.search(rf"\b{tool}\b", pyproject, re.IGNORECASE):
                    tools.add(tool)

        pkg = _load_json(d / "package.json")
        if pkg:
            languages.add("node")
            node_scripts.update(pkg.get("scripts", {}) or {})
            alldeps = {**(pkg.get("dependencies") or {}), **(pkg.get("devDependencies") or {})}
            for dep in (
                "next",
                "react",
                "vue",
                "svelte",
                "@sveltejs/kit",
                "vite",
                "express",
                "@nestjs/core",
                "vitest",
                "jest",
                "eslint",
                "prettier",
                "typescript",
            ):
                if dep in alldeps:
                    frameworks.add(dep.split("/")[0].lstrip("@"))

        if (d / "go.mod").exists():
            languages.add("go")
        if (d / "Cargo.toml").exists():
            languages.add("rust")
        jvm = _read(d / "pom.xml") + _read(d / "build.gradle") + _read(d / "build.gradle.kts")
        if jvm:
            languages.add("java")
            if re.search(r"spring", jvm, re.IGNORECASE):
                frameworks.add("spring")
        gemfile = _read(d / "Gemfile")
        if gemfile:
            languages.add("ruby")
            if re.search(r"\brails\b", gemfile, re.IGNORECASE):
                frameworks.add("rails")

    if (root / ".golangci.yml").exists() or (root / ".golangci.yaml").exists():
        tools.add("golangci-lint")

    # Tauri desktop app: a web frontend plus a Rust backend in src-tauri/.
    if (root / "src-tauri" / "Cargo.toml").exists():
        languages.add("rust")
        frameworks.add("tauri")

    tracks = [
        name
        for name in TRACK_DIRS
        if (root / name).is_dir() and (name in STRONG_TRACKS or _has_manifest(root / name))
    ]
    if (root / "src-tauri" / "Cargo.toml").exists():
        tracks.append("src-tauri")

    # data / infra
    infra: dict[str, Any] = {
        "databases": [],
        "supabase": False,
        "migrations": None,
        "docker_compose": False,
    }
    for compose in _compose_files(root):
        text = _read(compose)
        if text:
            infra["docker_compose"] = True
            for img in DB_IMAGES:
                if re.search(rf"image:\s*[\"']?{img}", text, re.IGNORECASE):
                    if img not in infra["databases"]:
                        infra["databases"].append(img)
    if (root / "supabase").is_dir():
        infra["supabase"] = True
        if "postgres" not in infra["databases"]:
            infra["databases"].append("postgres")
    for mig in ("alembic", "migrations", "prisma", "db/migrate"):
        if (root / mig).exists() or any((root / t / "alembic").exists() for t in tracks):
            infra["migrations"] = mig
            break

    existing = {
        "constitution": (root / "CONSTITUTION.md").exists(),
        "claude_dir": (root / ".claude").is_dir(),
        "docs": (root / "docs").is_dir(),
        "ci": (root / ".github" / "workflows").is_dir(),
        "git": (root / ".git").exists(),
        "specced": (root / ".specced" / "config.json").exists(),
    }

    detection = {
        "repo_root": str(root),
        "languages": sorted(languages),
        "frameworks": sorted(frameworks),
        "tools": sorted(tools),
        "node_scripts": node_scripts,
        "tracks": tracks,
        "infra": infra,
        "existing": existing,
        "monorepo": len([t for t in tracks if t in ("backend", "frontend", "ml")]) >= 2,
    }
    detection["suggested_preset"] = suggest_preset(detection)
    detection["suggested_mcp"] = suggest_mcp(detection)
    detection["suggested_verification"] = suggest_verification(detection)
    detection["summary"] = summary(detection)
    return detection


def _load_presets() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for path in sorted((templates_dir() / "presets").glob("*.json")):
        try:
            out.append(json.loads(path.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            continue
    return out


def suggest_preset(d: dict[str, Any]) -> str | None:
    """Pick the highest-priority preset whose declared markers match the repo.

    Detection is DATA-DRIVEN: each preset file (templates/presets/*.json) carries a
    `detect` block, e.g. ``{"any_frameworks": ["next"], "priority": 52}``. The preset's
    top-level ``language`` must be present in the repo; if ``any_frameworks`` is given,
    at least one must match. A preset with no ``any_frameworks`` is the generic fallback
    for its language. Adding an auto-detected preset is therefore one JSON file, no code.
    """
    langs = set(d["languages"])
    fw = set(d["frameworks"])
    best: str | None = None
    best_priority = -1
    for preset in _load_presets():
        det = preset.get("detect")
        if det is None:
            continue
        language = det.get("language") or preset.get("language")
        if not language or language not in langs:
            continue
        any_frameworks = det.get("any_frameworks") or []
        if any_frameworks and not (fw & set(any_frameworks)):
            continue
        priority = det.get("priority", 0)
        if priority > best_priority:
            best_priority = priority
            best = preset.get("name")
    return best


def suggest_mcp(d: dict[str, Any]) -> list[str]:
    servers = ["context7"]
    if d["existing"]["ci"] or d["existing"]["git"]:
        servers.append("github")
    infra = d["infra"]
    if infra["supabase"]:
        servers.append("supabase")
    elif "postgres" in infra["databases"]:
        servers.append("postgres")
    if "qdrant" in infra["databases"]:
        servers.append("qdrant")
    # de-dup, preserve order
    seen: set[str] = set()
    return [s for s in servers if not (s in seen or seen.add(s))]


def suggest_verification(d: dict[str, Any]) -> dict[str, str | None]:
    langs = d["languages"]
    tools = set(d["tools"])
    scripts = d["node_scripts"]
    out: dict[str, str | None] = {"fmt": None, "lint": None, "test": None, "build": None}
    if "python" in langs:
        out["fmt"] = "ruff format ." if "ruff" in tools else "black ."
        out["lint"] = "ruff check ." + (" && mypy ." if "mypy" in tools else "")
        out["test"] = "pytest -q"
        out["build"] = "python -m build"
    if "go" in langs:
        out["fmt"] = "gofmt -w ."
        out["lint"] = "golangci-lint run" if "golangci-lint" in tools else "go vet ./..."
        out["test"] = "go test ./..."
        out["build"] = "go build ./..."
    if "rust" in langs:
        out["fmt"] = "cargo fmt"
        out["lint"] = "cargo clippy --all-targets -- -D warnings"
        out["test"] = "cargo test"
        out["build"] = "cargo build --release"
    if "java" in langs:
        out["fmt"] = "./mvnw spotless:apply"
        out["lint"] = "./mvnw -q verify -DskipTests"
        out["test"] = "./mvnw test"
        out["build"] = "./mvnw -q package -DskipTests"
    if "ruby" in langs:
        out["fmt"] = "bundle exec rubocop -A"
        out["lint"] = "bundle exec rubocop"
        out["test"] = "bundle exec rspec"
        out["build"] = "bundle exec rails zeitwerk:check"
    if "node" in langs:
        if "lint" in scripts:
            out["lint"] = "npm run lint"
        if "build" in scripts:
            out["build"] = "npm run build"
        if "test" in scripts:
            out["test"] = "npm test"
        if "format" in scripts:
            out["fmt"] = "npm run format"
    return out


def summary(d: dict[str, Any]) -> list[str]:
    lines = []
    lines.append(f"languages: {', '.join(d['languages']) or 'unknown'}")
    if d["frameworks"]:
        lines.append(f"frameworks: {', '.join(d['frameworks'])}")
    if d["tracks"]:
        lines.append(
            f"tracks: {', '.join(d['tracks'])}" + ("  (monorepo)" if d["monorepo"] else "")
        )
    if d["infra"]["databases"]:
        lines.append(
            f"data: {', '.join(d['infra']['databases'])}"
            + ("  +supabase" if d["infra"]["supabase"] else "")
        )
    if d["suggested_preset"]:
        lines.append(f"suggested preset: {d['suggested_preset']}")
    lines.append(f"suggested mcp: {', '.join(d['suggested_mcp'])}")
    return lines
