# specced — quickstart

Install a complete, project-tailored agentic coding setup into any repo in ~2 minutes.

## 1. Install the CLI

```bash
uv tool install specced      # or: pipx install specced
specced version
```

## 2. Bootstrap your repo

**With Claude Code (recommended — runs the interview):**

```
/plugin marketplace add NoroSaroyan/specced
/plugin install specced
/specced:init
```

`/specced:init` detects your stack, asks a few sharp questions, and scaffolds everything —
then writes your `CONSTITUTION.md`, coding rules, and review dimensions from your answers.

**CLI only (no interview):**

```bash
cd your-repo
specced init --preset auto    # or pick one: specced presets
specced doctor                # check the setup is healthy
```

Either way you get: the proof-loop engine, project agents, a two-level `make verify` /
`make verify-full` gate, `.claude/rules` + `.claude/code-review` skeletons, MCP servers, and
a permission allowlist so the agent runs unblocked.

## 3. Run your first task

In Claude Code, invoke the installed engine and name a task:

```
Use the repo-task-proof-loop skill: init add-my-feature
```

It runs **spec-freeze → build → evidence → fresh-verify → fix**, leaving an audit trail in
`.agent/tasks/<id>/`. "Done" means a fresh verifier reran your `make verify` gate and it passed.

## Handy follow-ups

```bash
specced list-skills                 # the task-skill library
specced add-skill api-endpoint      # install one
specced add-mcp postgres github     # wire MCP servers
specced status                      # what's installed
```

## Go deeper

- Full walkthrough: **[docs/getting-started.md](docs/getting-started.md)**
- Concepts, proof loop, CLI reference, presets, skills, FAQ: **[docs/](docs/index.md)**
