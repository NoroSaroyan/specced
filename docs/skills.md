# Skills

A **skill** is a reusable playbook for a recurring engineering task. In Claude Code you
don't call skills by name — Claude routes to one by its `description`, so you just
describe the task and the matching skill activates. Each specced skill encodes the
discipline for its task, references your `.claude/rules/**` and `CONSTITUTION.md`, keeps
every step runnable, and hands off to the proof loop.

## The library

Install any of these with `specced add-skill <name>`:

### Foundations
| Skill | Use when |
|---|---|
| `code-review` | Reviewing a diff against this repo's review dimensions + rules. |
| `new-domain-skill` | Creating a new project-specific skill for a recurring task. |
| `decision-record` | Recording a significant/architectural decision as an ADR. |
| `capture-rule` | Turning a user correction or preference into a durable rule or ADR. |

### Build
| Skill | Use when |
|---|---|
| `api-endpoint` | Adding or changing an HTTP endpoint, contract-first. |
| `db-migration` | Writing a backward-compatible, reversible schema migration. |
| `add-integration` | Integrating an external service / API / connector / webhook. |
| `background-worker` | Adding a queue consumer, job, or scheduled task. |
| `regen-client` | Regenerating SDKs / clients / types from a contract or schema. |
| `write-tests` | Adding tests to existing or under-tested code. |

### Maintain
| Skill | Use when |
|---|---|
| `debug-issue` | Systematically debugging a bug/failure (with a regression test). |
| `refactor` | Restructuring code without changing behavior. |
| `dependency-upgrade` | Safely upgrading dependencies / applying a security patch. |
| `perf-investigation` | Measure-first performance work against a budget. |

### Ship & assure
| Skill | Use when |
|---|---|
| `security-review` | A focused, defensive security pass over a change. |
| `release` | Cutting a versioned release. |
| `prepare-pr` | Assembling a PR from a completed proof-loop task's evidence. |

List them at runtime with `specced list-skills`.

## Installing

```bash
specced add-skill api-endpoint        # lands in .claude/skills/api-endpoint/
specced add-skill write-tests
```

Each installed skill has `TODO(specced)` markers for stack-specific bits (test runner,
migration tool, profiler). Resolve them once for your repo — or let the bootstrap
interview adapt them when it installs the skill.

## Project-specific skills

When a recurring task is specific to *your* repo, don't force it into the library — use
the `new-domain-skill` skill to scaffold one under `.claude/skills/`. If it turns out to
be broadly reusable, contribute it back to the specced library (see
[authoring skills](authoring-skills.md)).
