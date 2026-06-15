---
name: db-migration
description: Use when adding or changing a database schema / writing a migration — a table, column, index, or constraint — under the backward-compatible two-phase (expand → migrate → contract) rule, with a reversible migration tested against the previous release's schema. Any tool (Alembic, golang-migrate, Prisma, Rails, Flyway, …).
---

# Write a database migration

Author a schema migration that is **backward compatible** and **reversible**. The hard constraint: a rolling deploy must let release N and N+1 run against the same schema, so a migration must never break the still-running previous code, and must never lose data.

## Before you write

Read `.claude/rules/<track>/data-and-migrations.md` (the tool, file location/naming, schema and index conventions for the table you touch) and `CONSTITUTION.md` (data-safety invariants — zero-data-loss, the compatibility window, safety-critical tables). Then **freeze a spec** via the proof loop.

> TODO(specced): Name the migration tool, the migrations directory, the naming/sequence scheme, how forward+rollback are run, the schema/type/index conventions, and any backfill pattern (batched, re-runnable) — in `.claude/rules/<track>/data-and-migrations.md`.

## The two-phase rule (the core constraint)

Add → use → drop, spread across releases. In **one** release/PR ship only the additive, reversible half:

| Change | Same release as the consuming code? |
|---|---|
| Add nullable column / column with default | Yes |
| Add table / add non-unique index | Yes |
| Make a column NOT NULL | **No** — backfill first, enforce later |
| Drop a column / table | **No** — stop using first, drop later |
| Rename a column | **No** — add new + dual-write, drop old later |
| Change a column type | **No** — add new-typed column, migrate, drop old |

Never ship a destructive or tightening change in the same release that introduces the code depending on it. If a task seems to require it, split it into expand / migrate-backfill / contract phases and surface the sequencing in the spec — do not violate the rule.

## Reversibility, data safety, locking

- Every migration has a working `down`/rollback that restores the prior schema. If a step is genuinely irreversible, say so in the spec and justify it — never the silent default.
- No `up` that destroys data a rollback cannot recover; data-moving steps must be reversible or staged across phases. Keep safety-critical tables additive — stranding or emptying them mid-rollout is an outage/data-loss risk.
- Schema changes can take blocking locks and stall live traffic. Prefer the non-blocking variant your engine offers (concurrent/online index builds, no-rewrite column adds, batched backfills). Do not ship a lock-heavy op on a large table without a stated plan.

> TODO(specced): Record the engine's online-DDL escape hatches and the row-count threshold above which a migration needs an explicit locking plan.

## Procedure

1. Create the migration with the next id/name per the repo's scheme.
2. Write only the additive/reversible half consistent with the two-phase table; state which phase this PR is.
3. Add/adjust indexes and constraints per repo conventions, each justified by a query or invariant — no speculative indexes.
4. Write the `down`/rollback so it cleanly reverses `up`.
5. Regenerate any derived artifacts (ORM models, typed query code, schema snapshots) and commit them.

## Acceptance criteria (runnable)

- Apply **up then down** cleanly with no errors (forward + backward test).
- Apply the new migration **on top of the previous release's schema**, then run the current code's checks against it — proves backward compatibility. A failure here means a non-additive change; split it.
- The schema after `up` matches the documented conventions for the affected table (names, types, constraints, indexes).
- Generated/derived artifacts produce **no diff**; build and tests pass.

> TODO(specced): Replace each criterion with the exact command (e.g. `make migrate-up && make migrate-down`, `make test-migrations`, `make gen`, `make test`) so these are checkable, not aspirational.

## Proof-loop handoff

Drive this through `repo-task-proof-loop`:

1. `freeze` `.agent/tasks/<TASK_ID>/spec.md` with the AC block as runnable `AC1..ACn`; make "up+down clean" and "applies on the previous-release schema" separate criteria, and state which two-phase phase this PR is.
2. `build` the migration + derived artifacts.
3. `evidence` → `verify` (fresh) → `fix` until `PASS`.
