# Code review dimensions

Dimension-based review guides. Each `NN-<topic>.md` is one lens a reviewer (human
or agent) applies to a change. Splitting review into dimensions keeps each pass
focused and makes "did we check X?" answerable.

## Severity rubric

- **Critical** — must fix before merge. Breaks a `CONSTITUTION.md` invariant,
  leaks data, corrupts state, or fails a verification budget.
- **Important** — should fix; correctness/maintainability risk that isn't a hard
  stop.
- **Minor** — nice to fix; style and polish.

## Always-critical classes

> TODO(specced): List the change classes that are *automatically* Critical for
> this project (e.g. "any change to authorization filtering", "any cross-boundary
> import"). These are the things a reviewer must never wave through.

## Running a review

Apply each dimension to the diff, report findings as
`[SEVERITY] file:line — issue → suggested fix`, and only surface findings you are
confident are real. Copy `_template.md` to add a dimension.
