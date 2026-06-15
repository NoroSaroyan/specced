---
name: security-review
description: Use when security-reviewing a change or component — auth, input handling, secrets, dependencies, data exposure. A focused defensive pass over the developer's own code; complements the generic code-review skill with an attacker's-eye lens. Any stack.
---

# Security review

A focused, **defensive** security pass over a change. This is the attacker's-eye complement to
`code-review`: that skill checks correctness against every dimension; this one maps the change's
attack surface and hunts for exploitable weakness. Scope is the diff and the component it touches —
not a whole-repo audit, and not offensive tooling.

## Method

1. **Map the trust boundary.** For the change under review, name where untrusted input crosses into
   trusted code: request handlers, deserializers, file/URL/SQL builders, auth checks, IPC, and any
   data sourced from users, other services, or storage. Everything downstream of a boundary is
   attack surface.
2. **Walk each boundary against the checklist below**, deciding severity with the rubric and citing
   the source — the security clause in `CONSTITUTION.md` and the relevant `.claude/rules/**`.
3. **Report only confident, real findings.** No "consider hardening" noise; a finding must name a
   concrete weakness an attacker could reach.

## Severity rubric

- **Critical** — directly exploitable: auth bypass / privilege escalation, injection (RCE/SQLi), a
  live secret in code or logs, or unauthenticated access to sensitive data. Blocks merge.
- **High** — exploitable with a precondition, or sensitive-data exposure without full bypass (e.g.
  SSRF, path traversal, missing authorization on one path, weak crypto on secrets).
- **Medium** — hardening gap that raises real risk but isn't directly exploitable here (e.g. a
  known-vuln dependency not yet on a reachable path, missing rate limit on an auth endpoint).

## Checklist

- **Authentication & authorization — fail closed.** Identity is verified before any privileged work;
  authorization is checked per request against the acting principal (no IDOR, no client-supplied role
  trusted). No bypass flag, no "allow on error" / default-allow branch — missing/invalid credential
  denies. Watch for privilege escalation: a lower-privileged caller reaching a higher-privileged path.
- **Input validation & injection.** Every value crossing a boundary is validated/encoded for its
  sink: parameterized queries (no string-built SQL), no shell/`eval`/template execution on user input
  (SQLi / command / template injection), output encoded for its context (XSS), and no mass-assignment
  of unvetted fields.
- **Secrets handling.** No secret, token, key, or credential in code, config, fixtures, or logs —
  from env or a secret store only. Errors and debug output must not echo secrets, tokens, or full
  request bodies. Check the diff *and* what it logs.
- **Sensitive-data exposure & access control.** Responses, logs, and errors expose only what the
  caller is entitled to — no over-broad serialization, no PII/secrets in error messages, no missing
  ownership/tenant scoping on reads. Verbose stack traces stay off the wire.
- **SSRF / path traversal / unsafe deserialization.** User-influenced URLs are allowlisted (no
  fetch to arbitrary/internal hosts or metadata endpoints); file paths are canonicalized and confined
  to an allowed root (no `../`); untrusted bytes are never deserialized into live objects via an
  unsafe deserializer.
- **Crypto misuse.** Use vetted libraries, not hand-rolled crypto: a strong algorithm/mode, a CSPRNG
  for tokens/IDs, password hashing with a slow KDF (not a raw hash), constant-time comparison for
  secrets/signatures, and no hardcoded keys/IVs.
- **Dependency & supply-chain.** New or bumped dependencies are from a trusted source, pinned, and
  free of known advisories; the lockfile changes match the manifest (no unexpected transitive jumps).

> TODO(specced): Name this project's security tooling and the command for each — SAST/linter, secret
> scanner, dependency/advisory audit, and any IaC/container scan — so findings can be backed by a run,
> not just inspection. Reference the exact security clause/section in `CONSTITUTION.md` and the
> security-relevant files under `.claude/rules/**`.

## Output

Group by severity, highest first. One line per finding, with a concrete fix and the cited source:

```
[CRITICAL] path/to/file.ext:42 — <reachable weakness> → <concrete fix>  (CONSTITUTION §security)
```

End with a one-line verdict: **block** (any Critical/High), **approve with hardening** (Medium only),
or **approve** (clean). If reviewing a proof-loop task, write findings the fixer can act on and stop
short of editing code yourself.

## Proof-loop handoff

Every accepted finding becomes a regression guarantee, not just a patch:

1. `freeze` (or amend) `.agent/tasks/<TASK_ID>/spec.md` so each fix has a runnable acceptance
   criterion `AC1..ACn` — e.g. "missing/invalid auth → denied", "malicious input is rejected/escaped",
   "no secret in code or logs (secret-scan clean)", "known-vuln dependency resolved (audit clean)".
2. `build` the fix plus a **regression test that fails on the vulnerable code and passes on the fix**.
3. `evidence` → `verify` (fresh) → `fix` until every AC is `PASS` — especially the fail-closed-auth
   and injection criteria. A fix without a guarding test or a green scan is not done.
