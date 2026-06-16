# Stack presets

A preset prefills the stack-specific defaults so the interview is short. Apply one with
`specced init --preset <name>`, or let detection choose: `specced init --preset auto`.

List them: `specced presets`. Current set:

| preset | for |
|---|---|
| `go` | Go module / monorepo (gofmt + golangci-lint + go test) |
| `rust` | Rust crate / workspace (rustfmt + clippy + cargo test) |
| `python-fastapi` | FastAPI backend (ruff + mypy + pytest + alembic) |
| `python-django` | Django backend (ruff + manage.py check + pytest) |
| `python` | generic Python (ruff + pytest) |
| `node-next` | Next.js / React frontend |
| `node-svelte` | SvelteKit frontend |
| `node-react` | React SPA (Vite) |
| `node-express` | Node/TypeScript backend API (Express or NestJS) |
| `node` | generic Node / TypeScript |
| `java-spring` | Spring Boot service (Maven wrapper) |
| `ruby-rails` | Ruby on Rails app |
| `tauri` | Tauri desktop app — web frontend + Rust backend in `src-tauri/` |

`specced detect` suggests a preset from the repo's signals; `--preset auto` applies it.
Java without Spring and Ruby without Rails resolve to "no preset" — the interview asks
instead of guessing.

## What a preset controls

- **`make`** → the `fmt` / `lint` / `test` / `build` recipes in the generated `Makefile`
  (the proof loop's acceptance-criteria vocabulary). The template wires a **two-level gate**:
  `make verify` (fmt+lint+test, everyday) and `make verify-full` (adds `build`, for
  features/release) — both recorded in `.specced/checks.json` (`all` / `all_full`).
- **`tracks`** → recorded in `.specced/config.json`.
- **`mcp_servers`** → composed into `.mcp.json` from the catalog.
- **`rules`** → per-track stub files created under `.claude/rules/`.
- **`code_review`** → dimension stub files created under `.claude/code-review/`.

## Schema

`src/specced/templates/presets/<name>.json`:

```json
{
  "name": "python-fastapi",
  "description": "FastAPI backend (ruff + mypy + pytest + alembic).",
  "language": "python",
  "detect": { "any_frameworks": ["fastapi"], "priority": 79 },
  "make": { "fmt": "ruff format .", "lint": "ruff check . && mypy .",
            "test": "pytest -q", "build": "python -m build" },
  "tracks": ["backend"],
  "mcp_servers": ["postgres", "github", "context7"],
  "rules": ["backend/architecture.md", "backend/api.md"],
  "code_review": ["01-api.md", "02-tests.md"]
}
```

Every server in `mcp_servers` must exist in the catalog (`templates/mcp/servers.json`);
a test enforces this.

## Adding a preset

Detection is **data-driven** — adding an auto-detected preset is one JSON file, no code:

1. Drop the JSON in `src/specced/templates/presets/`, including a `detect` block:
   `"detect": { "any_frameworks": ["fastapi"], "priority": 79 }`. The preset's top-level
   `language` must be present in the repo; if `any_frameworks` is set, at least one must
   match; higher `priority` wins (set it above the generic same-language preset). Omit the
   `detect` block for a manual-only preset.
2. Add any new servers it needs to `templates/mcp/servers.json`.
3. Run `make verify` — the property tests automatically check the new preset is valid and
   reachable; only a brand-new *language* needs a line in `detect.py:suggest_verification`.

Presets are starting points — for monorepos with multiple stacks, the interview fills in
the second track's commands and rules by hand.
