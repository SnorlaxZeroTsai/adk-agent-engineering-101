#!/usr/bin/env python3
"""Run the production-envelope release gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


LAB_ROOT = Path(__file__).resolve().parents[1]
if str(LAB_ROOT) not in sys.path:
    sys.path.insert(0, str(LAB_ROOT))

from production_lab.fixtures import build_baseline_suite  # noqa: E402
from production_lab.fixtures import build_broken_suite  # noqa: E402
from production_lab.gate import exit_code  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--variant",
        choices=("baseline", "broken"),
        required=True,
    )
    args = parser.parse_args()
    report = (
        build_baseline_suite()
        if args.variant == "baseline"
        else build_broken_suite()
    )
    print(json.dumps(report.as_dict(), indent=2, sort_keys=True))
    raise SystemExit(exit_code(report))


if __name__ == "__main__":
    main()
