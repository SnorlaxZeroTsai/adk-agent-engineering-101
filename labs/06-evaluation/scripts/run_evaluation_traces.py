#!/usr/bin/env python3
"""Render dataset, traces and grades as a deterministic evidence bundle."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
import sys


LAB_ROOT = Path(__file__).resolve().parents[1]
if str(LAB_ROOT) not in sys.path:
    sys.path.insert(0, str(LAB_ROOT))

from evaluation_lab.cross_lab import collect_trace_set  # noqa: E402
from evaluation_lab.dataset import build_dataset  # noqa: E402
from evaluation_lab.engine import grade_trace_set  # noqa: E402
from evaluation_lab.metrics import default_metric_policies  # noqa: E402


async def main() -> None:
    dataset = build_dataset()
    policies = default_metric_policies()
    baseline_traces = await collect_trace_set("baseline")
    broken_traces = await collect_trace_set("broken")
    baseline_grade = grade_trace_set(
        dataset,
        baseline_traces,
        policies,
    )
    broken_grade = grade_trace_set(
        dataset,
        broken_traces,
        policies,
    )
    print(
        json.dumps(
            {
                "dataset": dataset.as_dict(),
                "traces": {
                    "baseline": baseline_traces.as_dict(),
                    "broken": broken_traces.as_dict(),
                },
                "grade_results": {
                    "baseline": baseline_grade.as_dict(),
                    "broken": broken_grade.as_dict(),
                },
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
