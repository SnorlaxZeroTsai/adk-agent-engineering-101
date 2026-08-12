#!/usr/bin/env python3
"""Render deterministic Lab 05 evidence as JSON."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
import sys


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT))

from rag_lab.domain import DELETED_PROMOTION_CASE  # noqa: E402
from rag_lab.domain import QUERY_CASES  # noqa: E402
from rag_lab.domain import query_case  # noqa: E402
from rag_lab.runtime import build_deletion_lag_index  # noqa: E402
from rag_lab.runtime import build_stale_index  # noqa: E402
from rag_lab.runtime import run_explicit_vector  # noqa: E402
from rag_lab.runtime import run_managed_search  # noqa: E402
from rag_lab.runtime import summarize_result  # noqa: E402


async def main() -> None:
    baselines: dict[str, dict[str, object]] = {}
    for case in QUERY_CASES:
        baselines[case.case_id] = {
            "managed": summarize_result(await run_managed_search(case)),
            "explicit": summarize_result(await run_explicit_vector(case)),
        }

    breaks = {
        "unfiltered_managed_search": summarize_result(
            await run_managed_search(
                query_case("public-reset"),
                enforce_principal_filter=False,
            )
        ),
        "missing_provenance": summarize_result(
            await run_explicit_vector(
                query_case("current-payload"),
                include_provenance=False,
            )
        ),
        "stale_version": summarize_result(
            await run_explicit_vector(
                query_case("current-payload"),
                index=build_stale_index(),
            )
        ),
        "deletion_lag": summarize_result(
            await run_explicit_vector(
                DELETED_PROMOTION_CASE,
                index=build_deletion_lag_index(),
            )
        ),
    }
    print(
        json.dumps(
            {
                "baselines": baselines,
                "breakages": breaks,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
