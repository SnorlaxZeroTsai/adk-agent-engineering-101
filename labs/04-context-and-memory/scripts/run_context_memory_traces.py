#!/usr/bin/env python3
"""Render deterministic Lab 04 evidence as JSON."""

from __future__ import annotations

import asyncio
from dataclasses import asdict
import json
import logging
from pathlib import Path
import sys
import warnings


LAB_ROOT = Path(__file__).resolve().parents[1]
if str(LAB_ROOT) not in sys.path:
    sys.path.insert(0, str(LAB_ROOT))

from context_memory_lab.runtime import run_artifact_scope_trace
from context_memory_lab.runtime import run_baseline_comparison
from context_memory_lab.runtime import run_large_context_comparison
from context_memory_lab.runtime import run_leaky_memory_trace
from context_memory_lab.runtime import run_memory_lifecycle_trace
from context_memory_lab.runtime import run_state_context
from context_memory_lab.runtime import run_state_scope_trace
from context_memory_lab.runtime import summarize_result


logging.getLogger("google_adk").setLevel(logging.CRITICAL)
warnings.filterwarnings(
    "ignore",
    message=r".*JSON_SCHEMA_FOR_FUNC_DECL.*",
)


async def main() -> None:
    baselines = await run_baseline_comparison()
    large = await run_large_context_comparison()
    evidence = {
        "baselines": {
            name: summarize_result(result)
            for name, result in baselines.items()
        },
        "stale_state": summarize_result(
            await run_state_context(stale_second_turn=True)
        ),
        "large_context": {
            name: summarize_result(result)
            for name, result in large.items()
        },
        "state_scopes": asdict(await run_state_scope_trace()),
        "artifact_scopes": asdict(await run_artifact_scope_trace()),
        "memory_lifecycle": asdict(await run_memory_lifecycle_trace()),
        "leaky_memory_adapter": summarize_result(
            await run_leaky_memory_trace()
        ),
    }
    print(json.dumps(evidence, indent=2, sort_keys=True))


if __name__ == "__main__":
    asyncio.run(main())
