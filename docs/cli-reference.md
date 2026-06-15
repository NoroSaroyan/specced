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
`TODO(specced)`), so an agent knows which guidance isn't yet authoritative.

## status

```
specced status [--repo-root PATH]
```
Show installed components, the engine version, installed skills, available presets, the
MCP catalog, and the contents of `.specced/config.json`.

## version

```
specced version
```
Print the specced and bundled-engine versions.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | success |
| `1` | `doctor` found a problem · `add-skill` failed · `add-mcp` got an unknown server |

## Examples

```bash
# Inspect, then bootstrap with the detected preset
specced detect
specced init --preset auto

# Explicit preset + extra servers + a skill
specced init --preset go --format-cmd "make fmt lint"
specced add-mcp postgres github sentry
specced add-skill release

# Health check (CI-friendly)
specced doctor || echo "setup drifted"
```
