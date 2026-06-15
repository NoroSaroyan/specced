---
description: Check that the specced setup in this repo is consistent, and fix what's drifted.
---

Verify the specced setup health.

1. Run `specced doctor` and `specced status`.
2. For each failing check, apply its `hint` (usually `specced init` or
   `specced sync`), then re-run `specced doctor`.
3. Also sanity-check the content layer the CLI can't judge: does `CONSTITUTION.md`
   still have unfilled `TODO(specced)` markers? Are there empty `.claude/rules/`
   tracks? Report anything that looks like an unfinished bootstrap.

Summarize the final state and any remaining manual follow-ups.
