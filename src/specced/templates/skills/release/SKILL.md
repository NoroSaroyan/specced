---
name: release
description: Use when cutting a release, tagging a version, or publishing a package/image/binary of any ecosystem — pick the version per SemVer from the actual changes, ship from a green commit with an updated changelog, tag and build reproducibly, then smoke-check. Never include secrets or AI attribution.
---

# Cut a release

A release is a **promise about a specific commit**: this tree, at this version, behaves as the changelog says and the public surface as `CONSTITUTION.md` allows. Everything below makes that promise checkable. The release is reproducible from the tag alone; nothing is hand-massaged after the build.

## Before you cut

Read, in order:

1. `.claude/rules/<track>/release.md` (or the nearest release/versioning rule) — where the version string lives, the changelog format, the tag scheme, the build + publish commands, and any signing/provenance step. Match it exactly.
2. `CONSTITUTION.md` — the SemVer/backward-compatibility policy for the public surface, the deprecation window, and the secrets/attribution boundary.

> TODO(specced): Name the canonical version location (e.g. a manifest field, a `VERSION` file, a tag-derived scheme), the changelog file, the tag format, and the build/publish/sign commands. Examples this covers: language package registries, container images, OS packages, prebuilt binaries.

## Choose the version (SemVer, from the actual changes)

Diff the public surface since the last tag and let the **changes** pick the bump — not habit:

| Change since last release | Bump |
|---|---|
| Breaking change to the public surface (removed/renamed/incompatible) | **major** |
| Backward-compatible new capability | **minor** |
| Backward-compatible bug fix / internal-only change | **patch** |

`0.x` and pre-release/build suffixes follow `CONSTITUTION.md`. A breaking change requires either a major bump **or** an explicit ADR-backed exception in `CONSTITUTION.md` — never a silent compat break.

## Procedure

1. **Pin the release commit and prove it green.** Choose the exact commit to ship; `make verify` MUST pass on *that* commit with a clean tree — no uncommitted changes, no "fix later".
   > TODO(specced): `git status --porcelain` (empty) and `make verify`
2. **Update the changelog from merged commits/PRs + ADRs.** Move the unreleased section under the new version + date; entries derive from what actually merged since the last tag and reference any ADRs in `docs/decisions/**`. No secrets, no internal-only noise, no AI attribution.
3. **Bump the version in the canonical place.** Edit the single source-of-truth version string to the chosen value; do not duplicate it across files.
   > TODO(specced): name the file/field and its bump command, if any.
4. **Regen clients iff the public surface changed.** If the public API/contract surface changed, regenerate downstream artifacts via the `regen-client` skill and confirm the bump honors the backward-compat policy in `CONSTITUTION.md`. A no-surface-change release skips this.
5. **Vet any new release/publish tooling** with the `sonatype-guide` skill before adding it (supply-chain risk applies doubly to what you ship).
6. **Commit, then tag the exact commit.** Commit the version + changelog, then create the tag on it per the repo's tag scheme. Sign if the rules require it. The commit message and tag carry **no AI attribution**.
   > TODO(specced): `git tag <scheme>` (annotated/signed per rules).
7. **Build artifacts reproducibly.** Build from the tagged tree via the committed command — pinned toolchain, no ad-hoc flags — so the same tag yields the same artifact.
   > TODO(specced): `make build` / the release-artifact target.
8. **Publish.** Push the tag and publish the artifacts via the committed command. Credentials come from the environment/CI secret store — never hardcoded, logged, or committed.
   > TODO(specced): `git push --tags` and the publish target.
9. **Post-release smoke checks.** Install/pull the published artifact from a clean environment and confirm it runs and reports the new version.
   > TODO(specced): the clean-install + `--version` (or equivalent) check.

## Acceptance criteria (runnable)

Express each as an independently-checkable criterion backed by a command:

- `make verify` is green on the **exact** release commit, tree clean. `TODO(specced): git status --porcelain && make verify`
- Version bump matches the SemVer class of the diff; changelog has a dated entry for it. `TODO(specced): the version-vs-changelog check`
- Public-surface change ⇒ clients regenerated with **no drift**; bump honors `CONSTITUTION.md` compat policy. `TODO(specced): make gen && git diff --exit-code`
- Tag points at the release commit; artifact builds reproducibly from the tag. `TODO(specced): make build`
- No secret or AI-attribution string in the commit, tag, changelog, or artifact.
- Post-release smoke check passes: clean install reports the new version. `TODO(specced): the smoke check`

## Proof loop

Drive it to green via `repo-task-proof-loop`: `freeze` `.agent/tasks/<TASK_ID>/spec.md` with the AC block as runnable `AC1..ACn`, keeping "verify green on the exact commit", "version matches the SemVer diff + changelog", and "no-drift regen iff surface changed" as **separate**, independently-verifiable criteria. `build` the version bump + changelog (+ regen if the surface changed); `evidence` → `verify` (fresh) → `fix` until `PASS`. Tag, build, and publish only after every AC is green. Not done until the green-commit AC, the SemVer/changelog AC, and the post-release smoke AC all pass.
