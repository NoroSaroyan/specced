# Contributing to specced

## Dev setup

```bash
make install      # uv venv + editable install with dev extras
make verify       # ruff format --check + ruff check + pytest + build (the CI gate)
```

Individual targets: `make fmt`, `make lint`, `make test`, `make build`.

## Layout

```
src/specced/
  cli.py          # argparse surface (JSON output)
  scaffold.py     # deterministic mechanics: engine, agents, managed blocks, presets, mcp
  detect.py       # stack detection
  templates/      # SINGLE source of truth shipped in the wheel
    skills/repo-task-proof-loop/   # vendored engine (Apache-2.0 — do not edit; see NOTICE)
    skills/<name>/                 # library skills
    presets/*.json                 # stack presets
    mcp/servers.json               # MCP server catalog
    project/                       # CONSTITUTION / settings / mcp / Makefile templates
    rules/  code-review/           # skeletons + _template.md
plugin/           # Claude Code plugin (the interview); references the CLI, ships no templates
tests/            # pytest
```

`templates/` is data, not code. Ruff is configured to **never** lint it (it holds the
vendored engine and example snippets).

## Adding a stack preset

See [docs/presets.md](docs/presets.md). In short: drop a `templates/presets/<name>.json`
with a `detect` block (markers + priority) — detection is data-driven, so no code change;
`make verify`'s property tests check it automatically.

## Adding a library skill

See [docs/authoring-skills.md](docs/authoring-skills.md). Drop
`templates/skills/<name>/SKILL.md` matching the house style, and add it to the
expected set in `tests/test_scaffold.py`.

## Updating the vendored engine

The `repo-task-proof-loop` engine is vendored under
`templates/skills/repo-task-proof-loop/` (Apache-2.0, OpenAI — see `NOTICE`). To
update, replace that directory wholesale from upstream and keep the `LICENSE`
file. Don't hand-patch it; `specced sync` copies it verbatim into target repos.

## Conventions

- Every CLI command prints JSON to stdout (the interview parses it).
- Scaffolding is create-if-absent + idempotent; never clobber user content without `--force`.
- No AI/assistant attribution in commits or PRs.

## Releasing

Publishing to PyPI uses **Trusted Publishing** (OIDC) via `.github/workflows/release.yml`
— no API tokens are stored.

One-time PyPI setup (project owner), at <https://pypi.org/manage/account/publishing/>:

- PyPI project name: `specced`
- Owner: `NoroSaroyan` · Repository: `specced`
- Workflow: `release.yml` · Environment: `pypi`

(Add it as a *pending publisher* before the first release; PyPI creates the project on
first publish.) Optionally create a GitHub Environment named `pypi`
(Settings → Environments) for release protection.

To cut a release:

1. Bump `version` in `pyproject.toml` (SemVer); update the changelog; `make verify`.
2. Commit, then publish a GitHub Release with tag `vX.Y.Z` (must match the version).
3. `release.yml` builds and publishes to PyPI. See the `release` skill for the full flow.
