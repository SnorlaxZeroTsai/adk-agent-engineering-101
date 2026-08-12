#!/usr/bin/env python3
"""Render deterministic production topology and rollback evidence."""

from __future__ import annotations

import json
from pathlib import Path
import sys


LAB_ROOT = Path(__file__).resolve().parents[1]
if str(LAB_ROOT) not in sys.path:
    sys.path.insert(0, str(LAB_ROOT))

from production_lab.fixtures import build_evidence_bundle  # noqa: E402


def main() -> None:
    print(
        json.dumps(
            build_evidence_bundle(),
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
