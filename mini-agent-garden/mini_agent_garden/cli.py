"""JSON CLI for local Agent Garden discovery and project lifecycle."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any
from typing import Callable

from .errors import GardenError
from .service import MiniAgentGarden
from .service import find_repository_root


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mini-agent-garden")
    parser.add_argument(
        "--repository",
        type=Path,
        default=None,
        help="learning repository root",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    list_command = commands.add_parser("list")
    list_command.add_argument("--architecture")
    list_command.add_argument("--tag")

    inspect_command = commands.add_parser("inspect")
    inspect_command.add_argument("blueprint")

    validate_command = commands.add_parser("validate")
    validate_command.add_argument("blueprint")

    create_command = commands.add_parser("create")
    create_command.add_argument("blueprint")
    create_command.add_argument("output", type=Path)

    test_command = commands.add_parser("test")
    test_command.add_argument("project", type=Path)

    upgrade_command = commands.add_parser("upgrade")
    upgrade_command.add_argument("project", type=Path)
    upgrade_command.add_argument("blueprint")
    upgrade_command.add_argument("--apply", action="store_true")
    upgrade_command.add_argument(
        "--accept-review",
        action="store_true",
    )
    return parser


def _emit(value: dict[str, Any], stream: Any | None = None) -> None:
    target = stream if stream is not None else sys.stdout
    print(json.dumps(value, indent=2, sort_keys=True), file=target)


GardenFactory = Callable[[Path], MiniAgentGarden]


def main(
    argv: list[str] | None = None,
    *,
    garden_factory: GardenFactory = MiniAgentGarden,
) -> int:
    args = _parser().parse_args(argv)
    try:
        repository = (
            args.repository.resolve()
            if args.repository is not None
            else find_repository_root()
        )
        garden = garden_factory(repository)
        if args.command == "list":
            result = garden.list(
                architecture=args.architecture,
                tag=args.tag,
            )
        elif args.command == "inspect":
            result = garden.inspect(args.blueprint)
        elif args.command == "validate":
            result = garden.validate(args.blueprint)
            _emit(result)
            return 0 if result["passed"] else 1
        elif args.command == "create":
            result = garden.create(args.blueprint, args.output)
        elif args.command == "test":
            result = garden.test(args.project)
            _emit(result)
            return 0 if result["passed"] else 1
        elif args.command == "upgrade":
            result = garden.upgrade(
                args.project,
                args.blueprint,
                apply=args.apply,
                accept_review=args.accept_review,
            )
        else:
            raise GardenError(f"unsupported command: {args.command}")
        _emit(result)
        return 0
    except (GardenError, OSError, ValueError) as error:
        _emit(
            {
                "error": type(error).__name__,
                "message": str(error),
            },
            sys.stderr,
        )
        return 2
