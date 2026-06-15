# The bootstrap interview

`/specced:init` runs the `specced-bootstrap` skill. What it does, step by step:

0. **Preflight** — confirm the repo, check `specced version`, run `specced status`
   (re-runs only fill gaps).
1. **Detect** — `specced detect` reports languages, frameworks, tracks, infra
   (databases, migrations), CI, plus a **suggested preset** and **suggested MCP
   servers**. The interview confirms detections instead of asking blind.
2. **Interview** — a few batched `AskUserQuestion` rounds covering: tracks, the
   verification vocabulary (fmt/lint/test/build/e2e), non-negotiables (→ constitution),
   per-track conventions (→ rules), always-critical review classes, MCP servers, and
   which library skills to install.
3. **Install mechanics** — `specced init --preset <name>` (or `--preset auto`):
   installs the engine + agents + managed blocks, prefills the `Makefile`, stubs
   per-track rule + review files, composes `.mcp.json`. `specced add-mcp <names>` adds
   anything extra.
4. **Author content** — the agent replaces skeletons with real content:
   `CONSTITUTION.md`, `.claude/rules/**`, `.claude/code-review/**`, and tightens the
   `Makefile`/hook to the project's true commands.
5. **Skills** — `specced add-skill <name>` for chosen library skills; or scaffold new
   project-specific ones (`new-domain-skill`).
6. **Verify & hand off** — `specced doctor`, confirm no leftover `TODO(specced)`
   markers, then point at the engine: start a task with the `repo-task-proof-loop`
   skill (`init <TASK_ID>`).

## Design principle

Detect → ask → write. The CLI owns mechanics so the agent can spend its judgment on
the content that actually has to fit *this* repo. Nothing is fabricated; every rule
and acceptance criterion is runnable.
