---
name: new-domain-skill
description: Use when creating a new repeatable, project-specific skill / playbook for a recurring task in this repo — capturing "the right way" to do something (a kind of change, a workflow) so a fresh agent can do it correctly without extra context. Authors a `.claude/skills/<name>/SKILL.md`.
---

# Author a new project skill

Turn a recurring task into a skill: a tight, runnable playbook a fresh agent can follow to do the task *this repo's way*. Capture the convention; do not re-explain general programming.

## 1. Confirm it deserves a skill

A skill earns its place only if the task is **repeated** (it will happen again), **multi-step** (more than a one-liner), and **has a right way** (project conventions, ordering, or gotchas that an unguided agent would get wrong). If it fails any of these — a one-off, or already obvious — don't write one; just do the task. If a near-duplicate skill exists under `.claude/skills/`, extend it instead.

> Broadly-reusable skills (anything not specific to *this* repo) belong in the **specced library** under `src/specced/templates/skills/`, so every project gets them — contribute it back there rather than letting it live only in this repo.

## 2. Scaffold `.claude/skills/<name>/SKILL.md`

- `<name>`: **kebab-case**, verb-or-noun naming the task (`add-feature-flag`, `bump-protobuf`), matching the existing skills.
- Frontmatter: `name: <name>` and a `description:` written as an **auto-trigger** — start with "Use when …" and list the concrete situations/keywords that should fire it, so Claude selects it unprompted. Be specific; this is the only thing the model sees when deciding to load the skill.

## 3. Write the body as runnable steps

Make every step concrete and checkable for *this* repo — not generic advice:

- **Cite, don't restate.** Point to `.claude/rules/<track>/<file>.md` for layer conventions and `CONSTITUTION.md §n` for invariants the task must respect. The rules are the source of truth; the skill routes to them.
- **Use the repo's verification vocabulary.** Express acceptance as the actual `make` targets (`make fmt`, `make lint`, `make test`, `make build`, `make verify`) — not "run the tests". If a command doesn't exist yet, leave a `TODO(specced):` to name it.
- **Hand off to the proof loop** for anything non-trivial: drive it through `repo-task-proof-loop` (`freeze` a spec with runnable `AC1..ACn` → `build` → `evidence` → `verify` fresh → `fix` to `PASS`).
- **Keep it tight and example-driven.** ~40–80 lines. Lead with the hard constraint, show one good/bad example or a small table, prefer a numbered procedure over prose.

Mark every project-specific blank you can't fill with `> TODO(specced): …` so the gap is explicit, not silently wrong.

## 4. Good SKILL.md skeleton

```
---
name: <kebab-case>
description: Use when <trigger situations + keywords> — <one-line of what it does>.
---
# <Imperative title>
<1–2 lines: the goal + the single hard constraint.>
## Before you start    → which .claude/rules/** + CONSTITUTION § to read
## The core rule       → the gotcha/ordering an agent would get wrong (table or good/bad)
## Procedure           → numbered, runnable steps
## Acceptance (runnable)→ exact `make …` commands that prove it
## Proof-loop handoff   → freeze → build → evidence → verify → fix
```

## 5. Verify the skill

A skill is done only when a **fresh agent, given just this SKILL.md and the repo**, can do the task correctly with no extra context. Check: trigger description is specific enough to fire; every step is actionable; acceptance criteria are real commands, not aspirations; no dangling `TODO(specced)` that blocks execution. If a clean-context reader would still have to ask "how?", tighten it.

> TODO(specced): If this project standardizes where skills live or how they're registered/tested, note it here.
