#!/usr/bin/env python3
"""Render every Lab 02 experiment as stable JSON."""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
import sys
import warnings


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from workflow_lab.runtime import run_baseline_comparison
from workflow_lab.runtime import run_duplicate_output_comparison
from workflow_lab.runtime import run_graph_resume_trace
from workflow_lab.runtime import run_legacy_resume_trace
from workflow_lab.runtime import run_loop_limit_comparison
from workflow_lab.runtime import run_missing_state_trace
from workflow_lab.runtime import run_retry_comparison
from workflow_lab.runtime import summarize_resume
from workflow_lab.runtime import summarize_run


logging.getLogger("google_adk").setLevel(logging.CRITICAL)
warnings.filterwarnings(
    "ignore",
    message=r"\[EXPERIMENTAL\] feature AGENT_STATE.*",
)


async def main() -> None:
    baseline = await run_baseline_comparison()
    loop_limit = await run_loop_limit_comparison()
    retry = await run_retry_comparison()
    duplicate = await run_duplicate_output_comparison()
    missing_state = await run_missing_state_trace()
    graph_resume = await run_graph_resume_trace()
    legacy_resume = await run_legacy_resume_trace()

    evidence = {
        "baseline": {
            key: summarize_run(value) for key, value in baseline.items()
        },
        "loop_limit": {
            key: summarize_run(value) for key, value in loop_limit.items()
        },
        "retry": {
            key: summarize_run(value) for key, value in retry.items()
        },
        "duplicate_output": {
            key: summarize_run(value) for key, value in duplicate.items()
        },
        "missing_state": summarize_run(missing_state),
        "graph_resume": summarize_resume(graph_resume),
        "legacy_resume": summarize_resume(legacy_resume),
    }
    print(json.dumps(evidence, indent=2, sort_keys=True))


if __name__ == "__main__":
    asyncio.run(main())
