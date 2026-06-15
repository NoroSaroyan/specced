# FAQ & troubleshooting

### Do I need both the CLI and the plugin?

The **CLI** does the mechanical scaffolding and is required. The **plugin** adds the
interview (`/specced:init`) that detects your stack and authors content. You can use the
CLI alone — `specced init --preset auto` — and write the content yourself.

### Will it overwrite my existing `CLAUDE.md` / `Makefile` / `.mcp.json`?

No. Scaffolding is **create-if-absent**. Existing files are skipped (you'll see
`skipped (exists)` in the output). The only thing written into an existing
`CLAUDE.md`/`AGENTS.md` is the managed `<!-- repo-task-proof-loop -->` block, which is
inserted/updated in place and leaves the rest of the file untouched. Use `--force` only
if you explicitly want to overwrite.

### I already used the OpenAI proof-loop skill directly. Will I get two copies?

No. specced uses the **same** managed-block markers, so re-running keeps a single block.

### Does it work with Codex (not just Claude Code)?

Yes. `init` installs `.codex/agents/*.toml` and maintains the `AGENTS.md` managed block
alongside the Claude side. The CLI itself is agent-agnostic.

### Detection picked the wrong preset / a monorepo with two stacks.

Run `specced detect` to see what it found, then override: `specced init --preset
node-next`. Presets are **starting points** — for a monorepo, the interview (or you) adds
the second track's `Makefile` commands and rules by hand (e.g. `cd backend && …`).
`--preset auto` only picks one stack.

### `specced doctor` reports a failure.

Each check prints a `hint`. Usually `specced init` (missing files) or `specced sync`
(drifted engine/agents). Re-run `doctor` after applying it.

### There are `TODO(specced)` markers everywhere.

That's intentional — they mark the project-specific content you (or the interview) fill
in: real invariants in `CONSTITUTION.md`, conventions in `.claude/rules/**`, stack
specifics in skills. `specced doctor` and the interview's final check flag leftover ones.

### Where do secrets go?

Never in files. `.mcp.json` references them via `${ENV:-default}` interpolation; set the
environment variables in your shell or secret manager.

### How do I update?

```bash
uv tool upgrade specced     # newer CLI + bundled engine
specced sync                # refresh engine/agents/managed blocks in the repo
```

Your authored content (constitution, rules, review dims) is never touched by `sync`.

### How do I remove specced from a repo?

Everything it installs is just files in your repo. Delete what you don't want:
`.claude/skills/repo-task-proof-loop/`, `.claude/agents/task-*.md`,
`.codex/agents/task-*.toml`, the managed block in `CLAUDE.md`/`AGENTS.md`, and
`.specced/`. Your own rules/constitution stay.

### Is the proof-loop engine specced's own code?

No — it's the `repo-task-proof-loop` skill, vendored unmodified from OpenAI under
Apache-2.0 (see `NOTICE`). specced adds the structure, content, presets, skill library,
and the interview around it. specced's own code is MIT.

### What Python version do I need?

3.10+. The CLI is pure-Python with no runtime dependencies.

### Can I add my own presets and skills?

Yes — see [Presets](presets.md) and [authoring skills](authoring-skills.md). Broadly
useful ones are worth contributing back.
