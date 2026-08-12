#!/usr/bin/env python3
"""Run the valid or deliberately broken pattern catalog gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


LAB_ROOT = Path(__file__).resolve().parents[1]
if str(LAB_ROOT) not in sys.path:
    sys.path.insert(0, str(LAB_ROOT))

from pattern_catalog.gate import build_gate_report
from pattern_catalog.gate import exit_code


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--variant",
        choices=("baseline", "broken"),
        default="baseline",
    )
    args = parser.parse_args()
    report = build_gate_report(args.variant)
    print(json.dumps(report, indent=2, sort_keys=True))
    return exit_code(report)


if __name__ == "__main__":
    raise SystemExit(main())
