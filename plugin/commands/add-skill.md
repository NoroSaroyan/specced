---
description: Add a domain skill to this repo — from the specced library or scaffolded fresh.
argument-hint: "[skill-name]"
---

Add a domain skill to this repository.

1. Run `specced list-skills` to see what the library offers.
2. If the user named a library skill (`$ARGUMENTS`) or picks one, install it with
   `specced add-skill <name>`, then read its `SKILL.md` and adapt any
   `TODO(specced)` markers to this project's stack and `.claude/rules/`.
3. If they want something not in the library, scaffold a new project skill under
   `.claude/skills/<name>/` following the conventions in `.claude/rules/` and the
   structure of the existing skills. Make every step it describes runnable.

Confirm the result with `specced status`.
