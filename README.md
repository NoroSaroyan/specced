# specced

Install a reusable, **interview-driven agentic coding setup** into any repo — one
command instead of copy-pasting `.claude/`, `.codex/`, `CONSTITUTION.md`, and the
proof-loop scaffolding between projects.

specced is two things sharing one set of templates:

- a **uv-installable CLI** that does the deterministic, agent-agnostic scaffolding, and
- a **Claude Code plugin** whose `specced-bootstrap` skill *interviews you* — detects
  your stack, asks a few sharp questions, and writes the project-specific content.

## What you get

specced installs three layers into a repo:

1. **The engine** — the [`repo-task-proof-loop`](src/specced/templates/skills/repo-task-proof-loop)
   skill (spec-freeze → build → evidence → fresh-verify → fix, with durable
   `.agent/tasks/<ID>/` artifacts). Vendored from OpenAI, Apache-2.0 — see [NOTICE](NOTICE).
2. **The structure** — four project agents (`.claude/agents/` + `.codex/agents/`),
   managed blocks in `CLAUDE.md`/`AGENTS.md`, a Stop-hook formatter, skeletons for
   `.claude/rules/`, `.claude/code-review/`, `.mcp.json`, and a `Makefile` verification
   vocabulary — plus an **agent-experience layer**: a pre-authorized permission
   allowlist, an orientation block, and a machine-readable checks map (`.specced/`).
3. **The content** *(interview)* — your real `CONSTITUTION.md`, per-track rules,
   review dimensions, MCP servers, and `make` targets — authored to fit *this* repo.

## Install

```bash
uv tool install specced          # or: uvx --from git+https://github.com/NoroSaroyan/specced specced
```

In Claude Code, add the marketplace and install the plugin:

```
/plugin marketplace add NoroSaroyan/specced
/plugin install specced
```

## Quickstart

From inside the target repo, in Claude Code:

```
/specced:init
```

This runs the interview: it detects your stack, asks what matters, runs
`specced init` for the mechanics, then writes your constitution, rules, review
dimensions, MCP servers, and Makefile targets. Add `--minimal` to author all
content by hand.

Then start your first task with the installed engine:

```
init my-first-task     # via the repo-task-proof-loop skill
```

## Documentation

Full docs in [`docs/`](docs/index.md):
[Getting started](docs/getting-started.md) ·
[Concepts](docs/concepts.md) ·
[The proof loop](docs/proof-loop.md) ·
[CLI reference](docs/cli-reference.md) ·
[Skills](docs/skills.md) ·
[Presets](docs/presets.md) ·
[FAQ](docs/faq.md)

## CLI reference

```
specced detect                    Inspect the repo: languages, tracks, infra,
                                  suggested preset + MCP servers (JSON).
specced presets                   List stack presets.
specced init [--preset NAME|auto] [--minimal] [--force] [--format-cmd "…"]
                                  Install / refresh the setup (idempotent).
specced add-mcp <names…> [--force]  Add MCP servers to .mcp.json from the catalog.
specced add-skill <name> [--force]  Install a library skill into .claude/skills/.
specced list-skills               List available library skills.
specced sync                      Refresh engine + agents + managed blocks.
specced doctor                    Verify the setup is consistent.
specced status                    Show installed components, presets, mcp catalog, config.
specced version                   Print specced + engine versions.
```

**13 presets** (`go`, `rust`, `python-fastapi`, `python-django`, `python`,
`node-next`, `node-svelte`, `node-react`, `node-express`, `node`, `java-spring`,
`ruby-rails`, `tauri` — see [docs/presets.md](docs/presets.md)) and a **17-skill library**
(code-review, api-endpoint, db-migration, add-integration, background-worker,
regen-client, write-tests, debug-issue, refactor, dependency-upgrade,
perf-investigation, security-review, release, prepare-pr, new-domain-skill,
decision-record, capture-rule — see [docs/skills.md](docs/skills.md)).

Every command prints JSON, so the interview agent can read exactly what happened.
State is recorded in `.specced/config.json`.

## How it works

The CLI is the mechanical half: it copies the vendored engine, installs the static
agent + managed-block templates verbatim (the same files the engine itself would
write), and lays down create-if-absent skeletons for the content layer. The plugin
is the intelligent half: the `specced-bootstrap` skill detects, interviews, calls
the CLI, then replaces the skeletons with real content. One template tree, two
surfaces.

## Develop

```bash
make install   # uv venv + editable install with dev extras
make verify    # ruff format --check + ruff check + pytest + build (the CI gate)
```

See [CONTRIBUTING.md](CONTRIBUTING.md) and [docs/architecture.md](docs/architecture.md).

## Status

v0.1 — interview-first, with stack detection, 13 presets, a 7-server MCP catalog, a
17-skill library, an agent-experience layer, and GitHub repo-as-code (Terraform under
`infra/terraform/github/`). Roadmap: a `specced update` that diffs managed content
across versions, more presets/skills, and PyPI publication.

## License

specced is MIT (see [LICENSE](LICENSE)). It bundles the Apache-2.0
`repo-task-proof-loop` engine unmodified; attribution in [NOTICE](NOTICE).
