#!/usr/bin/env python3
"""Render deterministic Lab 03 evidence as JSON."""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
import sys
import warnings


LAB_ROOT = Path(__file__).resolve().parents[1]
if str(LAB_ROOT) not in sys.path:
    sys.path.insert(0, str(LAB_ROOT))

from multi_agent_lab.runtime import run_baseline_comparison
from multi_agent_lab.runtime import run_overlap_trace
from multi_agent_lab.runtime import run_shared_state_conflict
from multi_agent_lab.runtime import run_task_hard_failure
from multi_agent_lab.runtime import run_task_validation_recovery
from multi_agent_lab.runtime import run_transfer_continuation
from multi_agent_lab.runtime import summarize_result


logging.getLogger("google_adk").setLevel(logging.CRITICAL)
warnings.filterwarnings(
    "ignore",
    message=r".*JSON_SCHEMA_FOR_FUNC_DECL.*",
)


async def main() -> None:
    baselines = await run_baseline_comparison()
    evidence = {
        "baselines": {
            name: summarize_result(result)
            for name, result in baselines.items()
        },
        "transfer_continuation": summarize_result(
            await run_transfer_continuation()
        ),
        "task_validation_recovery": summarize_result(
            await run_task_validation_recovery()
        ),
        "task_hard_failure": summarize_result(
            await run_task_hard_failure()
        ),
        "overlapping_responsibility": summarize_result(
            await run_overlap_trace()
        ),
        "shared_state_conflict": summarize_result(
            await run_shared_state_conflict()
        ),
    }
    print(json.dumps(evidence, indent=2, sort_keys=True))


if __name__ == "__main__":
    asyncio.run(main())
