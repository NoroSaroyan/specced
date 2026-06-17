"""Tests for `specced stats` — read-only mining of the usage signal."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from specced import scaffold, stats

_GIT = ("git", "-c", "user.email=t@example.com", "-c", "user.name=t")


def _write_task(
    repo: Path, task_id: str, verdict: str, artifacts: list[str], changed: list[str]
) -> None:
    task = repo / ".agent" / "tasks" / task_id
    task.mkdir(parents=True, exist_ok=True)
    (task / "verdict.json").write_text(
        json.dumps(
            {
                "task_id": task_id,
                "overall_verdict": verdict,
                "criteria": [],
                "commands_run": ["make verify"],
                "artifacts_used": artifacts,
            }
        ),
        encoding="utf-8",
    )
    (task / "evidence.json").write_text(
        json.dumps(
            {
                "task_id": task_id,
                "overall_status": verdict,
                "acceptance_criteria": [],
                "changed_files": changed,
                "commands_for_fresh_verifier": [],
                "known_gaps": [],
            }
        ),
        encoding="utf-8",
    )


def test_stats_mines_proof_loop_records(repo: Path) -> None:
    scaffold.init_repo(repo, preset="go")  # rules: go/{conventions,errors,testing}.md; dims 01-04
    _write_task(
        repo,
        "t1",
        "PASS",
        [".claude/rules/go/errors.md", ".claude/code-review/01-correctness.md", "CONSTITUTION.md"],
        ["internal/auth/acl.go"],
    )
    _write_task(repo, "t2", "FAIL", [], ["internal/auth/acl.go"])

    s = stats.compute(repo)
    assert s["signal_present"] is True
    assert s["gate_health"]["proof_loop"]["PASS"] == 1
    assert s["gate_health"]["proof_loop"]["FAIL"] == 1
    assert s["rules"]["cited"].get("go/errors.md") == 1
    assert "go/errors.md" not in s["rules"]["dead"]
    assert "go/testing.md" in s["rules"]["dead"]  # present, never cited
    assert s["rules"]["phantom"] == []  # the dim citation is not miscounted as a rule
    assert s["review_dimensions"]["fired"].get("01-correctness") == 1
    assert "02-api" in s["review_dimensions"]["never_fired"]
    assert s["reviews"]["constitution_citations"] == 1
    assert s["hotspots"][0]["path"] == "internal/auth/acl.go"
    assert s["hotspots"][0]["changes"] == 2


def test_stats_mines_git_trailers(repo: Path) -> None:
    scaffold.init_repo(repo, preset="go")
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(
        [
            *_GIT,
            "commit",
            "-q",
            "-m",
            "feat: thing\n\nSpecced-Review: verdict=block dims=01-correctness,03-concurrency "
            "rules=go/errors.md cites=CONSTITUTION§2",
        ],
        cwd=repo,
        check=True,
    )
    subprocess.run(
        [
            *_GIT,
            "commit",
            "-q",
            "--allow-empty",
            "-m",
            "chore: rule\n\nSpecced-Rule: created .claude/rules/go/errors.md",
        ],
        cwd=repo,
        check=True,
    )

    s = stats.compute(repo)
    assert s["reviews"]["total"] == 1
    assert s["reviews"]["verdicts"].get("block") == 1
    assert s["rules"]["cited"].get("go/errors.md") == 1  # from the review trailer
    assert "01-correctness" in s["review_dimensions"]["fired"]
    assert "03-concurrency" in s["review_dimensions"]["fired"]
    assert any(rc["action"] == "created" for rc in s["rules"]["created"])


def test_stats_empty_repo_frames_no_signal(repo: Path) -> None:
    scaffold.init_repo(repo, preset="go")  # rules exist but nothing uses them yet
    s = stats.compute(repo)
    assert s["signal_present"] is False
    assert s["sources"]["proof_loop_tasks"] == 0
    assert len(s["rules"]["dead"]) == s["rules"]["total"]  # all uncited
    assert any("no usage signal yet" in line for line in s["summary"])
    # git/ci unavailable is reported, not fatal
    assert isinstance(s["notes"], list)


def test_stats_surfaces_rule_candidates(repo: Path) -> None:
    scaffold.init_repo(repo, preset="go")
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    # two reviews flagging 03-concurrency with NO rule cited -> a recurring, un-encoded finding
    for i in range(2):
        subprocess.run(
            [
                *_GIT,
                "commit",
                "-q",
                "--allow-empty",
                "-m",
                f"fix {i}\n\nSpecced-Review: verdict=block dims=03-concurrency",
            ],
            cwd=repo,
            check=True,
        )
    cands = stats.compute(repo)["candidates"]["rules_from_reviews"]
    assert any(c["dimension"] == "03-concurrency" and c["reviews_without_rule"] == 2 for c in cands)
