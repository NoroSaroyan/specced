# specced — handoff

State of the project as of **v0.1.2** (2026-06-17), written so a fresh session can pick
up cold and reason about what to build next.

## What specced is

A tool that installs a reusable, **interview-driven agentic coding setup** into any repo —
the proof-loop engine, project agents, coding rules, code-review dimensions, MCP servers,
and a verification gate — so you stop copy-pasting `.claude/` scaffolding between projects.
It is two surfaces over **one** template tree:

- **CLI** (`src/specced/`, on PyPI) — deterministic, agent-agnostic scaffolding.
- **Claude Code plugin** (`plugin/`) — the `specced-bootstrap` skill that *interviews*
  the user (detect → ask → call the CLI → author the project-specific content).

Three layers it installs: (1) the vendored **proof-loop engine** (OpenAI, Apache-2.0),
(2) the **structure** (agents, managed `CLAUDE.md`/`AGENTS.md` blocks, gate, skeletons),
(3) the **content** the interview authors (CONSTITUTION, rules, review dims, MCP).

## Shipped / live

- **PyPI:** `specced 0.1.2` — `uv tool install specced` / `pip install specced`.
- **GitHub:** https://github.com/NoroSaroyan/specced (public; CI green; branch protection).
- **Plugin marketplace:** `/plugin marketplace add NoroSaroyan/specced`.
- **Repo-as-code:** `infra/terraform/github/` manages the repo + settings (Terraform state
  is **local** on the maintainer's machine — HCP remote backend was planned, not wired).
- **Releases:** GitHub Release `vX.Y.Z` → `.github/workflows/release.yml` publishes to PyPI
  via **Trusted Publishing** (OIDC, no tokens; env `pypi`).

## Code map

```
src/specced/
  cli.py         # argparse surface (JSON output): detect, presets, init, add-mcp,
                 #   add-skill, list-skills, sync, doctor, status, version
  scaffold.py    # mechanics: engine/agents/managed-blocks, presets, mcp compose,
                 #   permission allowlist, checks.json, repo-map, orientation, doctor
  detect.py      # stack fingerprint (data-driven preset selection)
  _paths.py      # shared templates_dir (avoids scaffold<->detect import cycle)
  templates/     # SINGLE source of truth (shipped in the wheel)
    skills/repo-task-proof-loop/  # vendored engine (do not edit; see NOTICE)
    skills/<name>/                # 19 library skills
    presets/*.json                # 13 stack presets (data-driven `detect` block each)
    mcp/servers.json              # 7-server MCP catalog
    project/                      # CONSTITUTION / settings / mcp / Makefile templates
    rules/ , code-review/         # skeletons + _template.md
plugin/          # marketplace.json + plugin.json + commands/ + specced-bootstrap skill
tests/           # 47 pytest tests (property-based; grow without churn)
docs/            # user + contributor docs
infra/terraform/github/  # repo-as-code
```

Dev loop: `make install` then `make verify` (ruff + pytest + build = the CI gate).

## What's in the box (v0.1.2)

- **13 presets:** go, rust, python-fastapi, python-django, python, node-next, node-svelte,
  node-react, node-express, node, java-spring, ruby-rails, **tauri**.
- **17 skills:** code-review, new-domain-skill, decision-record, capture-rule, api-endpoint,
  db-migration, add-integration, background-worker, regen-client, write-tests, debug-issue,
  refactor, dependency-upgrade, perf-investigation, security-review, release, prepare-pr.
- **MCP catalog:** context7, github, postgres, qdrant, supabase, playwright, sentry.
- **Agent-experience layer** (written by `init`, not in `--minimal`): permission allowlist
  (`.claude/settings.local.json`), machine-readable `.specced/checks.json` (two-level
  `verify`/`verify-full` gate), generated `.specced/repo-map.md`, an orientation managed
  block in the guide files, and `doctor` warnings (unfilled `TODO(specced)`; git-ignored
  `.claude/`).

## What's been validated (dogfood)

1. **jewelry-tracker** (Tauri: Next.js + Rust/SQLx) — drove the 0.1.1 fixes: the `tauri`
   preset, Tauri/Rust detection, two-level gate, the `.claude` git-ignore warning, and the
   enforced-today-vs-direction constitution distinction.
2. **ContextGate** (Go; the maintainer's fullest hand-built setup) — head-to-head: specced
   + the interview **reproduced it ~1:1** — same 8 domain rules, same 9 review dimensions,
   the same hard invariants (ACL fail-closed, OSS/EE boundary, NFR budgets, two-phase
   migrations), authored *from the code*. specced's versions are ~30% terser; it also adds
   the agent-experience layer ContextGate predates. Drove the 0.1.2 deploy/compose fix.

Conclusion: **mechanics for free + interview authors the domain layer ≈ an expert hand-built
setup.** The thesis holds against the gold standard.

## Landed since v0.1.2 (unreleased, in `main`)

The **day-2 lifecycle** thread — get a setup *in* → *enforce* it → *evolve* it. Full
design + decisions in `docs/proposals/ci-gate-and-signal.md`.

- **`specced ci`** — emits `.github/workflows/specced-gate.yml` running the same gate
  (`make verify` on PRs, `make verify-full` on the default branch). Toolchain setup is
  keyed off the preset language (all 6). Refuses over `TODO(specced)` placeholder targets
  (the no-op-CI guard) unless `--force`; `--pre-commit` adds a fast hook. Non-clobber like
  init; `sync` deliberately leaves CI alone (re-run `specced ci --force`).
- **Signal convention (the keystone for the loop):** `code-review` and `capture-rule`
  now emit machine-readable trailers (`Specced-Review:` / `Specced-Rule:`; grammar in the
  proposal). Combined with the engine's existing `.agent/tasks/*/verdict.json` (PASS/FAIL,
  commands, changed files), these are the sources a future `specced stats` mines — no
  committed run-log, no engine edits.
- **Deps-based MCP detection** (closes the old "beyond compose" gap): `detect()` collects
  `dep_signals` from go.mod / pyproject+requirements / package.json; `suggest_mcp` maps
  them (postgres, qdrant, sentry, playwright, supabase); `doctor` returns a `suggestions`
  list for servers the stack implies but `.mcp.json` hasn't enabled. Advisory, not auto-add.
- **`specced stats`** (the loop's read side) — new `src/specced/stats.py` module + CLI
  command. Read-only miner over the three signal sources (proof-loop `verdict.json`/
  `evidence.json`, the git-history trailers, and `gh` CI runs; each best-effort, reported
  in `notes` when absent). Surfaces gate pass/fail health, per-rule & per-dimension
  citation counts, **dead rules**, `phantom` citations, review-verdict tallies, and
  changed-file hotspots. `signal_present` is false until there's activity to mine.
- **`specced adopt`** (the inverse of init) — absorb an existing hand-built setup.
  **Dry-run by default** (the `plan` + `found` inventory + `interview_followups` are the
  deliverable); `--apply` runs only mechanical, non-destructive steps. Safety boundary:
  CREATES specced-owned files + UPSERTS managed blocks (prose preserved), and NEVER
  rewrites the Makefile, CONSTITUTION, rules, dims, or `.mcp.json`. Standout mechanic:
  synthesizes `checks.json` + the permission allowlist from the repo's **actual Makefile
  targets** (`_parse_makefile_targets`), chaining present gates when there's no `verify`.
  Records existing `.mcp.json` servers + detected stack in config. Semantic work (classify
  prose, align rules, author missing layers) is handed to the interview as followups.
- **Loop write side** — two new library skills (19 total now): **`learn-from-review`**
  (mine recurring `Specced-Review:` findings → cluster → author rules via `capture-rule`)
  and **`promote-constitution`** (audit CONSTITUTION's enforced-today vs direction split,
  promote items now backed by a check/cited rule). The CLI half is deterministic: `specced
  stats` gained a `candidates.rules_from_reviews` block (dimensions that produced findings
  citing no rule, ≥2× = recurring & un-encoded) that `learn-from-review` consumes. The
  clustering/judgment itself is intentionally skill-side (semantic), not CLI.

**The day-2 lifecycle thread is now complete** — get a setup *in* (`adopt`), *enforce* it
(`ci` + signal), *observe* it (`stats`), *evolve* it (`learn-from-review` +
`promote-constitution`). The chosen non-pick was multi-agent compile (Cursor/Copilot/etc.
emitters from the one template tree) — still the strongest *breadth* play if reach matters
next. Other open items live in *Known gaps* below.

## Known gaps / deferred (good first issues)

- ~~**Detection beyond compose:**~~ done — deps-based MCP signals (see *Landed* above).
  Still room to infer *more* (cache/queue servers, ORMs → migration tooling).
- **`settings.local.json` merge:** today `init` *skips* an existing one (safe) — could merge
  specced's verify-command allowlist into it instead.
- **No `commands` concept:** ContextGate has `.claude/commands` (eval, nfr-check); specced
  maps those to `make` targets + skills. Decide whether to scaffold commands too.
- **Monorepo multi-stack:** one preset per repo today; a real monorepo (e.g. python backend
  + node frontend) needs per-track preset composition.
- **Interview→rules→dims ordering:** when fanning out, author rules *before* review dims so
  the dims can cite the rule files (a coordination nuance, not a bug).
- **Terraform state is local** — wire HCP/remote backend if durability/sharing matters.
- Cosmetic: `templates/rules/README.md` still carries a `TODO(specced)` line.

## Feature ideas to consider next

- **`specced update`** — diff the specced-managed content (engine, agents, blocks, gate)
  across versions and apply, showing what changed (today only `sync` force-refreshes).
- **`specced doctor --fix`** — auto-apply safe fixes (un-ignore `.claude/{rules,agents}`,
  append a missing `verify` target to an existing Makefile).
- **Deps-based detection** (above) + **more presets** (elixir-phoenix, php-laravel, deno,
  dotnet, python-flask, java-gradle).
- **Per-track preset composition** for monorepos.
- **Team profiles** — an org baseline constitution/rules a repo extends.
- **Golden-repo tests** — fixture repos + asserted `specced init` output (beyond unit tests).
- **Richer generated stubs** — more example-driven rule/review templates.
- **`sync` extends to library skills** — refresh installed library skills, not just the engine.

## Operational gotchas

- The GitHub handle is **`NoroSaroyan`** (the author email `noriksaroyan@gmail.com` is
  separate — don't confuse them in URLs).
- `uv tool install` caches by version: after editing source at the *same* version, run
  `uv cache clean specced` or install the freshly built wheel, or the global `specced`
  serves a stale build. (Bumping the version sidesteps this.)
- CI pins `actions/checkout@v6` + `astral-sh/setup-uv@v8.2.0` (setup-uv has no moving `v8`).
- Release flow: bump `version` in `pyproject.toml` (+ `__init__.py` + `scaffold.py`
  `SPECCED_VERSION`, `plugin/.claude-plugin/plugin.json`), `make verify`, commit, `gh release create vX.Y.Z` — `release.yml` has
  a tag==version guard.
