---
name: code-review
description: Run a dimension-based code review of a change using this repo's review guides in .claude/code-review/ and the rules in .claude/rules/. Use when the user asks for a review, before opening a PR, or to verify a proof-loop task against project conventions.
---

# Code review

Review a change against this repository's own standards — not generic advice.

## Inputs

- The diff under review (default: uncommitted changes / current branch vs the
  base; ask if ambiguous).
- The review dimensions in `.claude/code-review/*.md` (each is one lens).
- The conventions in `.claude/rules/**` and the invariants in `CONSTITUTION.md`.

## Method

1. Determine the changed files and the diff scope.
2. For each dimension file in `.claude/code-review/` (in number order), apply its
   checklist to the changed files. Honor the **always-critical** classes listed in
   `.claude/code-review/README.md`.
3. For each finding, decide severity with the rubric (Critical / Important / Minor)
   and cite the source (`CONSTITUTION.md §n` or a rule file). Only report findings
   you are confident are real — no speculative noise.

## Output

Group by severity, highest first. One line per finding:

```
[CRITICAL] path/to/file.py:42 — <what's wrong> → <concrete fix>  (CONSTITUTION §2)
```

End with a one-line verdict: **block** (any Critical), **approve with nits**
(Important/Minor only), or **approve** (clean). If reviewing a proof-loop task,
write findings the fixer can act on and stop short of editing code yourself.

> TODO(specced): If this project needs review steps beyond the generic dimensions
> (e.g. a required command to run, a contract test), add them here.
