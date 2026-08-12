#!/usr/bin/env python3
"""Render deterministic source-coverage and misleading-entry evidence."""

from __future__ import annotations

import json
from pathlib import Path
import sys


LAB_ROOT = Path(__file__).resolve().parents[1]
if str(LAB_ROOT) not in sys.path:
    sys.path.insert(0, str(LAB_ROOT))

from garden_discovery.gate import build_gate_report


def main() -> None:
    bundle = {
        "baseline": build_gate_report("baseline"),
        "broken": build_gate_report("broken"),
    }
    print(json.dumps(bundle, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
