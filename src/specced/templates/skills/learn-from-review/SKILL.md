---
name: learn-from-review
description: Use periodically, or after a batch of reviews, to turn recurring code-review findings into durable rules — triggers like "why do we keep flagging this", "turn our review history into rules", a review retro, or codifying repeated PR comments. Mines `specced stats` + the Specced-Review trailers and writes rules via capture-rule.
---

# Learn from review

Close the loop: a finding a reviewer keeps writing is a rule that doesn't exist yet.
Encode it once and the next agent stops making the mistake — and reviews get cheaper.
This skill *mines and clusters*; it hands the actual writing to `capture-rule`.

## When to use

- On a cadence (before a release, every N PRs) — not after a single review.
- A reviewer (human or the `code-review` skill) keeps raising the same class of issue.
- "What should we codify from our reviews?"

Skip it for a one-off finding — that's a single review comment, not a rule.

## Method

1. **Get the coarse signal.** Run `specced stats`. Read `candidates.rules_from_reviews`
   (review dimensions that produced findings citing *no* rule — recurring and un-encoded),
   plus `review_dimensions.fired` and `rules.dead`.
2. **Pull the real findings.** For each candidate dimension, gather the actual
   `Specced-Review:` findings behind it — from PR review comments, commit trailers, or a
   fresh `code-review` run. The trailer says *which* dimension fired; the finding text
   says *what* was wrong.
3. **Cluster into principles.** Group findings that are the same underlying mistake. A
   cluster earns a rule only if it is **recurring** (≥2 distinct instances) and **general**
   (it will happen again). Capture the principle, not the instance.
4. **Write it via `capture-rule`.** For each durable cluster, state a one-line,
   reviewer-checkable rule in the narrowest correct home (usually
   `.claude/rules/<track>/*.md`; `CONSTITUTION.md` only for a hard invariant). Add a
   good/bad example from a real finding and cross-link the dimension that keeps catching
   it. If a near-duplicate rule exists, **sharpen it** instead of adding one.
5. **Prune the dead.** A rule in `rules.dead` that never fires and is never cited may be
   obsolete — flag it for merge/deletion (confirm with the user; don't auto-delete).
6. **Confirm the loop closed.** Re-run `specced stats`; the candidate's
   `reviews_without_rule` count should stop climbing, because the rule now catches the
   issue *before* review.

## Guardrails

- No rule from a single finding — recurrence is the bar.
- One cluster → one home; cross-link, don't duplicate.
- The rule must be checkable by a reviewer, or it can't reduce future findings.
- This skill never edits product code; it only authors guidance.

> A good pass means the dimensions that fired most now cite rules — the review's recurring
> lessons are written down, not re-discovered each PR.
