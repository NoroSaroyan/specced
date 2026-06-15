# The proof loop

The proof loop is how you do substantial work in a specced repo: features, refactors,
migrations, bug fixes — anything that should leave proof it actually works. It's provided
by the `repo-task-proof-loop` engine skill that `specced init` installs.

## The cycle

```
freeze ──▶ build ──▶ evidence ──▶ verify ──▶ (fix ──▶ verify)* ──▶ PASS
```

1. **freeze** — turn the request into `spec.md`: explicit acceptance criteria (`AC1`,
   `AC2`, …), constraints, and non-goals. Every AC must be **runnable** — a `make`
   target, a test, a command, a grep. No production code changes here.
2. **build** — implement against the frozen spec.
3. **evidence** — rerun each AC and record `PASS` / `FAIL` / `UNKNOWN` with proof
   (commands, output, file paths) in `evidence.md` + `evidence.json`.
4. **verify** — a **fresh** verifier (new session/subagent) independently reruns the
   ACs against the *current code* — not the builder's story — and writes `verdict.json`
   (and `problems.md` if anything isn't PASS).
5. **fix** — apply the smallest safe changes from `problems.md`, refresh evidence.
6. Repeat verify → fix until the verdict is `PASS`.

The separation of **builder** and **fresh verifier** is the point: it's what makes
"done" mean *proven*, not *claimed*.

## Running it in Claude Code

The skill auto-triggers. Start a task by naming it and describing the work:

```
Use the repo-task-proof-loop skill: init add-rate-limiting
```

Then let it run the cycle. The main session routes phases to the installed agents
(`spec-freezer`, `builder`, `verifier`, `fixer`) by their descriptions. You can also
drive phases explicitly: `freeze add-rate-limiting`, `build …`, `verify …`.

For a big task you can authorize parallel work ("you can use subagents"); for a narrow
one it stays serial. Either way `init`, evidence ownership, and each verify pass stay
serialized.

## The artifacts

Everything lives under `.agent/tasks/<task-id>/`:

| File | Written by | Contains |
|---|---|---|
| `spec.md` | spec-freezer | Task statement, `AC1…`, constraints, non-goals |
| `evidence.md` / `evidence.json` | builder | Per-AC PASS/FAIL/UNKNOWN with proof |
| `verdict.json` | verifier (fresh) | Overall verdict + per-criterion status |
| `problems.md` | verifier | Per-failure: repro, expected/actual, smallest fix |
| `raw/` | builder/verifier | Command logs, screenshots, etc. |

This is the durable source of truth — not chat history, not a TODO list. Validate it any
time:

```bash
python3 .claude/skills/repo-task-proof-loop/scripts/task_loop.py status   --task-id <id>
python3 .claude/skills/repo-task-proof-loop/scripts/task_loop.py validate --task-id <id>
```

## How the rest of the setup plugs in

- **Acceptance criteria are `make` targets.** Keep `make fmt|lint|test|build|verify`
  honest and the proof loop has real gates. The verifier reruns them.
- **Rules and the constitution become criteria.** The spec-freezer reads
  `CONSTITUTION.md` and `.claude/rules/**` and turns the relevant ones into ACs.
- **Skills guide the build.** Installed skills auto-trigger during a task — e.g.
  `api-endpoint` while adding a route, `db-migration` for schema changes,
  `write-tests` to close coverage gaps.
- **Review before you ship.** Run the `code-review` (and `security-review`) skill against
  the diff; then `prepare-pr` turns the task's evidence into a PR description.

## A typical session

```
init add-audit-log              # create task scaffold
freeze add-audit-log            # spec-freezer writes runnable ACs (you confirm)
build add-audit-log             # builder implements; write-tests/db-migration skills assist
evidence add-audit-log          # builder packs proof
verify add-audit-log            # FRESH verifier → verdict.json
fix add-audit-log               # only if verdict ≠ PASS
verify add-audit-log            # fresh again → PASS
# then: code-review → prepare-pr
```

Don't claim completion until every AC is `PASS` in a fresh verdict.
