---
name: refactor
description: Use when restructuring or cleaning up code WITHOUT changing its behavior — renaming, extracting, inlining, moving, deduplicating, or splitting modules. Not for behavior changes, features, or bug fixes (do those separately). Any stack.
---

# Refactor (behavior-preserving)

Change the *shape* of the code, never its *behavior*. The single invariant: every observable output, side effect, and public contract is identical before and after. If a change alters behavior, it is not a refactor — it is a separate change and must be split out.

## Before you touch code

Read `.claude/rules/**` and `CONSTITUTION.md` for the boundaries, layering, and patterns the result must still honor — a refactor moves code *toward* these, never away. Refactoring is not a license to cross a boundary or invent a new pattern.

> TODO(specced): Link this stack's structural conventions (module/package layout, naming, allowed dependency directions) so "well-shaped" is concrete, not taste.

## Pin behavior first

You cannot preserve what you cannot observe. **Before** editing, confirm the code under change is covered by tests that would fail if behavior drifted.

1. Run `make test` to confirm a green baseline. Never start from red — if it's red, stop and fix or report that first.
2. Assess coverage of the target code. If it is thin, write **characterization tests** that capture *current* behavior exactly (including quirks and known-wrong outputs — assert what it *does*, not what it *should*). These are scaffolding that locks the behavior in place.
3. Re-run `make test`; the new tests pass against the unchanged code.

> TODO(specced): Name the test runner / coverage tool and the command to scope tests to changed files, so this is checkable per step.

## Refactor in small, reversible steps

- **One transformation at a time** — rename, extract, inline, move, dedupe. Each step is mechanical and individually revertable.
- **Run `make test` after every step.** Green → keep going. Red → revert that single step (not the whole session) and retry smaller. Never stack a second change on a red baseline.
- **No behavior, features, or fixes mixed in.** If you spot a bug, leave a `> TODO(specced):` note and fix it in a separate change against its own spec — do not "improve" it inside the refactor. A diff that changes both shape and behavior is unreviewable.
- **Keep the public surface stable.** Exported APIs, schemas, CLI flags, wire formats, and config keys stay identical. If a rename must reach the public surface, call it out explicitly in the spec and treat it as a contract change — not an incidental edit.

## If the refactor changes an established pattern

A refactor that replaces a load-bearing pattern (a boundary, a layering rule, a dependency choice) is a decision, not a cleanup. Record it via the `decision-record` skill and update the relevant `.claude/rules/**` so the new shape is the documented one — otherwise the next contributor reverts you.

## Acceptance criteria (runnable)

- `make test` is green at the start (baseline) and after **every** step.
- Behavior is unchanged: the characterization/existing tests pass identically before and after; no test assertions were weakened or deleted to make them pass.
- The public surface is byte-stable, or each change to it is named in the spec as a contract change.
- `make verify` (build, lint, full tests) is green on the final diff.
- The diff contains structural changes only — no behavior, feature, or bugfix edits.

> TODO(specced): Replace `make test` / `make verify` with this repo's exact commands and add any structure check (e.g. `make lint`, an import-boundary/architecture check) that proves the patterns held.

## Proof-loop handoff

Drive this through `repo-task-proof-loop`:

1. `freeze` a spec whose acceptance criterion is **behavior unchanged** — `AC1..ACn` as the runnable checks above, with "characterization tests added/confirmed" and "`make verify` green" as explicit criteria.
2. `build` the refactor in small steps, re-running `make test` between each.
3. `evidence` → `verify` (fresh) → `fix` until every AC is `PASS` — the behavior-unchanged and public-surface-stable criteria especially.
