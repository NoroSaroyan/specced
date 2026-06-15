# Authoring library skills

A library skill is a reusable, stack-agnostic playbook for a recurring engineering
task. Users install one with `specced add-skill <name>`; it lands in their repo's
`.claude/skills/<name>/` and the agent adapts its `TODO(specced)` markers.

## Current library

`code-review`, `api-endpoint`, `db-migration`, `add-integration`,
`background-worker`, `regen-client`, `new-domain-skill`, `decision-record`.

List at runtime: `specced list-skills`.

## House style

A skill is a single `templates/skills/<name>/SKILL.md`:

- **Frontmatter:** `name:` (kebab-case, matches the dir) and a `description:` written
  as an auto-trigger — "Use when …" — because Claude routes to skills by description.
- **Body:** terse, imperative, example-driven. Every step must be **runnable or
  checkable**, never vibes.
- **Generic:** no project/stack specifics. Where something is stack-dependent, use a
  `> TODO(specced):` blockquote and point at `.claude/rules/**`, `CONSTITUTION.md`, and
  the `make` verification vocabulary.
- **End at the proof loop:** map the work to acceptance criteria the verifier reruns.
- **Length:** ~45–80 lines. One file; no extra assets unless essential.

Use `templates/skills/code-review/SKILL.md` as the reference.

## Checklist to add one

1. Write `templates/skills/<name>/SKILL.md` in house style.
2. Add `<name>` to the expected set in `tests/test_scaffold.py`.
3. `make verify`.

## Project-specific vs library

Skills that encode *this repo's* specifics belong in the repo
(`.claude/skills/`, authored via the `new-domain-skill` skill). When a skill is broadly
reusable, contribute it back here so every project gets it.
