# specced documentation

**specced** installs a reusable, interview-driven agentic coding setup into any repo —
the proof-loop engine, project agents, coding rules, code-review dimensions, and a
library of task skills — so you stop copy-pasting `.claude/` scaffolding between projects.

It is two things sharing one set of templates:

- a **uv-installable CLI** (`specced`) that does deterministic scaffolding, and
- a **Claude Code plugin** whose `specced-bootstrap` skill *interviews you* and writes
  the project-specific content.

## Who this is for

Developers who drive coding agents (Claude Code, Codex) and want a consistent,
auditable workflow — a spec → build → evidence → verify → fix loop — set up the same
way in every repo, tuned to each project's stack and rules.

## Read in this order

1. **[Getting started](getting-started.md)** — install, bootstrap a repo, run your first task.
2. **[Concepts](concepts.md)** — the mental model and the anatomy of a bootstrapped repo.
3. **[The proof loop](proof-loop.md)** — how to do day-to-day work with it.
4. **[CLI reference](cli-reference.md)** — every command and flag.
5. **[Skills](skills.md)** — the library of task playbooks.
6. **[Presets](presets.md)** — stack presets and how to add one.
7. **[FAQ & troubleshooting](faq.md)** — common questions and fixes.

Building on specced itself? See **[architecture](architecture.md)**,
**[authoring skills](authoring-skills.md)**, and **[how the interview works](interview.md)**.

## 30-second version

```bash
uv tool install specced            # the CLI
# in Claude Code, inside your repo:
/plugin marketplace add NoroSaroyan/specced
/plugin install specced
/specced:init                      # detect stack → interview → scaffold
```

You get a repo wired for the proof loop. Start a task by invoking the
`repo-task-proof-loop` skill with `init <task-id>` and describing the work.
