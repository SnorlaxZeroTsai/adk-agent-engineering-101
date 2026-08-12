#!/usr/bin/env python3
"""Run one cross-phase release gate and return its CI exit status."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
import sys


LAB_ROOT = Path(__file__).resolve().parents[1]
if str(LAB_ROOT) not in sys.path:
    sys.path.insert(0, str(LAB_ROOT))

from evaluation_lab.gate import evaluate_variant  # noqa: E402
from evaluation_lab.gate import exit_code  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--variant",
        choices=("baseline", "broken"),
        required=True,
    )
    return parser.parse_args()


async def main() -> int:
    args = parse_args()
    report = await evaluate_variant(args.variant)
    print(json.dumps(report.as_dict(), indent=2, sort_keys=True))
    return exit_code(report)


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
