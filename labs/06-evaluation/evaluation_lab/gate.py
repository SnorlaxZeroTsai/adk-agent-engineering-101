"""High-level cross-phase evaluation gate."""

from __future__ import annotations

from .contracts import SuiteReport
from .cross_lab import collect_trace_set
from .dataset import build_dataset
from .engine import grade_trace_set
from .metrics import default_metric_policies


async def evaluate_variant(variant: str) -> SuiteReport:
    """Generate traces, grade them and return the CI verdict."""

    dataset = build_dataset()
    traces = await collect_trace_set(variant)
    return grade_trace_set(
        dataset,
        traces,
        default_metric_policies(),
    )


def exit_code(report: SuiteReport) -> int:
    """Map the release verdict to a process exit status."""

    return 0 if report.passed else 1
