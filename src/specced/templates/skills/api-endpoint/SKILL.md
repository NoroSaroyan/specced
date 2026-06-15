---
name: api-endpoint
description: Use when adding a new HTTP API endpoint/route (or changing an existing one's contract) — design the contract first, then wire it through this project's layers with fail-closed auth, input validation, and a test that proves it. Works for any stack (Go, FastAPI, Express, ...).
---

# Add an HTTP API endpoint

Contract-first, layered, fail-closed. The API contract is the source of truth: design it
first, then implement to match. Evolve additively within a version — never silently break an
existing field, type, or status code (see `CONSTITUTION.md`).

## Before you write

Read, in order:

1. `.claude/rules/<track>/api.md` — this project's API conventions: error shape, pagination,
   idempotency, correlation/request-id, status codes, and naming. Match them exactly.
2. `CONSTITUTION.md` — the auth model, the layering rule, versioning policy, and any
   latency/performance budget that applies to this endpoint.
3. The surface your endpoint joins — find a sibling endpoint and copy its structure rather
   than inventing a new one.

> TODO(specced): Name the contract artifact and its location (e.g. `openapi.yaml`, a `.proto`,
> a route+schema module) and whether it is hand-written or generated. If generated, say which
> `make` target regenerates it. If this project has no separate contract, delete step 1 below
> and treat the route handler's request/response types as the contract.

## Procedure

1. **Design the contract FIRST.** Add the path/route, request and response schemas, the auth
   requirement, and **every** error response (success and each failure mode). Additive only:
   breaking changes go to a new version. Validate the contract before writing code.
2. **Implement through the project's layers, no layer-skipping.** Per `CONSTITUTION.md`, keep
   transport, business logic, and persistence separate.
   > TODO(specced): Replace with this project's actual layers and directories, e.g.
   > `handler → service → store` (Go), `router → service → repository` (FastAPI/Express).
   > The handler decodes/validates and encodes only — no business logic and no direct DB access.
3. **Wire auth fail-closed.** Verify the caller's identity and **check authorization before any
   privileged work**. Any missing/invalid credential → `401`; authenticated-but-not-permitted →
   `403`. No best-effort path, no bypass flag, no "allow on error" branch.
   > TODO(specced): Name the auth mechanism and where it lives (middleware/dependency/guard),
   > and the scope/role check this endpoint requires.
4. **Validate every input** against the contract — body, query/path params, and headers —
   before it reaches business logic. Reject invalid input with the project's standard error
   shape, not a stack trace.
5. **Use the standard error envelope and conventions** from `.claude/rules/<track>/api.md`:
   stable machine-readable error codes, the project's pagination shape for lists, idempotency
   for resource-creating writes, and an echoed request/correlation id.
6. **Respect the latency/perf budget** in `CONSTITUTION.md` (if any): keep heavy I/O, auditing,
   and side effects off the request's critical path.
7. **Add a test that proves it.** Assert the live endpoint matches the contract: success shape
   and status, each error shape and status, and — explicitly — that missing/invalid auth →
   `401` and out-of-scope → `403`.

## Acceptance criteria (runnable)

Express these as independently-checkable criteria, each backed by a command:

- Contract is valid and lints clean.  `TODO(specced): make <contract-lint>`
- The endpoint test passes — success + every error shape/status conform to the contract.
  `TODO(specced): make test` (or the narrower test target for this route)
- Auth fail-closed is proven by a test: missing/invalid → `401`, out-of-scope → `403`.
- Lint/build pass and generated artifacts produce no diff.
  `TODO(specced): make lint`, `make build`, `make gen`

## Proof loop

Drive it to green: write the acceptance criteria as runnable `AC1..ACn`, keeping "contract
designed first and lints", "endpoint conforms to contract", and "auth fails closed (401/403)"
as separate, independently-verifiable criteria; name the latency budget if one applies. Build
contract → layers → test, then run the `make` targets above and fix until every AC passes. Not
done until the contract-conformance and fail-closed-auth criteria are both green.
