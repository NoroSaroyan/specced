# Architecture

specced is two surfaces over one set of templates.

## Two surfaces

- **CLI (`src/specced/`)** — deterministic, agent-agnostic mechanics. Installs the
  engine, agents, managed blocks, and Layer-2 skeletons; applies presets; composes
  MCP. Idempotent, scriptable, CI-able. Every command emits JSON.
- **Plugin (`plugin/`)** — the Claude Code plugin. Its `specced-bootstrap` skill runs
  the **interview**: detect → ask → call the CLI → author project-specific content.
  It ships no templates; it drives the CLI.

The repo is also a **marketplace** (`.claude-plugin/marketplace.json`) so the plugin
installs with `/plugin marketplace add` + `/plugin install`.

## Three layers installed into a target repo

1. **Engine** — `.claude/skills/repo-task-proof-loop/` (vendored, Apache-2.0). The
   spec-freeze → build → evidence → fresh-verify → fix loop with `.agent/tasks/<ID>/`.
2. **Structure** — `.claude/agents/` + `.codex/agents/` (4 agents), managed
   `<!-- repo-task-proof-loop -->` blocks in `CLAUDE.md`/`AGENTS.md`, a Stop-hook in
   `.claude/settings.json`, and a `Makefile` verification vocabulary.
3. **Content** — `CONSTITUTION.md`, `.claude/rules/**`, `.claude/code-review/**`,
   `.mcp.json`. Presets stub these; the interview fills them.

## Single source of truth

All templates live in `src/specced/templates/` and ship in the wheel. The CLI reads
them via `importlib.resources`. The plugin never duplicates them — it calls the CLI.

## State

`.specced/config.json` in the target repo records the specced + engine versions, the
chosen preset, tracks, installed skills, and MCP servers. `specced doctor` checks the
install; `specced sync` refreshes the engine/agents/blocks to the current version.

## Why managed blocks

The proof-loop section in `CLAUDE.md`/`AGENTS.md` lives between
`<!-- repo-task-proof-loop:start -->` / `:end` markers. Re-running `init` upserts that
block in place and never touches surrounding user content — the markers are identical
to the engine's own, so a repo that used the engine directly keeps one block, not two.
