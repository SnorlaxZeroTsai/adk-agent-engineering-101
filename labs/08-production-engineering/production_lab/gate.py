"""Production suite aggregation and process exit semantics."""

from __future__ import annotations

from .contracts import ProductionSuiteReport
from .contracts import ScenarioReport


def build_suite(
    variant: str,
    scenarios: tuple[ScenarioReport, ...],
) -> ProductionSuiteReport:
    failures = tuple(
        f"{scenario.scenario_id}:{issue.code}:{issue.path}"
        for scenario in scenarios
        for issue in scenario.issues
    )
    return ProductionSuiteReport(
        variant=variant,
        passed=all(item.passed for item in scenarios),
        scenarios=scenarios,
        blocking_failures=failures,
    )


def exit_code(report: ProductionSuiteReport) -> int:
    return 0 if report.passed else 1
