# Coding rules

Layer-specific conventions for this repo. The proof-loop agents read these:

- the **spec-freezer** turns relevant rules into explicit acceptance criteria,
- the **builder** follows them while implementing,
- the **verifier** checks the code against them.

Keep each file short, concrete, and enforceable. A rule a reviewer can't check is
a comment, not a rule — put those in `docs/` instead.

## Layout

Organize by track / layer, for example:

```
.claude/rules/
  backend/      architecture.md, data.md, migrations.md, api.md, ...
  frontend/     components.md, data-fetching.md, ...
  ml/           prompts.md, routing.md, ...
```

Copy `_template.md` to start a new rule file. Truly global, rarely-changing rules
belong in the repo `CONSTITUTION.md`, not here.

> TODO(specced): The bootstrap interview populates these from your stack and answers.
