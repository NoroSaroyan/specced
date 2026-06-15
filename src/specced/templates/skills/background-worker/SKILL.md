---
name: background-worker
description: Use when adding a background job, queue/stream consumer, or scheduled task (Celery, BullMQ, Sidekiq, NATS/Kafka consumer, cron) — anything that processes work off a queue/stream/timer rather than in a request handler.
---

# Add a background worker

A worker pulls work off a queue, stream, or timer, does it idempotently, and signals completion (ack / commit / mark-done). Assume **at-least-once delivery**: every message can arrive more than once and the process can die mid-task. Correctness comes from idempotency, not from hoping each message lands once.

## Before you write

Read the conventions before touching code:

1. `CONSTITUTION.md` — invariants the worker must not violate.
2. `.claude/rules/**` — where worker code lives, how to talk to the broker/scheduler (use the project's abstraction, not a raw client type), config/secrets access, logging and metrics.
3. The data model / migrations for the state this worker reads and writes.

> TODO(specced): Link the exact files — the worker layer/dir, the broker or scheduler used, the delivery semantics (at-least-once vs exactly-once), and any per-job latency or throughput budget. If there is a job/subject/topic catalog, point to it and require new entries be registered there first (no hardcoded topic/queue names).

Then **freeze a spec** via the proof loop.

## Procedure

1. **Place it where workers live; talk to the broker through the project's abstraction.** No raw client type (broker SDK message/record) outside the adapter layer. New queue/topic/schedule ⇒ register it in the canonical place first, never a hardcoded string.
2. **Idempotent handler — safe to run twice.** Key the work on a stable id (message id, dedup key, content hash, or natural key) so reprocessing the same message yields the same final state. Make every persistent write idempotent-by-construction: upsert on a unique key, transaction-wrap so it's all-or-nothing, or recompute as a pure function. No blind `INSERT`/append/increment.
3. **At-least-once + restart-safe.** Assume duplicates and mid-task crashes. Ack/commit/mark-done **only after** the work is durably persisted — never before. Un-acked work redelivers; idempotency (step 2) makes replay harmless.
4. **Explicit retry + backoff.** Transient failure ⇒ retry with a defined backoff (e.g. exponential with jitter) and a max-attempts cap. Permanent failure (bad input, validation, auth) ⇒ do not retry; fail fast to the dead-letter path. Decide which exceptions are transient vs permanent — don't retry everything.
5. **Dead-letter / poison-message handling.** When max-attempts is exhausted or the message is unprocessable, route it to a DLQ / failed-job store / parking topic with the failure reason attached. A poison message must never block the queue or loop forever.
6. **Bounded concurrency + backpressure.** Cap worker pool size and in-flight/prefetch count. Do not unbounded-buffer in memory. Respect the broker's in-flight limit so a slow consumer applies backpressure instead of falling over.
7. **Graceful shutdown.** On SIGTERM/shutdown, stop accepting new work, let in-flight messages finish (or safely re-queue them), and exit within the platform's grace window — no half-done writes left unacked-yet-applied.
8. **Observability.** Emit structured logs with the message/correlation id, and metrics with **bounded cardinality** (no per-user/per-id labels): processed-count by status, processing duration, queue depth/lag, and DLQ count. Register them where the project's metrics live.

> TODO(specced): Replace the generic retry/backoff, DLQ destination, concurrency limits, and metric names above with this project's conventions from `.claude/rules/**`.

## Acceptance criteria (runnable)

- Tests pass, and include: **idempotency** — process the same message twice, assert identical final state (one row, not two; counter moved once); **retry** — transient failure retries then succeeds; **poison** — a permanent failure lands in the DLQ / failed store and is not retried forever.
- An integration test exercises the worker against a real (or test-container) broker, not just a mocked handler.
- Lint/format/type-check pass: no raw broker client type outside the adapter, no hardcoded queue/topic names, ack happens after persistence.
- Build/start succeeds and the worker registers/consumes its queue.

> TODO(specced): Replace with the exact commands (test, lint, build, integration suite).

## Proof-loop handoff

Per `CONSTITUTION.md`, drive this through the proof loop:

1. **freeze** the spec with runnable `AC1..ACn`. Make "idempotent under duplicate delivery", "transient failure retries then succeeds", and "poison message lands in DLQ and stops" three separate, independently-verifiable criteria.
2. **build** registration/config → idempotent handler → retry/DLQ → metrics → tests.
3. **evidence** → **verify** (fresh) → **fix** until `PASS`. Not done until the idempotency AC and the DLQ AC are both `PASS`.
