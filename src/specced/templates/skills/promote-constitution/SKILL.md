---
name: promote-constitution
description: Use when periodically auditing CONSTITUTION.md — to promote aspirational "direction" invariants that are now enforced-in-practice to "enforced today", demote ones the code no longer honors, or reconcile the constitution with what the gate actually checks. Triggers like "review our constitution", "is this still just aspirational", or constitution drift.
---

# Promote constitution invariants

specced's `CONSTITUTION.md` separates **enforced today** (the gate or a rule actually
checks it) from **direction** (where the project is heading, not yet enforced). Over time
direction quietly becomes reality but nothing moves it, and enforced-today claims quietly
rot. This skill keeps the constitution honest, so agents can trust it as ground truth.

## When to use

- On a cadence (release, quarterly), or when a direction item now has a check/rule behind it.
- When the constitution claims an invariant the code visibly violates.

## Method

1. **List the direction items** in `CONSTITUTION.md` (the aspirational / "where we're
   going" section).
2. **Test each for real enforcement.** It is enforced-in-practice only if a *mechanism*
   exists: a `make` gate or `.specced/checks.json` entry covers it; a `.claude/rules/**`
   rule encodes it (and `specced stats` shows that rule actually cited); or the code
   uniformly follows it (spot-check — don't assume).
3. **Promote** the ones that pass to *enforced today* — but only with a mechanism
   attached. A promotion without a check is just a louder claim: if none exists, add the
   rule/check (or mark `TODO(specced)` naming the missing one) before promoting.
4. **Reconcile enforced-today items** the code violates: fix the code via the proof loop,
   or — if the invariant itself was wrong — move it back to direction with a one-line why.
5. **Record the significant moves** (especially reversals) as an ADR via
   `decision-record`, and cross-link the affected rule or clause.
6. **Re-verify:** `make verify` and `specced doctor` should be green, and `doctor` should
   report no unfilled `TODO(specced)` left by the promotion.

## Guardrails

- Never promote without an enforcement mechanism — enforced-today is a promise the gate
  must keep.
- Keep the constitution **small**: promote and consolidate, don't accrete. A constitution
  nobody can hold in their head isn't enforced.
- Demoting is not failure — an honest "direction" beats a false "enforced".

> A good audit leaves every enforced-today clause backed by a check or a cited rule, and
> every direction item genuinely still aspirational.
