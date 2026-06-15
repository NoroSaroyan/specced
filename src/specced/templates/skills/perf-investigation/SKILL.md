---
name: perf-investigation
description: Use when investigating or improving performance — latency, throughput, memory, a regression or budget miss — anything where "it's slow / heavy / using too much" needs to become a measured win. Any stack (pprof, perf, py-spy, flamegraphs, JMH, Lighthouse, ...).
---

# Investigate and improve performance

Optimize by **measuring, not guessing**. The hotspot is rarely where you assume, and an
"obvious" fix that you can't measure is a coin flip. The loop is: state a number → measure →
find the real hotspot → change one thing → re-measure → guard the gain. Skipping a step turns
this into superstition.

## Before you touch anything

Read the conventions first:

1. `CONSTITUTION.md` — the **verification budget** that applies (e.g. `<op>` p99 < `<N>` ms,
   sustained `<N>` req/s, peak memory < `<N>`). That number is the goal. If none is defined,
   set an explicit target with the requester and propose adding it to the budget.
2. `.claude/rules/**` — where perf-sensitive code lives, the project's allocation/I-O/query
   conventions, and any existing benchmarks or perf gates.
3. The path actually under load — the endpoint, query, job, or render in question.

> TODO(specced): Name this stack's profiler and benchmark harness (e.g. `pprof`/`perf`,
> `py-spy`/`pytest-benchmark`, JMH, `criterion`, Lighthouse/Web Vitals), how to capture a
> flamegraph, the representative workload/dataset to drive it, and the `make` target that runs
> the benchmark suite.

Then **freeze a spec** via the proof loop — the budget is the headline acceptance criterion.

## Procedure

1. **State the goal as a number.** Write the metric, the budget, the workload, and the
   environment (e.g. "p99 of `<op>` < 50 ms under `<N>` concurrent on prod-like data"). No
   number ⇒ nothing to prove. Vague ("make it faster") is not a target.
2. **Measure the baseline first.** Profile or benchmark the current code against a
   **representative** workload — real-shaped data and concurrency, not a toy loop. Record the
   baseline number; you cannot claim a win without it. Never start editing before this.
3. **Find the actual hotspot.** Read the profile/flamegraph and let the data point to where time
   or allocation actually goes. Optimize the top cost, not the code you assumed was slow. Check
   the obvious structural wins first (N+1 queries, missing index, repeated work, no caching,
   accidental O(n²), serialization) before micro-tuning.
4. **One hypothesis, one change.** State *why* it should help, then change a **single** thing.
   Batching multiple "optimizations" makes the re-measurement uninterpretable — you won't know
   what helped or what regressed.
5. **Re-measure to confirm the win is real.** Re-run the same benchmark in the same conditions
   and compare to the baseline. Keep the change only if the improvement is real and beyond run
   noise (compare against variance, not a single sample). No measured win ⇒ revert it.
6. **Guard the gain.** Add a benchmark or perf-regression test that asserts the budget so the
   improvement can't silently rot. Without a guard, the next change quietly gives it back.
   > TODO(specced): Name the perf-test target/CI gate and the threshold it enforces.
7. **Avoid premature/micro optimization; document the trade-off.** Don't trade readability,
   memory, or correctness for speed you don't need. When a change is non-obvious (a cache and
   its invalidation, a precompute, an algorithm swap), record the cost — link `decision-record`
   for notable ones.

> TODO(specced): Replace the generic profiler, workload, and benchmark-target references above
> with this project's actuals from `.claude/rules/**`.

## Acceptance criteria (runnable)

- The metric meets the budget under the representative workload — backed by a re-run benchmark,
  not a claim.  `TODO(specced): make bench` (or the narrower perf target)
- Baseline vs. after numbers are recorded, and the delta exceeds run-to-run noise.
- A perf-regression test/benchmark guards the budget and **fails** if it's breached again.
- Behavior is unchanged: correctness tests, lint/type-check, and build all pass.
  `TODO(specced): make test`, `make lint`, `make build`

> TODO(specced): Replace each criterion with the exact command so these are checkable, not
> aspirational.

## Proof-loop handoff

Drive this through `repo-task-proof-loop`:

1. `freeze` `.agent/tasks/<TASK_ID>/spec.md` with runnable `AC1..ACn`. Make **the budget itself**
   one acceptance criterion ("p99 < `<N>` ms under workload W"), and "a perf-regression guard
   exists and fails when breached" a separate one. Record the baseline number in the spec.
2. `build` the measurement → the single change → the perf guard.
3. `evidence` (baseline vs after, same conditions) → `verify` (fresh) → `fix` until `PASS`. Not
   done until the budget AC and the perf-guard AC are both `PASS`.
