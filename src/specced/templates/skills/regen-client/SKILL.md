---
name: regen-client
description: Use when regenerating SDKs / clients / types / stubs / models from a contract or schema (OpenAPI, protobuf, GraphQL, JSON Schema, DB) after the contract changes — keep generated code in sync with its single source of truth, never hand-edited, and prove no drift.
---

# Regenerate generated artifacts from a contract

Generated code is **downstream** of a contract. The contract is the single source of truth: it
is changed **first**, then the generated output follows — never the reverse. Generated files are
**never hand-edited**; they are reproduced by a committed, deterministic command. The same command
runs in CI and must produce zero diff against the committed output (see `CONSTITUTION.md`).

> TODO(specced): Name the contract artifact and its location, the generated output path(s), the
> committed generation command (e.g. a `make gen` / `make generate` target), and the generator
> tool + pinned version. Examples this covers: OpenAPI→client SDKs, `.proto`→stubs, GraphQL→types,
> JSON Schema→models, DB schema→ORM/query types. List the concrete targets your project ships.

## Before you write

Read, in order:

1. `.claude/rules/<track>/codegen.md` (or the nearest generation/contract rule) — this project's
   source-of-truth contract, which directories are generated, the generation command, and any
   layering/boundary rule the generated code must respect. Match it exactly.
2. `CONSTITUTION.md` — the source-of-truth invariant, the versioning/compatibility policy for the
   public surface, and any dependency/license boundary the generated artifacts must stay inside.
3. The contract diff you are regenerating against, and a sibling already-generated artifact —
   copy its structure rather than inventing a new layout.

> TODO(specced): If the contract itself is changing, do that **first** via the contract-owning
> skill (e.g. `api-endpoint`) so the contract is updated and lints **before** any regen work.

## Procedure

1. **Contract first, and it lints.** Confirm the contract already reflects the new shape and
   passes its linter/validator. The artifact is regenerated to match the contract, never the other
   way around. Evolve additively within a major version (`CONSTITUTION.md`).
   > TODO(specced): `make <contract-lint>`
2. **Never hand-edit generated files.** Every change to generated output comes from the contract +
   the committed generator. If you need behavior the generator can't express, put it in the
   hand-written layer that wraps the generated code — not inside the generated files.
3. **Regenerate via the committed command.** Run the project's single generation target so the run
   is deterministic and reproducible (same in CI as locally). Do not invoke a generator by hand
   with ad-hoc flags.
   > TODO(specced): `make gen` (or the per-artifact `generate` target)
4. **Respect the boundary rule.** Generated artifacts may import only what the layering/dependency
   rule allows; if a needed type lives behind a boundary it must not cross, the type belongs on the
   public/shared side of that boundary instead.
   > TODO(specced): Name the boundary check, e.g. `make check-boundary` / `make lint-deps`.
5. **Bump version + changelog iff the public surface changed.** If regeneration adds, removes, or
   changes the public surface, bump the artifact's version per the project's policy and record the
   change. A pure no-op regen needs no bump.
   > TODO(specced): State the versioning policy (e.g. artifact major tracks the contract major) and
   > the changelog location.
6. **Update examples/docs that call the changed surface** so they still compile/run against the new
   types.
7. **Vet any new generator or runtime dependency** with the `sonatype-guide` skill before adding it
   (license/supply-chain risk matters doubly for shipped artifacts — `CONSTITUTION.md`).

## Acceptance criteria (runnable)

Express each as an independently-checkable criterion backed by a command:

- Contract is valid and lints clean.  `TODO(specced): make <contract-lint>`
- **No drift:** re-running generation produces **zero git diff** against the committed output —
  the committed generated code matches the contract. `TODO(specced): make gen && git diff --exit-code`
- Generated artifacts build and their tests pass. `TODO(specced): make build && make test`
- Boundary/dependency rule holds — no generated package crosses a forbidden boundary.
  `TODO(specced): make check-boundary`
- Version + changelog bumped iff the public surface changed (else unchanged).

## Proof loop

Drive it to green: write the acceptance criteria as runnable `AC1..ACn`, keeping "contract updated
first and lints", "regen produces no diff", and "boundary rule holds" as **separate**,
independently-verifiable criteria. Build contract-confirm → regenerate → examples/docs →
version/changelog, then run the `make` targets above and fix until every AC passes. Review the
**contract diff** as the unit of human review; keep the generated output out of manual line review.
Not done until the no-drift AC and the boundary AC are both green.
