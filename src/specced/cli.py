"""specced command-line interface.

Thin wrapper over :mod:`specced.scaffold`. Every command prints a JSON result to
stdout so the interview agent (or a human) can read exactly what happened.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from . import scaffold


def _repo_root(args: argparse.Namespace) -> Path:
    start = Path(args.repo_root).resolve() if args.repo_root else Path.cwd()
    return scaffold.discover_repo_root(start)


def _emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2))


def cmd_init(args: argparse.Namespace) -> int:
    _emit(
        scaffold.init_repo(
            _repo_root(args),
            minimal=args.minimal,
            force=args.force,
            format_cmd=args.format_cmd,
            preset=args.preset,
        )
    )
    return 0


def cmd_detect(args: argparse.Namespace) -> int:
    _emit(scaffold.detect_repo(_repo_root(args)))
    return 0


def cmd_presets(args: argparse.Namespace) -> int:
    _emit({"presets": scaffold.list_presets()})
    return 0


def cmd_add_mcp(args: argparse.Namespace) -> int:
    result = scaffold.compose_mcp(_repo_root(args), args.names, force=args.force)
    _emit(result)
    return 1 if result["unknown"] else 0


def cmd_add_skill(args: argparse.Namespace) -> int:
    result = scaffold.add_skill(_repo_root(args), args.name, force=args.force)
    _emit(result)
    return 0 if result.get("ok") else 1


def cmd_list_skills(args: argparse.Namespace) -> int:
    _emit({"library_skills": scaffold.list_library_skills()})
    return 0


def cmd_sync(args: argparse.Namespace) -> int:
    _emit(scaffold.sync(_repo_root(args)))
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    result = scaffold.doctor(_repo_root(args))
    _emit(result)
    return 0 if result["ok"] else 1


def cmd_status(args: argparse.Namespace) -> int:
    _emit(scaffold.status(_repo_root(args)))
    return 0


def cmd_version(args: argparse.Namespace) -> int:
    _emit({"specced": scaffold.SPECCED_VERSION, "engine": scaffold.engine_version()})
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="specced",
        description="Install and manage the specced agentic coding setup in a repo.",
    )

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--repo-root",
        default=None,
        help="Path inside the target repo. Defaults to the current directory.",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser(
        "init", parents=[common], help="Install the setup into the repo (idempotent)."
    )
    p_init.add_argument(
        "--preset",
        default=None,
        help="Stack preset name, or 'auto' to detect (see: specced presets).",
    )
    p_init.add_argument(
        "--minimal",
        action="store_true",
        help="Install only the engine, agents, managed blocks, and config "
        "(skip Layer-2 content files so the interview can author them).",
    )
    p_init.add_argument("--force", action="store_true", help="Overwrite existing files.")
    p_init.add_argument(
        "--format-cmd",
        default=None,
        help="Format+lint command for the Stop hook (default: 'make fmt lint').",
    )
    p_init.set_defaults(func=cmd_init)

    p_detect = sub.add_parser(
        "detect", parents=[common], help="Inspect the repo and report stack signals (JSON)."
    )
    p_detect.set_defaults(func=cmd_detect)

    p_presets = sub.add_parser("presets", help="List available stack presets.")
    p_presets.set_defaults(func=cmd_presets)

    p_mcp = sub.add_parser(
        "add-mcp", parents=[common], help="Add MCP servers to .mcp.json from the catalog."
    )
    p_mcp.add_argument(
        "names", nargs="+", help="Server names (see 'mcp_catalog' in: specced status)."
    )
    p_mcp.add_argument("--force", action="store_true", help="Overwrite an existing server entry.")
    p_mcp.set_defaults(func=cmd_add_mcp)

    p_add = sub.add_parser(
        "add-skill", parents=[common], help="Install a domain skill from the library."
    )
    p_add.add_argument("name", help="Library skill name (see: specced list-skills).")
    p_add.add_argument("--force", action="store_true", help="Replace if already present.")
    p_add.set_defaults(func=cmd_add_skill)

    p_list = sub.add_parser("list-skills", help="List available library skills.")
    p_list.set_defaults(func=cmd_list_skills)

    p_sync = sub.add_parser(
        "sync",
        parents=[common],
        help="Refresh engine + agents + managed blocks to this specced version.",
    )
    p_sync.set_defaults(func=cmd_sync)

    p_doctor = sub.add_parser("doctor", parents=[common], help="Verify the setup is consistent.")
    p_doctor.set_defaults(func=cmd_doctor)

    p_status = sub.add_parser(
        "status", parents=[common], help="Show installed components and config."
    )
    p_status.set_defaults(func=cmd_status)

    p_version = sub.add_parser("version", help="Print specced and engine versions.")
    p_version.set_defaults(func=cmd_version)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
