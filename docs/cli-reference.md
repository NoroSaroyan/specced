# CLI reference

Every command prints a JSON result to stdout, so the interview agent (and scripts) can
read exactly what happened. Commands that act on a repo take `--repo-root` (default: the
current directory; the repo root is resolved via git).

```
specced <command> [options]
```

## detect

```
specced detect [--repo-root PATH]
```
Inspect the repo and print stack signals: `languages`, `frameworks`, `tools`, `tracks`,
`infra` (databases, migrations), `existing`, `monorepo`, plus `suggested_preset`,
`suggested_mcp`, `suggested_verification`, and a human `summary`. Read-only.

## presets

```
specced presets
```
List available stack presets (name + description). See [Presets](presets.md).

## init

```
specced init [--repo-root PATH] [--preset NAME|auto] [--minimal] [--force]
             [--format-cmd "make fmt lint"]
```
Install (or refresh) the setup. Idempotent: existing files are skipped unless `--force`.

- `--preset NAME` — apply a stack preset; `--preset auto` picks one from detection.
- `--minimal` — install only the engine, agents, managed blocks, and config (skip the
  Layer-2 content files so the interview can author them by hand).
- `--force` — overwrite existing files.
- `--format-cmd` — the command for the Stop-hook (default `make fmt lint`).

Output lists every action (`created` / `skipped` / `overwritten`) and the chosen preset.

## adopt

```
specced adopt [--repo-root PATH] [--apply]
```
Absorb an existing hand-built setup into specced management — the inverse of `init`, for a
repo that already has a `.claude/`, a `CLAUDE.md`, a Makefile, etc. **Dry-run by default**:
it prints a `plan` (what it would install / synthesize / keep / flag), the `found`
inventory, and `interview_followups` (the semantic work it won't guess at) — and writes
nothing. Pass `--apply` to execute only the mechanical, non-destructive steps:

- installs the engine + agents and upserts the managed + orientation blocks into
  `CLAUDE.md` / `AGENTS.md` (your prose is preserved, never clobbered);
- synthesizes `.specced/checks.json` and the permission allowlist from your **actual
  Makefile targets** (not a preset), chaining the present gates when there's no `verify`;
- records existing `.mcp.json` servers and the detected stack in `.specced/config.json`.

It never rewrites your Makefile, `CONSTITUTION.md`, rules, dimensions, or `.mcp.json`. Then
run the bootstrap interview for the `interview_followups`.

## ci

```
specced ci [--repo-root PATH] [--force] [--pre-commit]
```
Emit `.github/workflows/specced-gate.yml` — a GitHub Actions workflow that runs the same
gate the proof loop uses: `make verify` (fmt + lint + test) on pull requests,
`make verify-full` (adds build) on the default branch. The toolchain setup is chosen
from the preset's language. specced-owned and self-contained: it never edits the repo's
other workflows.

- Refuses (exit `1`) if the `make` targets are still `TODO(specced)` placeholders — a
  gate over them would be a green no-op. Wire the Makefile first, or pass `--force`.
- Non-clobber: skips an existing gate unless `--force`. `sync` does **not** refresh it —
  re-run `specced ci --force` deliberately.
- `--pre-commit` also writes a `.pre-commit-config.yaml` fast hook (`make fmt lint`).

## add-mcp

```
specced add-mcp <names…> [--repo-root PATH] [--force]
```
Merge MCP servers from the catalog into `.mcp.json`. Names not in the catalog are
reported under `unknown` and the command exits non-zero. Existing entries are kept unless
`--force`. The catalog is listed in `specced status` (`mcp_catalog`).

## add-skill

```
specced add-skill <name> [--repo-root PATH] [--force]
```
Copy a library skill into `.claude/skills/<name>/` and record it in config. Exits
non-zero (with the available list) if the name isn't a library skill. See [Skills](skills.md).

## list-skills

```
specced list-skills
```
List the library skills available to install.

## sync

```
specced sync [--repo-root PATH]
```
Refresh the engine, the four agents, and the managed guide blocks to this specced
version. Does not touch your authored content. Run after upgrading specced.

## doctor

```
specced doctor [--repo-root PATH]
```
Verify the install is consistent (engine present, agents installed, managed block in
`CLAUDE.md`, config present). Prints each check with a fix `hint`. Exit code `0` if all
pass, `1` otherwise — usable as a CI gate. Also returns non-fatal `warnings` for content
that was scaffolded but left unfilled (e.g. `CONSTITUTION.md` or rules still carrying
`TODO(specced)`), so an agent knows which guidance isn't yet authoritative — and
`suggestions`, advisory MCP servers the detected stack implies but `.mcp.json` hasn't
enabled (e.g. a `sentry-sdk` dependency → `specced add-mcp sentry`).

## status

```
specced status [--repo-root PATH]
```
Show installed components, the engine version, installed skills, available presets, the
MCP catalog, and the contents of `.specced/config.json`.

## stats

```
specced stats [--repo-root PATH]
```
Mine the usage signal to show how the installed setup is actually exercised — read-only,
and the input the self-improving loop needs. Reads three best-effort sources (a missing
one is reported under `notes`, never fatal): proof-loop task records
(`.agent/tasks/*/verdict.json` + `evidence.json`), the `Specced-Review:` / `Specced-Rule:`
trailers in git history, and the specced gate's GitHub Actions runs (via `gh`). Reports
gate pass/fail health, per-rule and per-dimension citation counts, **dead rules** (present
but never referenced), `phantom` citations (to missing files), review-verdict tallies, and
changed-file `hotspots`. `signal_present` is `false` until there's proof-loop or trailer
activity to mine.

## version

```
specced version
```
Print the specced and bundled-engine versions.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | success |
| `1` | `doctor` found a problem · `add-skill` failed · `add-mcp` got an unknown server · `ci` hit placeholder targets (without `--force`) |

## Examples

```bash
# Inspect, then bootstrap with the detected preset
specced detect
specced init --preset auto

# Already have a hand-built setup? Adopt it (plan first, then apply)
specced adopt
specced adopt --apply

# Explicit preset + extra servers + a skill
specced init --preset go --format-cmd "make fmt lint"
specced add-mcp postgres github sentry
specced add-skill release

# Put the verify gate in CI (runs make verify on PRs, verify-full on main)
specced ci

# Health check (CI-friendly)
specced doctor || echo "setup drifted"

# See which rules/dimensions actually get used, and gate health
specced stats
```
