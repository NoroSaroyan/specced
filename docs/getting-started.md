# Getting started

This walks you from zero to a bootstrapped repo running its first task. ~10 minutes.

## 1. Install the CLI

```bash
uv tool install specced
# or run without installing:
uvx --from git+https://github.com/NoroSaroyan/specced specced version
```

Check it: `specced version` → prints the specced and engine versions.

> Prefer pip? `pipx install specced` works too. The CLI is pure-Python, no runtime deps.

## 2. Install the Claude Code plugin

The plugin provides the interview. In Claude Code:

```
/plugin marketplace add NoroSaroyan/specced
/plugin install specced
```

This adds three commands: `/specced:init`, `/specced:add-skill`, `/specced:doctor`.

## 3. Bootstrap your repo

From inside the target repository, run:

```
/specced:init
```

The `specced-bootstrap` skill will:

1. **Detect** your stack (`specced detect`) — languages, frameworks, tracks, databases.
2. **Interview** you — a few batched questions about your verification commands,
   non-negotiables, conventions, MCP servers, and which skills you want. Detected
   answers are pre-filled as the recommended option.
3. **Scaffold** — runs `specced init --preset <name>` to install the engine, agents,
   managed guide blocks, a prefilled `Makefile`, rule/review stubs, and `.mcp.json`.
4. **Author** your `CONSTITUTION.md`, `.claude/rules/**`, and `.claude/code-review/**`
   from your answers.
5. **Verify** with `specced doctor` and summarize.

Prefer to do it by hand, or not in Claude Code? The CLI alone is enough:

```bash
specced detect                       # see what it found
specced init --preset auto           # or: --preset python-fastapi
specced add-mcp postgres github      # add MCP servers from the catalog
specced add-skill api-endpoint       # add a task skill
specced doctor                       # check the install
```

## 4. What landed in your repo

```
CONSTITUTION.md                      # your non-negotiables
CLAUDE.md / AGENTS.md                # proof-loop block + specced orientation block
Makefile                             # fmt / lint / test / build / verify  (your AC vocabulary)
.mcp.json                            # MCP servers
.claude/
  settings.json                      # Stop-hook: format + lint on every session end
  settings.local.json                # pre-authorized verify commands + enabled MCP servers
  agents/        task-*.md           # spec-freezer, builder, verifier, fixer
  skills/        repo-task-proof-loop + any you added
  rules/         <track>/*.md        # coding conventions (you fill these)
  code-review/   NN-*.md             # review dimensions
.codex/agents/   task-*.toml         # the same agents for Codex
.agent/                              # created when you run your first task
.specced/
  config.json                        # what specced installed + your choices
  checks.json                        # gate -> command (AC vocabulary, machine-readable)
  repo-map.md                        # generated orientation for agents
```

See [Concepts](concepts.md) for what each piece is for.

## 5. Run your first task

The setup is built around the **proof loop**. In Claude Code, invoke the installed
engine skill and name a task:

```
Use the repo-task-proof-loop skill: init add-healthcheck-endpoint
```

Then describe the work. The loop will freeze a spec with runnable acceptance criteria,
build it, pack evidence, verify in a fresh pass, and fix until the verifier says PASS —
leaving an audit trail in `.agent/tasks/add-healthcheck-endpoint/`.

Full walkthrough: [The proof loop](proof-loop.md).

## Re-running and updating

- `/specced:init` (or `specced init`) is **idempotent** — safe to re-run; it won't
  clobber your authored files.
- `specced sync` refreshes the engine, agents, and managed blocks to your installed
  specced version.
- `specced doctor` tells you if anything has drifted.
