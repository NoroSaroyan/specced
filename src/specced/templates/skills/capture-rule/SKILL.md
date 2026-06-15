---
name: capture-rule
description: Use when the user corrects you, rejects an approach, or states a preference worth keeping ("we don't do it that way", "always X here", "never Y"). Persists the lesson as a rule, constitution clause, or ADR so it is not repeated by you or the next agent.
---

# capture-rule

A correction you only hear once gets lost at the next context compaction — and the
next agent repeats the mistake. This skill turns a correction into durable guidance.

## When to use

Trigger on a *durable* correction or preference, not a one-off:

- "We don't do it that way here." / "Always …" / "Never …"
- A rejected PR/approach with a reason that will apply again.
- A convention the user states in passing that isn't written down.

Skip it for one-off, task-specific instructions (those belong in the task spec).

## Where it belongs

Pick the narrowest correct home:

- **A layer convention** → edit the matching `.claude/rules/<track>/*.md` (create one
  from `_template.md` if none fits). Most corrections land here.
- **A global, rarely-changing invariant** → add/adjust a clause in `CONSTITUTION.md`.
- **A significant decision or trade-off** (especially a reversal) → record an ADR via
  the `decision-record` skill, and link it from the affected rule.
- **A recurring multi-step task done a specific way** → capture it with `new-domain-skill`.

## How to capture it

1. Restate the correction as a **one-line, imperative, checkable** rule (how a
   reviewer would verify it), plus a one-line *why* if it isn't obvious.
2. Add a short good/bad example drawn from the actual change that prompted it.
3. Write it into the chosen home. If it sharpens an existing rule, edit that rule in
   place rather than adding a near-duplicate.
4. If it updates an empty stub, remove the `> TODO(specced):` marker (it's now real).
5. Confirm back to the user in one line: what you captured and where.

## Guardrails

- Capture the *principle*, not the single instance — make it general enough to apply
  next time, specific enough to check.
- Don't bloat: prefer editing an existing rule over creating a new file.
- One correction → one home. Cross-link instead of duplicating.

> A good capture means a fresh agent, reading only `.claude/rules/**` and
> `CONSTITUTION.md`, would not make the mistake you were just corrected for.
