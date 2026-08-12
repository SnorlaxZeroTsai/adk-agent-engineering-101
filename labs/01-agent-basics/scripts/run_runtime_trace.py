#!/usr/bin/env python3
"""Run deterministic ADK success and failure traces without cloud access."""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
import sys
import warnings


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent_basics.runtime_trace import run_callback_failure_trace  # noqa: E402
from agent_basics.runtime_trace import run_success_trace  # noqa: E402
from agent_basics.runtime_trace import run_tool_failure_trace  # noqa: E402
from agent_basics.runtime_trace import summarize_trace  # noqa: E402


async def main() -> None:
    logging.getLogger("google_adk").setLevel(logging.CRITICAL)
    warnings.filterwarnings(
        "ignore",
        message=r".*JSON_SCHEMA_FOR_FUNC_DECL.*",
    )
    traces = {
        "success": summarize_trace(await run_success_trace()),
        "continued_session": summarize_trace(
            await run_success_trace(continue_session=True)
        ),
        "unhandled_tool_failure": summarize_trace(
            await run_tool_failure_trace(recover=False)
        ),
        "recovered_tool_failure": summarize_trace(
            await run_tool_failure_trace(recover=True)
        ),
        "callback_failure": summarize_trace(
            await run_callback_failure_trace()
        ),
    }
    print(json.dumps(traces, indent=2, sort_keys=True))


if __name__ == "__main__":
    asyncio.run(main())
