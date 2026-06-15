---
name: decision-record
description: Use when making or recording a significant/architectural decision, trade-off, or reversal — anything that shapes architecture, a public contract, security posture, or a choice future contributors would otherwise re-debate. Also use when superseding an earlier decision.
---

# Record an architecture decision

Capture the *why* behind a decision once, so it isn't re-litigated. `CONSTITUTION.md` says "don't re-relitigate decisions already recorded" — this skill is how a decision earns that status. Keep it lightweight: a short ADR is the goal, not a process.

## Is it worth recording?

Record a decision when it would otherwise be re-debated later. Triggers:

- It shapes **architecture** — a boundary, layering, data flow, or a load-bearing dependency/framework choice.
- It changes a **public contract** — API shape, schema, CLI, config, or wire format.
- It affects **security** — an auth model, trust boundary, secret handling, or threat trade-off.
- You **rejected a reasonable alternative**, or you're **reversing a prior decision**.

If it's a local, reversible implementation detail, skip the ADR — a code comment is enough.

## Write the ADR

1. Find the next number: ADRs are numbered, zero-padded, sequential. Create `docs/decisions/NNNN-kebab-title.md` (e.g. `0007-use-postgres-for-the-job-queue.md`).
   > TODO(specced): Confirm this repo's decision-log location and numbering (e.g. `docs/adr/`, `decisions/`, or a single `DECISIONS.md`). If one already exists, follow it and delete this note.
2. Fill the template below. Keep each section to a few sentences — Context is the load-bearing part; state the forces and constraints, not a narrative.
3. New decisions start `Status: proposed`; flip to `accepted` once agreed.

```markdown
# NNNN. <Decision title>

- Status: proposed | accepted | superseded by [NNNN](NNNN-....md)
- Date: YYYY-MM-DD

## Context
The forces at play: the problem, the constraints, and what makes this non-obvious.

## Decision
What we will do, stated in the active voice ("We will ...").

## Consequences
What becomes easier or harder as a result — including the costs we accept.

## Alternatives considered
- **<Option>** — why not chosen.
```

## Wire it into the rules

If the decision establishes or changes a rule, it must be discoverable from where contributors look:

- When it sets a convention, add or update the relevant `.claude/rules/**` file and link back to the ADR (`See docs/decisions/NNNN-...`).
- When it changes an invariant, update `CONSTITUTION.md` and cite the ADR as the rationale. The constitution states the rule; the ADR holds the *why*.

## Superseding a decision

Never delete or silently rewrite an accepted ADR — the history is the value.

1. Write a new ADR for the new decision; in its Context, note what it replaces.
2. In the old ADR, set `Status: superseded by [NNNN](NNNN-...)` and leave the rest intact.
3. Update any `.claude/rules/**` or `CONSTITUTION.md` references to point at the new ADR.

> TODO(specced): If this project records decisions somewhere other than per-file ADRs (an RFC process, an issue label, a wiki), adapt the steps above to that medium and keep the Context/Decision/Consequences/Alternatives spine.
