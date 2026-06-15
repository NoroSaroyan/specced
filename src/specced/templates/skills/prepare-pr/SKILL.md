---
name: prepare-pr
description: Assemble a focused pull request from a completed change, pulling proof from a proof-loop task when present. Use when opening a pull request or preparing a change for review — to write the description, gather evidence, and run the pre-PR checklist.
---

# Prepare a pull request

Turn a finished change into a reviewable PR: confirm it's green, keep the diff
focused, and write a description that states **what** changed and **why** —
backed by proof, not narrative.

## Before you open it

1. Confirm the build and checks are green:
   ```bash
   make verify
   ```
   > TODO(specced): Replace with this repo's gate (e.g. `make ci`, `npm test`) and
   > note the CI checks a reviewer should expect to pass.
2. Confirm the diff is one logical change and small enough to review in one sitting:
   ```bash
   git fetch origin && git diff --stat origin/main...HEAD
   ```
   Split unrelated changes (drive-by refactors, formatting) into separate PRs.
   > TODO(specced): Set the base branch and any branch-naming convention (e.g.
   > `feat/<scope>`, `fix/<scope>`).

## Pull the proof (if a proof-loop task exists)

If `.agent/tasks/<TASK_ID>/` is present, the proof is already written — use it:

```bash
cat .agent/tasks/<TASK_ID>/verdict.json   # must be overall PASS
sed -n '/AC[0-9]/p' .agent/tasks/<TASK_ID>/spec.md   # acceptance criteria
```

- Summarize the acceptance criteria and the `verdict.json` result in the PR body.
- Link `spec.md`, the `evidence.md` bundle, and any ADRs the change introduced
  (see the `decision-record` skill; e.g. `docs/decisions/NNNN-*.md`).
- Do **not** open the PR if the verdict is not `PASS` — finish the loop first.

If there's no task folder, state the verification you ran by hand instead.

## Write the description

State what changed and why it changed; let the diff show the how. Use this body:

```markdown
## What
<one or two sentences: the change, in plain terms>

## Why
<the problem, the trigger, or the decision this implements>

## Proof
- Acceptance criteria: AC1–ACn — all PASS (`.agent/tasks/<TASK_ID>/verdict.json`)
- Spec: `.agent/tasks/<TASK_ID>/spec.md`
- Decisions: docs/decisions/NNNN-<title>.md   <!-- omit if none -->
- Verified locally: `make verify` green

## Checklist
- [ ] Tests added/updated for the change
- [ ] Docs and `.claude/rules/**` updated if behavior or a convention changed
- [ ] No secrets, tokens, or credentials in the diff
- [ ] Migrations are backward-safe and reversible (or N/A)
- [ ] Diff is one logical change, scoped and reviewable
```

> TODO(specced): If this repo has a PR template (`.github/pull_request_template.md`),
> use it as the source of truth and fold these sections into it.

## Open it

1. Suggest reviewers (code owners of the touched paths) and labels (area + size).
   > TODO(specced): Note the label scheme and how reviewers are chosen here.
2. Keep the commit and PR text human. Per `CONSTITUTION.md` (Attribution): do **not**
   add AI / assistant attribution or co-author trailers to commits or the PR.

A green PR is the hand-off: it opens only after a clean verifier pass, so the
reviewer audits a focused diff against stated proof — not a work-in-progress.
