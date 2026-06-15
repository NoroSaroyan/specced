---
name: add-integration
description: Use when integrating an external service / API / connector / webhook — a payment or SaaS API, an OAuth provider, an inbound webhook, or an outbound data source. Covers the discipline of a narrow adapter, secret handling, idempotency, timeouts/retries, signature verification, and an integration test.
---

# Add an external integration

Wrap a third-party system behind a narrow, owned interface — never let its SDK, error shapes, or auth leak into the rest of the codebase. An integration is a trust and failure boundary: treat auth, idempotency, and inbound-signature verification as the load-bearing parts.

## Before you write code

Read, in order:
1. The provider's API docs for the exact endpoints, auth flow, rate limits, error codes, and (if inbound) the webhook signature scheme.
2. `.claude/rules/**` and `CONSTITUTION.md` for this repo's boundaries, secret-handling rules, and error conventions.
3. Any existing adapter in this repo — mirror its file layout and patterns rather than inventing new ones.

> TODO(specced): Link the canonical integration/adapter pattern doc and the place new integrations live (directory, module, package boundary) for this stack.

Then **freeze a spec** via the proof loop before implementing (see "Proof-loop handoff").

## Design the boundary

- **Narrow interface first.** Define the smallest interface your app needs (the operations you actually call), then implement it as an adapter over the provider. App code depends on your interface, not the vendor SDK. Map provider errors to your own error type/codes; do not re-throw raw SDK errors.
- **Secrets via env / secret store only.** Read keys, tokens, and signing secrets from the environment or a secret manager. Never inline a secret, commit one, or log one. Fail to start (loud) if a required secret is missing.
- **Config is structural.** Validate config shape (URLs, required fields) without doing I/O; do network work only in an explicit `start`/`connect` step.

> TODO(specced): Name this repo's secret source (env var convention, vault, etc.) and the config-validation pattern.

## Procedure

1. **Define the interface + adapter.** Create the interface and a concrete adapter; register/wire it the way this repo wires dependencies. Keep all provider-specific types inside the adapter.
2. **Auth, fail closed.** Resolve credentials from the secret store. On any auth failure (missing/expired/invalid token, refused refresh) **deny the operation** — never fall through to an unauthenticated or default-allow path.
3. **Timeouts + retries with backoff.** Every outbound call gets an explicit timeout. Retry only idempotent/safe operations, with exponential backoff + jitter and a bounded attempt count; respect `Retry-After`. Do not retry blindly on 4xx.
4. **Idempotency keys.** For any state-changing outbound call (payments, creates), send a stable idempotency key derived from the business operation so a retry is a no-op, not a duplicate. Persist the key/result if the provider doesn't dedupe for you.
5. **Inbound webhooks: verify, then act.** Verify the signature (constant-time HMAC compare against the shared signing secret) **before** parsing or trusting the body; reject on mismatch or stale timestamp. Make handling idempotent on the provider's event ID (you will receive duplicates). Return 2xx fast; do real work async if needed.
6. **Rate limits + partial failure.** Honor the provider's rate limits (client-side limiter or backoff on 429). On batch/multi-item calls, handle partial success explicitly — record what succeeded, surface/queue what failed; never silently drop items.
7. **Observability.** Log requests/outcomes with correlation IDs and redacted secrets; surface failures as typed errors the caller can branch on.

> TODO(specced): Add stack-specific steps here (HTTP client / retry lib, webhook framework hook, queue for async handling).

## Integration test (required)

Record at least one integration test that exercises the real wire format — not just a hand-rolled mock:

- Run against the provider's **sandbox** environment, or against **recorded fixtures** (captured request/response, e.g. a cassette/VCR-style recording) checked into the repo.
- Cover: a happy-path call, an auth failure (asserting fail-closed), a retry/timeout path, and — for inbound — a **valid signature accepted + an invalid signature rejected**, plus a duplicate event handled once.

> TODO(specced): Specify the fixture/sandbox mechanism and where recordings live for this stack.

## Acceptance criteria (runnable)

Express these as the AC block in the frozen spec; each must run and pass:

- Build/compile and lint pass.
- Unit tests pass: config validation, provider-error mapping, and idempotency-key derivation.
- Integration test passes: happy path, fail-closed auth, retry/backoff, and (if inbound) signature accept/reject + duplicate-event dedupe.
- A grep/secret-scan confirms no secret is inlined or logged.

> TODO(specced): Replace the above with the exact commands for this repo (build, lint, test, secret-scan).

## Proof-loop handoff

Drive this through the repo's proof loop:

1. `freeze` a spec with the AC block above as runnable `AC1..ACn`, naming the exact interface methods and the signature-verification + idempotency criteria as explicit sub-criteria.
2. `build` against the spec.
3. `evidence` → `verify` (fresh) → `fix` until every AC is `PASS` — especially the fail-closed-auth and signature-reject criteria.
