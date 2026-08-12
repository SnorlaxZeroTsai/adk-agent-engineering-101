#!/usr/bin/env python3
"""Render deterministic component and lifecycle evidence."""

from __future__ import annotations

import json
from pathlib import Path
import sys


LAB_ROOT = Path(__file__).resolve().parents[1]
if str(LAB_ROOT) not in sys.path:
    sys.path.insert(0, str(LAB_ROOT))

from architecture_lab.gate import build_gate_report


def main() -> None:
    evidence = {
        "baseline": build_gate_report("baseline"),
        "broken": build_gate_report("broken"),
    }
    print(json.dumps(evidence, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
