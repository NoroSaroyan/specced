---
name: specced-bootstrap
description: Bootstrap the specced agentic coding setup into the current repository. Detects the stack with `specced detect`, interviews the user, runs `specced init --preset` for mechanical scaffolding, then authors the project-specific CONSTITUTION, coding rules, code-review dimensions, MCP servers, and Makefile verification vocabulary. Use when the user wants to set up specced, the proof loop, or this agentic workflow in a new or existing repo.
---

# specced bootstrap

You are setting up the **specced** agentic coding setup in a repository.

## The contract (read this first)

Work splits in two, and you must respect the split:

- **The `specced` CLI does the mechanics** — installs the vendored proof-loop engine,
  the four project agents, the managed guide blocks, and (via presets) prefilled
  `Makefile` targets, per-track rule/review stubs, and `.mcp.json`. Deterministic and
  idempotent. Let it do this; don't hand-write what it installs.
- **You do the intelligence** — detect, interview, then replace skeletons with *real*
  content: `CONSTITUTION.md`, `.claude/rules/**`, `.claude/code-review/**`, and the
  precise verification commands.

Never fabricate project facts. Detect → ask → write. Everything stays in the repo.

## Step 0 — Preflight

1. Confirm the working directory is the repo to set up.
2. Check the CLI: `specced version`. If missing, tell the user to install it and run
   commands as `uvx --from <source> specced …` meanwhile:
   - `uv tool install specced` (once published), or
   - `uvx --from git+https://github.com/NoroSaroyan/specced specced version`, or
   - from a local checkout: `uv tool install /path/to/specced`.
3. `specced status` — if already initialized, this is a re-run: read
   `.specced/config.json`, fill only gaps, don't clobber authored content.

## Step 1 — Detect

Run `specced detect`. It returns languages, frameworks, tracks, infra (databases,
migrations), CI, a **suggested preset**, **suggested MCP servers**, and candidate
verification commands. Read it and show the user a 5–10 line summary. This makes the
interview short — you confirm detections instead of asking blind. Read a few key files
yourself (the existing `Makefile`, `package.json` scripts, any `docs/` conventions) to
sharpen the picture, especially for monorepos where one preset won't cover every track.

## Step 2 — Interview

Use `AskUserQuestion`, batched into a few rounds. Lead every question with the detected
default as the recommended option. Cover:

1. **Tracks & layout** — confirm tracks and their root dirs.
2. **Verification vocabulary** *(most important)* — confirm the real command for
   format, lint/type-check, test, build, and e2e. These become the `Makefile` targets
   and the proof loop's acceptance-criteria vocabulary, and the Stop-hook (`make fmt lint`).
3. **Non-negotiables** — the invariant(s) that must never break; boundary rules; numeric
   budgets; security/supply-chain; backward-compat; commit attribution. For EACH, decide
   whether it's **enforced today** (true of the code now) or a **direction** (target for
   new code) — read the code to check, don't assume. → constitution.
4. **Per-track conventions** — the few rules that matter most per track. → rules.
5. **Always-critical review classes** — what a reviewer must never wave through. → code-review.
6. **MCP servers** — confirm the suggested set (`specced status` lists the catalog). → `.mcp.json`.
7. **Domain skills** — show `specced list-skills`; pick which to install.

Three or four well-batched rounds is plenty.

## Step 3 — Install the mechanics

Run from the repo root:

- With a preset: `specced init --preset <name>` (pick from `specced presets`, or
  `--preset auto` to use detection). This installs the engine + agents + managed
  blocks, prefills the `Makefile`, stubs per-track rules + review dimensions, and
  composes `.mcp.json`.
- Add any extra MCP servers: `specced add-mcp <names…>` (e.g. `sentry playwright`).
- Set the hook command if it isn't `make fmt lint`: pass `--format-cmd "…"`.
- Pure-by-hand path: `specced init --minimal`, then author all Layer-2 yourself.

`init` also writes the **agent-experience layer**: a permission allowlist
(`.claude/settings.local.json`) pre-authorizing the verify commands, a machine-readable
`.specced/checks.json`, a generated `.specced/repo-map.md`, and an orientation block in
`CLAUDE.md`/`AGENTS.md`. Read the JSON result — it lists exactly what was created vs skipped.

## Step 4 — Author the project content

Replace skeletons with real, enforceable content informed by Steps 1–2:

- **`CONSTITUTION.md`** — resolve every `TODO(specced)`; state real invariants, budgets,
  policies; cut what doesn't apply. Mark each invariant **enforced-today** (Critical) vs
  **direction** (new code only), checked against the actual code, so the gate doesn't flag
  healthy existing code.
- **`.claude/rules/<track>/*.md`** — fill each stub: one-line, imperative, checkable
  rules with good/bad examples from the actual code, and how a reviewer verifies each.
- **`.claude/code-review/NN-*.md`** — fill each dimension; cite a constitution clause
  or rule file; complete the always-critical list.
- **`Makefile`** — confirm the prefilled commands are correct for this repo (fix
  monorepo paths, e.g. `cd backend && …`). `make verify` must actually work.
- **`.mcp.json` / `.claude/settings.json`** — confirm servers and the Stop-hook.

Match the repo's style. Cite real paths and commands, never placeholders.

## Step 5 — Domain skills

- Install chosen library skills: `specced add-skill <name>`, then adapt their
  `TODO(specced)` markers to this stack and `.claude/rules/`.
- For project-specific playbooks, use the `new-domain-skill` skill to scaffold one
  under `.claude/skills/` with runnable steps.
- Install `capture-rule` so a later user correction becomes a saved rule/ADR instead
  of a repeated mistake.

## Step 6 — Verify & hand off

1. `specced doctor` — resolve any failing check (hints say `specced init`/`sync`), and
   read its `warnings`: they flag `CONSTITUTION.md`/rules still carrying `TODO(specced)`
   stubs (not yet authoritative). Clear them.
2. Self-check: no leftover `TODO(specced)` markers, no empty rule tracks, `make verify`
   is real.
3. Summarize what was installed and authored, then tell the user how to start their
   first task: invoke the **repo-task-proof-loop** skill with `init <TASK_ID>`.

## Guardrails

- Detect → ask → write. Never invent stack facts or budgets.
- The CLI is create-if-absent; only overwrite files you are intentionally authoring.
- Preserve user content outside the managed `<!-- repo-task-proof-loop -->` blocks.
- Keep everything repo-local; secrets via env interpolation only.
- A rule or acceptance criterion that can't be checked isn't done — make it runnable.
