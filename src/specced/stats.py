"""Read-only mining of the specced signal: how the installed setup is actually used.

``specced stats`` answers the questions the self-improving loop needs — which rules and
review dimensions actually get cited, and is the gate passing — by reading three signal
sources, all best-effort (a missing source is reported in ``notes``, never fatal):

1. Proof-loop task records the engine already writes: ``.agent/tasks/*/verdict.json``
   (gate PASS/FAIL, ``artifacts_used``) and ``evidence.json`` (``changed_files``).
2. Git-history trailers emitted by the ``code-review`` and ``capture-rule`` skills:
   ``Specced-Review:`` / ``Specced-Rule:`` (grammar in docs/proposals/ci-gate-and-signal.md).
3. GitHub Actions runs of the specced gate, via ``gh run list`` (if gh + a remote exist).

Stdlib + git/gh only, mirroring detect.py: deterministic, no third-party deps. Read-only —
it never writes to the repo.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

from . import scaffold

RULES_REL = (".claude", "rules")
DIMS_REL = (".claude", "code-review")
_SKIP_FILES = {"README.md", "_template.md"}

_TRAILER_RE = re.compile(r"^\s*Specced-(Review|Rule):\s*(.*)$", re.MULTILINE)


# --------------------------------------------------------------------------- #
# Small helpers
# --------------------------------------------------------------------------- #
def _run(cmd: list[str], cwd: Path) -> tuple[int, str]:
    try:
        r = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, timeout=20)
        return r.returncode, r.stdout
    except Exception:
        return 1, ""


def _rule_inventory(repo_root: Path) -> list[str]:
    """Rule files present, keyed by path relative to .claude/rules/ (e.g. go/errors.md)."""
    base = repo_root / Path(*RULES_REL)
    if not base.is_dir():
        return []
    return sorted(
        str(p.relative_to(base)).replace("\\", "/")
        for p in base.rglob("*.md")
        if p.name not in _SKIP_FILES
    )


def _dim_inventory(repo_root: Path) -> list[str]:
    """Review-dimension files present, keyed by stem (e.g. 01-correctness)."""
    base = repo_root / Path(*DIMS_REL)
    if not base.is_dir():
        return []
    return sorted(p.stem for p in base.glob("*.md") if p.name not in _SKIP_FILES)


def _norm_rule(token: str) -> str | None:
    """Normalize a rule citation to its path relative to .claude/rules/, or None.

    Rejects review-dimension citations (``.claude/code-review/...`` or an ``NN-slug``
    basename) so a dimension isn't double-counted as a phantom rule."""
    t = token.strip().strip(",").replace("\\", "/")
    if ".claude/code-review/" in t:
        return None
    if ".claude/rules/" in t:
        t = t.split(".claude/rules/", 1)[1]
    base = t.rsplit("/", 1)[-1]
    if re.match(r"^\d{2}[-_]", base):  # NN-slug basename -> a dimension, not a rule
        return None
    return t if (t.endswith(".md") and "/" in t) else None


def _norm_dim(token: str) -> str | None:
    """Normalize a review-dimension citation to its NN-slug stem, or None."""
    t = token.strip().strip(",").replace("\\", "/")
    if ".claude/code-review/" in t:
        t = t.split(".claude/code-review/", 1)[1]
    t = t.rsplit("/", 1)[-1]
    if t.endswith(".md"):
        t = t[:-3]
    return t if re.match(r"^\d{2}[-_]", t) else None


def _tally(token: str, rule_cites: dict[str, int], dim_cites: dict[str, int]) -> None:
    r = _norm_rule(token)
    if r:
        rule_cites[r] = rule_cites.get(r, 0) + 1
    d = _norm_dim(token)
    if d:
        dim_cites[d] = dim_cites.get(d, 0) + 1


# --------------------------------------------------------------------------- #
# Source readers
# --------------------------------------------------------------------------- #
def _read_proof_loop(repo_root: Path) -> dict[str, Any]:
    tasks_dir = repo_root / ".agent" / "tasks"
    verdicts: dict[str, int] = {"PASS": 0, "FAIL": 0, "UNKNOWN": 0}
    rule_cites: dict[str, int] = {}
    dim_cites: dict[str, int] = {}
    changed: dict[str, int] = {}
    constitution = 0
    task_count = 0
    if tasks_dir.is_dir():
        for vpath in sorted(tasks_dir.glob("*/verdict.json")):
            try:
                v = json.loads(vpath.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            task_count += 1
            verdicts[v.get("overall_verdict", "UNKNOWN")] = (
                verdicts.get(v.get("overall_verdict", "UNKNOWN"), 0) + 1
            )
            for art in v.get("artifacts_used") or []:
                _tally(str(art), rule_cites, dim_cites)
                if "CONSTITUTION" in str(art):
                    constitution += 1
            ev = vpath.parent / "evidence.json"
            if ev.exists():
                try:
                    e = json.loads(ev.read_text(encoding="utf-8"))
                    for f in e.get("changed_files") or []:
                        changed[f] = changed.get(f, 0) + 1
                except (OSError, json.JSONDecodeError):
                    pass
    return {
        "task_count": task_count,
        "verdicts": verdicts,
        "rule_cites": rule_cites,
        "dim_cites": dim_cites,
        "changed": changed,
        "constitution": constitution,
    }


def _parse_review(rest: str) -> dict[str, Any]:
    out: dict[str, Any] = {"verdict": None, "dims": [], "rules": [], "cites": []}
    for tok in rest.split():
        key, sep, val = tok.partition("=")
        if not sep:
            continue
        vals = [v for v in val.split(",") if v]
        if key == "verdict":
            out["verdict"] = val or None
        elif key == "dims":
            out["dims"] = [_norm_dim(v) or v for v in vals]
        elif key == "rules":
            out["rules"] = [_norm_rule(v) or v for v in vals]
        elif key == "cites":
            out["cites"] = vals
    return out


def _parse_rule(rest: str) -> dict[str, str] | None:
    m = re.match(r"(created|sharpened)\s+(\S+)", rest.strip())
    return {"action": m.group(1), "home": m.group(2)} if m else None


def _read_git_trailers(repo_root: Path) -> dict[str, Any]:
    if not (repo_root / ".git").exists():
        return {"available": False, "note": "not a git repo", "reviews": [], "rules_created": []}
    code, out = _run(["git", "log", "--no-merges", "--format=%B"], repo_root)
    if code != 0:
        return {"available": False, "note": "git log failed", "reviews": [], "rules_created": []}
    reviews: list[dict[str, Any]] = []
    rules_created: list[dict[str, str]] = []
    for kind, rest in _TRAILER_RE.findall(out):
        if kind == "Review":
            reviews.append(_parse_review(rest))
        else:
            parsed = _parse_rule(rest)
            if parsed:
                rules_created.append(parsed)
    return {"available": True, "reviews": reviews, "rules_created": rules_created}


def _read_ci_runs(repo_root: Path) -> dict[str, Any]:
    workflow = scaffold.CI_GATE_REL[-1]
    if _run(["gh", "--version"], repo_root)[0] != 0:
        return {"available": False, "note": "gh CLI not found — CI gate history unavailable"}
    code, out = _run(
        ["gh", "run", "list", "--workflow", workflow, "--limit", "100", "--json", "conclusion"],
        repo_root,
    )
    if code != 0 or not out.strip():
        return {
            "available": False,
            "note": f"no gh runs for {workflow} (not authenticated, no remote, or gate not pushed yet)",
        }
    try:
        runs = json.loads(out)
    except json.JSONDecodeError:
        return {"available": False, "note": "could not parse gh output"}
    tally: dict[str, int] = {}
    for r in runs:
        tally[r.get("conclusion") or "pending"] = tally.get(r.get("conclusion") or "pending", 0) + 1
    total = sum(tally.values())
    return {
        "available": True,
        "total": total,
        "conclusions": tally,
        "pass_rate": round(tally.get("success", 0) / total, 3) if total else None,
    }


# --------------------------------------------------------------------------- #
# Public
# --------------------------------------------------------------------------- #
def compute(repo_root: Path) -> dict[str, Any]:
    proof = _read_proof_loop(repo_root)
    git = _read_git_trailers(repo_root)
    ci = _read_ci_runs(repo_root)

    rules_inv = _rule_inventory(repo_root)
    dims_inv = _dim_inventory(repo_root)

    rule_counts = dict(proof["rule_cites"])
    dim_counts = dict(proof["dim_cites"])
    constitution = proof["constitution"]
    verdict_tally: dict[str, int] = {}
    for rv in git.get("reviews", []):
        if rv["verdict"]:
            verdict_tally[rv["verdict"]] = verdict_tally.get(rv["verdict"], 0) + 1
        for d in rv["dims"]:
            dim_counts[d] = dim_counts.get(d, 0) + 1
        for r in rv["rules"]:
            rule_counts[r] = rule_counts.get(r, 0) + 1
        constitution += len(rv["cites"])

    dead_rules = [r for r in rules_inv if r not in rule_counts]
    phantom_rules = sorted(r for r in rule_counts if r not in rules_inv)
    never_fired = [d for d in dims_inv if d not in dim_counts]

    # Candidates for the loop's write side (the learn-from-review skill consumes these):
    # a dimension that produced findings (block / approve-nits) citing NO rule is a
    # recurring lesson not yet encoded. Threshold 2 = recurring, not a one-off.
    unencoded: dict[str, int] = {}
    for rv in git.get("reviews", []):
        if rv["verdict"] in ("block", "approve-nits") and not rv["rules"]:
            for d in rv["dims"]:
                unencoded[d] = unencoded.get(d, 0) + 1
    candidate_rules = [
        {
            "dimension": d,
            "reviews_without_rule": c,
            "hint": f"dimension {d} produced findings in {c} review(s) citing no rule — recurring, not yet encoded",
        }
        for d, c in sorted(unencoded.items(), key=lambda kv: (-kv[1], kv[0]))
        if c >= 2
    ]

    n_reviews = len(git.get("reviews", []))
    n_rules_created = len(git.get("rules_created", []))
    signal_present = proof["task_count"] > 0 or n_reviews > 0 or n_rules_created > 0

    tasks = proof["task_count"]
    pass_rate = round(proof["verdicts"]["PASS"] / tasks, 3) if tasks else None

    hotspots = [
        {"path": p, "changes": c}
        for p, c in sorted(proof["changed"].items(), key=lambda kv: (-kv[1], kv[0]))[:10]
    ]

    notes: list[str] = []
    if not git.get("available"):
        notes.append(f"git trailers: {git.get('note')}")
    if not ci.get("available"):
        notes.append(f"ci runs: {ci.get('note')}")

    summary: list[str] = []
    if tasks:
        v = proof["verdicts"]
        summary.append(
            f"proof-loop: {tasks} task(s) — {v['PASS']} PASS / {v['FAIL']} FAIL / "
            f"{v['UNKNOWN']} UNKNOWN ({int((pass_rate or 0) * 100)}% pass)"
        )
    if ci.get("available"):
        summary.append(f"CI gate: {ci['total']} run(s), {int((ci['pass_rate'] or 0) * 100)}% pass")
    if rules_inv:
        cited = len(rules_inv) - len(dead_rules)
        line = f"rules: {cited}/{len(rules_inv)} cited"
        if signal_present and dead_rules:
            shown = ", ".join(dead_rules[:5]) + (" …" if len(dead_rules) > 5 else "")
            line += f"; never referenced: {shown}"
        summary.append(line)
    if dims_inv:
        fired = len(dims_inv) - len(never_fired)
        summary.append(f"review dimensions: {fired}/{len(dims_inv)} fired")
    if phantom_rules:
        summary.append(
            f"{len(phantom_rules)} citation(s) to missing rule file(s): {', '.join(phantom_rules[:5])}"
        )
    if candidate_rules:
        summary.append(
            f"learn-from-review: {len(candidate_rules)} dimension(s) with recurring un-encoded "
            f"findings (top: {candidate_rules[0]['dimension']} ×{candidate_rules[0]['reviews_without_rule']}) "
            "— run the learn-from-review skill"
        )
    if not signal_present:
        summary.append(
            "no usage signal yet — dead-rule analysis needs proof-loop tasks or "
            "code-review/capture-rule trailers in history."
        )

    return {
        "repo_root": str(repo_root),
        "signal_present": signal_present,
        "sources": {
            "proof_loop_tasks": tasks,
            "git_trailers": n_reviews + n_rules_created,
            "ci_runs": ci.get("total") if ci.get("available") else None,
        },
        "notes": notes,
        "gate_health": {
            "proof_loop": {**proof["verdicts"], "pass_rate": pass_rate},
            "ci": ci,
        },
        "rules": {
            "total": len(rules_inv),
            "cited": rule_counts,
            "dead": dead_rules,
            "phantom": phantom_rules,
            "created": git.get("rules_created", []),
        },
        "review_dimensions": {
            "total": len(dims_inv),
            "fired": dim_counts,
            "never_fired": never_fired,
        },
        "reviews": {
            "total": n_reviews,
            "verdicts": verdict_tally,
            "constitution_citations": constitution,
        },
        "candidates": {"rules_from_reviews": candidate_rules},
        "hotspots": hotspots,
        "summary": summary,
    }
