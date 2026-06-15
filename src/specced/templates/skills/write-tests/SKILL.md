---
name: write-tests
description: Use when adding tests to existing or untested code / raising coverage on a module / locking in current behavior before a refactor. Covers the discipline of testing the contract (not internals), picking the right level, covering happy path + edges + failure modes, and keeping tests deterministic and fast.
---

# Write tests for existing code

Add tests that pin the **observable contract** of code that already runs — so a future change that breaks behavior fails loudly. A test suite is a safety net, not a mirror of the implementation: assert what callers depend on, not how the code happens to do it.

## Before you write a test

Read, in order:
1. The code under test and its callers — what is the public surface, what do callers actually rely on, what are the inputs/outputs and side effects?
2. `.claude/rules/**` and `CONSTITUTION.md` for this repo's testing conventions, structure, and any invariants the tests must protect.
3. An existing test in this repo — mirror its layout, naming, fixture style, and assertion idioms rather than inventing new ones.

> TODO(specced): Name this stack's test runner, the test file location/naming convention, and where shared fixtures/helpers live.

Then **freeze a spec** via the proof loop before writing tests (see "Proof-loop handoff").

## Decide what to test

- **Lock the contract, not the implementation.** Assert return values, emitted events, persisted state, and error behavior — the things a caller observes. Do not assert private fields, call order, or internal helpers; those are free to change.
- **Pick the right level.** Prefer fast unit tests for pure logic and branching. Use an integration test only where the behavior *is* the integration (DB query, route handler, adapter wiring). Don't spin up the world to test a pure function; don't unit-test past a boundary you can't fake honestly.
- **Characterize first if behavior is unclear.** For legacy code, write a test that captures *current* output, confirm it passes, then treat that as the baseline to lock in.

> TODO(specced): Point at this repo's unit-vs-integration split and any test-tier rules in `.claude/rules/**`.

## Cover the real surface

For each unit of behavior, cover:
1. **Happy path** — the expected input → expected output.
2. **Edge cases** — empty/zero/one, boundaries, large input, unicode, ordering, duplicates, optional fields absent.
3. **Failure modes** — invalid input, missing dependency, downstream error → assert the *specified* error/exception/status, not just "it throws".
4. **Idempotency / state** where relevant — running twice doesn't double-apply; cleanup happens.

Use a table/parametrized form for many input variants instead of copy-pasted cases.

## Keep tests trustworthy

- **Deterministic.** No reliance on wall-clock, timezone, random seeds, map/dict iteration order, or test execution order. Inject or freeze time and randomness.
- **Fast and isolated.** Each test sets up and tears down its own state; no shared mutable globals; tests pass in any order and in parallel.
- **No live network.** Hit a fake, an in-process server, or a **recorded** fixture (cassette/golden file checked into the repo). Never call a real third party from the suite.
- **No flakiness.** No `sleep`-to-hope; wait on a condition. No assertions on nondeterministic strings. A test that's flaky is worse than no test — fix or delete it.
- **Readable.** Arrange-Act-Assert; one behavior per test; a name that states the behavior so a failure is self-explaining.

> TODO(specced): Specify this stack's fake/mock + time-freeze + recorded-fixture mechanisms and where recordings/golden files live.

## Run them

Tests run through this repo's verification vocabulary, not an ad-hoc invocation:

```bash
make test
```

Run the whole suite (not just the new file) to confirm you broke nothing. Treat coverage as a **guide**: use it to find untested branches, not as a target to game — a high number with weak assertions proves nothing.

> TODO(specced): Replace with the exact command if this repo scopes a single file/module, and name the coverage tool/threshold if one is enforced.

## Acceptance criteria (runnable)

Express these as the AC block in the frozen spec; each must run and pass:

- New tests exist for the targeted behavior and **fail** if the relevant logic is reverted (they actually pin the contract).
- `make test` passes locally and is green on a clean checkout.
- Tests are deterministic: the suite passes on repeated and parallel runs with no network access.
- `make lint` / `make build` still pass (tests don't break the gate).

> TODO(specced): Replace the above with the exact commands and any coverage check for this repo.

## Proof-loop handoff

Your tests *become* the acceptance criteria the verifier reruns. Drive this through the repo's proof loop:

1. `freeze` a spec with the AC block above as runnable `AC1..ACn`, naming the exact behaviors/contracts each test locks in.
2. `build` the tests against the spec.
3. `evidence` → `verify` (fresh) → `fix` until every AC is `PASS` — the fresh verifier reruns `make test` against current code, so a regression is caught, not narrated.
