# Proposal: CI gate + signal convention

Status: **accepted, v1 implemented** (the `specced ci` command, deps-based MCP
suggestion, and the review/rule trailers). Authored 2026-06-17.

## Context

specced installs a verification gate (`.specced/checks.json`, `make verify` /
`verify-full`) but it only ran **locally** — it left no trace and could be ignored.
Separately, the "self-improving loop" (see [the roadmap](#what-this-unlocks)) needs a
**machine-readable signal** to answer "which rules and review dimensions actually get
used, and is the gate passing?" Nothing emitted that yet.

This proposal is the day-2 *foundation*: give the gate external teeth, and start
emitting the signal the loop will later mine — while touching only specced-owned code.

### Engine boundary (hard constraint)

`templates/skills/repo-task-proof-loop/` is vendored (Apache-2.0, do-not-edit). Its
verifier prompt lives inside that tree, so it is off-limits. Everything here touches
only `scaffold.py`, `detect.py`, `cli.py`, and the **specced-owned** skills
`code-review` and `capture-rule`. The engine's artifacts are *read*, never edited.

## Part A — `specced ci`: external gate

A new subcommand emits a dedicated, fully specced-owned workflow,
`.github/workflows/specced-gate.yml`. It does **not** inject into the repo's other CI.

- Runs `make verify` on `pull_request`, `make verify-full` on push to the default
  branch (resolved via git, falling back to `main`).
- Toolchain setup is keyed off the preset's `language` (`_CI_SETUP` in `scaffold.py`) —
  no preset-schema change, since `language` already exists. Covers all six preset
  languages (go, node, python, rust, java, ruby).
- **No-op guard:** the shipped Makefile uses `@echo "TODO(specced): …"` placeholders.
  `make verify` over those *passes trivially* — green CI that checks nothing. `specced
  ci` detects the marker and **refuses without `--force`**, exiting non-zero.
- Idempotent / non-clobber: skips an existing gate unless `--force` (the project's
  `_write_file` convention). `sync` deliberately does **not** refresh CI — workflow
  changes that run on every PR should be explicit (`specced ci --force`).
- `--pre-commit` additionally writes a `.pre-commit-config.yaml` running the *fast*
  part only (`make fmt lint`; tests are too slow for a commit hook).

**Known limit:** one toolchain per repo. A multi-stack repo (e.g. the `tauri` preset =
node + rust) gets its primary language's setup plus a warning; the second toolchain is
added by hand. This tracks the existing "one preset per repo" limitation.

## Part B — the signal convention (the keystone)

Goal: answer "which rules/dims fire, is the gate passing?" **without a committed
run-log.** Four sources, three already free:

1. **Engine `verdict.json` / `evidence.json`** *(exists today)* — per-task gate
   PASS/FAIL, `commands_run`, `changed_files`, `artifacts_used`. A future `stats` globs
   `.agent/tasks/*/`. If the verifier cited rule/dim files in `artifacts_used`, rule
   usage comes for free; if not, no loss.
2. **GitHub Actions run history** *(Part A enables)* — `gh run list --workflow
   specced-gate.yml --json conclusion,headSha,createdAt`. Gate pass/fail over time, with
   nothing committed to the repo.
3. **`code-review` trailer** *(added)* — a structured echo of the sources the skill
   already cites, grep-able from PR bodies / review comments.
4. **`capture-rule` trailer** *(added)* — logs rule births so provenance is mineable.

**Decision: no `.specced/runs/` committed log in v1.** Sources 1+2 cover local
proof-loop runs and CI runs; a committed log is clutter and merge-conflict bait. Keep
it as a documented fallback for CI-less / non-GitHub repos later.

### Signal grammar

Emitted as the **last line** of the relevant artifact (review output; rule-capture
confirmation). Fields are space-separated `key=value`; omit an empty field.

```
Specced-Review: verdict=<block|approve-nits|approve> dims=<NN-slug,…> rules=<track/file.md,…> cites=<CONSTITUTION§n,…>
Specced-Rule: <created|sharpened> <home>
```

`stats` (next thread) parses these with a single regex per prefix. Any agent or tool
that wants to contribute signal emits the same shape.

## Part C — MCP auto-suggest (closes the deps-detection gap)

`suggest_mcp` keyed off docker-compose images only, and never suggested `sentry` or
`playwright`. Now `detect()` also collects a `dep_signals` set from real dependencies —
`go.mod` (`pgx`, `lib/pq`, `qdrant`, `sentry-go`), `pyproject`/`requirements.txt`
(`psycopg`, `asyncpg`, `sqlalchemy`, `sentry-sdk`, `qdrant-client`, `supabase`,
`playwright`), and `package.json` (`pg`, `prisma`, `@sentry/*`, `playwright`,
`@supabase/*`, `qdrant`). `DEP_MCP_SIGNALS` maps each to a server.

**Advisory, not auto-install** (matches the architecture: presets drive `init`'s
install; detection only advises). Surfaced as a `suggestions` field in `specced doctor`:
*"detected stack suggests MCP 'sentry' (not enabled) — `specced add-mcp sentry`."*

## Decisions

1. `specced ci` is a separate opt-in command, not folded into `init` (installing CI is
   outward-facing — it runs on every PR — and deserves an explicit step).
2. No committed run-log; mine `gh` history + the engine's existing `verdict.json`.
3. v1 scope = GitHub Actions + optional pre-commit. GitLab/others deferred.
4. `sync` does not refresh the CI file; `specced ci --force` is the deliberate refresh.
5. MCP suggestion is advisory (a `doctor` hint), never auto-added.

## What this unlocks

`specced stats` becomes a thin reader over sources 1+2+3 — the next thread, not this
one. Then the write side of the loop (learn-from-review → propose a rule via
`capture-rule`; promote constitution "direction" items observed enforced-in-practice).
