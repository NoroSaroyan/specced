---
name: dependency-upgrade
description: Use when upgrading dependencies, bumping versions, or applying a security patch — to a direct or transitive package, a toolchain, or a base image. Covers scoping the bump, reading breaking-change notes first, incremental upgrades, lockfile commit, full verify, deprecations, and a vulnerability audit. Any ecosystem (pip/uv, npm, go mod, cargo, bundler, maven).
---

# Upgrade a dependency

Move a dependency forward **deliberately**, not opportunistically. The hard constraint: a bump may change behavior, so every upgrade ships with the lockfile that pins it, a clean `verify`, and an audit that is no worse than before. Never bump blind.

## Before you bump

Read `.claude/rules/<track>/dependencies.md` (where deps are declared, the lockfile, the version-pinning policy, allowed registries) and `CONSTITUTION.md` (supply-chain invariants — provenance/allowlist, license policy, who may add a new dependency). Then **scope it**:

- **Why** — security patch, a feature/fix you need, or routine hygiene. Security and "needed fix" justify themselves; pure hygiene is lower priority and bundled, not heroic.
- **Which** — name the exact packages and target versions. Do not let an unrelated transitive upgrade ride along unexamined.

> TODO(specced): Name this repo's manifest + lockfile, the pin policy, the registry/provenance allowlist, and who may approve a *new* (vs. upgraded) dependency — in `.claude/rules/<track>/dependencies.md`.

## Read the changelog first (non-negotiable)

Before changing a single version constraint, read the target's release notes / `CHANGELOG` / migration guide for **every** version you cross, not just the latest. Note breaking changes, removed APIs, new minimums (language/runtime/peer deps), and required config changes. If you cannot find breaking-change notes for a major bump, treat that as a risk to surface in the spec — not a reason to skip reading.

## Prefer incremental over big-bang

- Bump **one logical group at a time** (a package and its peers), verify, commit; then the next. A failing `verify` then names the culprit instead of a 40-package haystack.
- For a multi-major jump, step through majors in order (N→N+1→N+2) when each has its own migration; do not leap N→N+3 and debug blind.
- Pin to an **exact** resolved version (via the lockfile); avoid widening a constraint to a floating range as a shortcut.

## Procedure

1. Update the version constraint in the manifest for the scoped package(s) only.
2. Re-resolve and **update the lockfile**; review the lockfile diff — unexpected transitive churn is a signal, investigate it.
3. Apply required code/config migrations from the changelog (renamed APIs, moved imports, new required options).
4. **Resolve deprecations** the bump surfaces now — do not leave new deprecation warnings for later; they are the next breaking change.
5. Run a **vulnerability/audit scan**; the result must be no worse than before the bump (ideally the reason for it). Do not introduce a new advisory to gain a feature.
6. **Commit the lockfile** together with the manifest in the same change — a manifest bump without its lockfile is a broken, non-reproducible build.
7. Record the rationale and note user-facing impact (see below).

> TODO(specced): Give the exact commands for this ecosystem — add/upgrade (e.g. `uv lock --upgrade-package <p>`, `npm update <p>`, `go get -u <p>`, `cargo update -p <p>`), re-lock, and audit (e.g. `uv pip audit`, `npm audit`, `govulncheck`, `cargo audit`).

## Record it

- For a **notable** upgrade — a load-bearing framework, a major version, or a security-driven swap — capture the *why* via `decision-record` so it isn't re-debated.
- For any **user-facing** change (behavior, config, minimum runtime, removed option), add a `CHANGELOG`/release-notes entry. A silent breaking bump is a regression with no paper trail.

## Acceptance criteria (runnable)

Express these as the AC block in the frozen spec; each must run and pass:

- Manifest **and** lockfile are both updated and committed; the lockfile resolves cleanly with no drift.
- Full `verify` passes (build, lint, type-check, tests) on the upgraded tree.
- The audit/vulnerability scan reports **no new** advisories vs. baseline (and closes the targeted one, if security-driven).
- No new deprecation warnings introduced by the bump remain unresolved.

> TODO(specced): Replace each criterion with the exact command (e.g. `make verify`, `make lock-check`, `make audit`) so these are checkable, not aspirational.

## Proof-loop handoff

Drive this through `repo-task-proof-loop`:

1. `freeze` `.agent/tasks/<TASK_ID>/spec.md` with the AC block as runnable `AC1..ACn`; state the scope (which packages, target versions, and why), and make "lockfile committed", "`verify` green", and "audit no-worse" separate criteria.
2. `build` the bump — manifest + lockfile + any migration + changelog/ADR.
3. `evidence` → `verify` (fresh) → `fix` until every AC is `PASS`.
