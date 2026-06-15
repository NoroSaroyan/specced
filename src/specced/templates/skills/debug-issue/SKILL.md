---
name: debug-issue
description: Use when investigating a bug, test failure, crash, or unexpected behavior — drive it to a reliable minimal reproduction, isolate the cause by evidence (not guessing), fix the root cause, and lock it with a regression test that failed before and passes after. Any stack.
---

# Debug an issue

Find the **root cause** by evidence, then prove the fix with a regression test. Discipline over speed: a guessed "fix" with no failing test that turns green is not a fix — it's a coincidence. Don't change production behavior until you can reproduce the failure on demand.

## Before you touch code

Read the conventions first:

1. `CONSTITUTION.md` — invariants the system must hold; the bug is a violation of one of them, and the fix must not violate another.
2. `.claude/rules/**` — where this code lives, how tests/logs/observability work, and the error-handling conventions you must restore (not invent around).

> TODO(specced): Link this project's debugging tools — the debugger/REPL invocation, where logs/traces/metrics live and how to read them, the test command and how to run a single test, and any feature-flag or env switch for verbose output. Point at the relevant `.claude/rules/**`.

Then **freeze a spec** via the proof loop, where the bug report *is* the spec: expected vs actual, plus the regression test as the acceptance criterion.

## Procedure

1. **Reproduce, reliably and minimally.** Get a deterministic repro before anything else. Pin the inputs, version/commit, and environment. Then **shrink** it — strip unrelated steps, data, and config until the smallest thing that still fails remains. A flaky or "sometimes" repro is not yet understood; chase the source of the nondeterminism (timing, ordering, shared state, uninitialized data) first. No repro ⇒ no fix.
2. **State expected vs actual precisely.** Write the exact observed behavior (error text, wrong value, status, side effect) and the exact correct behavior. Vague ("it's broken") blocks diagnosis; specific ("returns `0` for input `X`, should return `42`") points at the cause.
3. **Isolate by evidence, not by guessing.** Form **one** hypothesis at a time, predict what you'd observe if it were true, then gather evidence to confirm or kill it — read the failing logs/trace, add temporary instrumentation, inspect state in the debugger, or binary-search the input/code path. Use `git bisect` to pin the introducing commit when the bug is a regression. Each step must rule something *out*. No shotgun edits, no "try this and see."
   > TODO(specced): Replace with this project's debugger/REPL command, the exact log/trace locations, and how to run `git bisect` against the test suite (e.g. `git bisect run make test`).
4. **Find the root cause, not the symptom.** Trace back to *why* the wrong state arose — the originating defect, not the place it surfaced. Reject symptom-masking fixes: clamping the output, swallowing the exception, adding a retry, or special-casing the one failing input. If you can't explain the full chain from cause to symptom, you haven't found it yet.
5. **Write a regression test that FAILS first.** Encode the minimal repro as a test asserting the *expected* behavior. **Run it and watch it fail** for the right reason (it must catch this bug, not pass vacuously) — a test that was never red proves nothing.
6. **Fix the root cause, then watch the test go green.** Make the smallest change that addresses the cause and re-run the regression test until it passes. Restore the project's conventions (step 0) rather than working around them.
7. **Confirm nothing else regressed.** Run the broader suite, lint/type-check, and build. A fix that breaks a neighbor is not done.

## Acceptance criteria (runnable)

- The regression test **fails on the pre-fix code and passes after** — captured as evidence (red → green). `TODO(specced): make test` (or the single-test target)
- The minimal repro from step 1 no longer reproduces the failure.
- The full suite, lint/type-check, and build all pass — no new failures introduced. `TODO(specced): make test`, `make lint`, `make build`
- The fix addresses the root cause (the explained cause→symptom chain), not the symptom; if it's a regression, the introducing commit is identified.

> TODO(specced): Replace each command above with this project's exact targets.

## Proof-loop handoff

Per `CONSTITUTION.md`, drive this through `repo-task-proof-loop`:

1. **freeze** `.agent/tasks/<TASK_ID>/spec.md` with the bug as runnable `AC1..ACn`: make "minimal repro is deterministic", "regression test red before the fix", and "regression test green after, full suite still green" three separate, independently-verifiable criteria. Record expected-vs-actual verbatim.
2. **build** the failing regression test first, then the root-cause fix.
3. **evidence** (the red-before / green-after run, the bisect result if any) → **verify** (fresh) → **fix** until `PASS`. The regression test is the acceptance criterion: not done until it was red, is now green, and nothing else regressed.
