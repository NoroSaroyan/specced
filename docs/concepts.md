# Concepts

## The three layers

specced installs in three layers, from most generic to most project-specific:

1. **The engine** — the `repo-task-proof-loop` skill: a spec → build → evidence →
   fresh-verify → fix workflow with durable artifacts. Identical in every repo.
   (Vendored from OpenAI, Apache-2.0.)
2. **The structure** — the agents, managed guide blocks, the Stop-hook, and the
   skeletons for rules/code-review/mcp/Makefile. Same shape everywhere; presets
   prefill the stack-specific bits.
3. **The content** — your `CONSTITUTION.md`, coding rules, review dimensions, MCP
   servers, and verification commands. Unique to each repo; the interview writes it.

specced's job is to install (1) and (2) mechanically and help you author (3).

## Anatomy of a bootstrapped repo

| Path | What it is |
|---|---|
| `CONSTITUTION.md` | Global non-negotiables: invariants, budgets, security, attribution. Read first by agents. |
| `CLAUDE.md` / `AGENTS.md` | Guide files. Carry two managed blocks — the proof-loop workflow and a specced **orientation** block (links to rules, the repo map, the verify command, and MCP tools) — with your own content untouched around them. |
| `Makefile` | `fmt` / `lint` / `test` / `build` / `verify`. This **is** the acceptance-criteria vocabulary — when a spec says "AC: `make test` passes", it means this file. |
| `.mcp.json` | MCP servers the agent can use (database, github, etc.). |
| `.claude/settings.json` | Claude Code settings; a Stop-hook runs format+lint at session end. |
| `.claude/settings.local.json` | Pre-authorized permissions (your verify commands) + enabled MCP servers, so the agent runs unblocked by prompts. |
| `.claude/agents/task-*.md` | The four proof-loop roles (spec-freezer, builder, verifier, fixer). |
| `.codex/agents/task-*.toml` | The same roles for Codex. |
| `.claude/skills/` | The engine + any task skills you installed. |
| `.claude/rules/<track>/*.md` | Per-track coding conventions. Agents turn these into acceptance criteria and check against them. |
| `.claude/code-review/NN-*.md` | Dimension-based review guides + a severity rubric. |
| `.agent/tasks/<id>/` | Durable per-task artifacts (created when you run a task). |
| `.specced/config.json` | What specced installed: versions, preset, tracks, skills, MCP servers. |
| `.specced/checks.json` | Machine-readable gate → command map (the verification vocabulary). |
| `.specced/repo-map.md` | Generated orientation: stack, where things live, how to verify. |

## Constitution vs rules vs code-review

Three homes for "how we build here", by scope:

- **`CONSTITUTION.md`** — truly global, rarely-changing non-negotiables. A violation is
  always a blocking issue. Keep it short.
- **`.claude/rules/`** — per-layer conventions (how the API layer works, how migrations
  are written). Concrete and checkable. This is where most of your knowledge lives.
- **`.claude/code-review/`** — the lenses a reviewer applies to a diff, with severity
  guidance and the always-critical classes.

Rule of thumb: a global invariant → constitution; a layer convention → rules; a thing to
*check on every change* → a review dimension.

## Presets

A **preset** is a stack starting point (`python-fastapi`, `go`, `node-next`, …). It
prefills the `Makefile` commands, stubs per-track rules + review dimensions, and composes
the right MCP servers, so the interview is short. `specced detect` suggests one; you can
override with `--preset <name>`. See [Presets](presets.md).

## Skills

A **skill** is a reusable playbook for a recurring task (add an endpoint, write tests,
cut a release). Claude routes to a skill by its `description`, so you just describe the
task. specced ships a [library](skills.md); install the ones you want with
`specced add-skill`, or scaffold project-specific ones with the `new-domain-skill` skill.

## MCP servers

specced ships a catalog of common [MCP](https://modelcontextprotocol.io) servers
(postgres, qdrant, supabase, github, context7, playwright, sentry). `specced add-mcp
<names>` composes them into `.mcp.json`; secrets are referenced via `${ENV:-}`, never
inlined.

## Why managed blocks

The proof-loop section in `CLAUDE.md`/`AGENTS.md` sits between
`<!-- repo-task-proof-loop:start -->` / `:end` markers. Re-running `init` replaces just
that block and leaves the rest of the file alone — so specced can update its guidance
without ever touching your prose.
