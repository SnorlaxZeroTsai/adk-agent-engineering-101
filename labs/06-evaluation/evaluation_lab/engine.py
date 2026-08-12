"""Grade normalized traces with explicit per-case blocking semantics."""

from __future__ import annotations

from statistics import mean

from .contracts import AggregateMetricResult
from .contracts import CaseReport
from .contracts import EvalDataset
from .contracts import MetricPolicy
from .contracts import MetricResult
from .contracts import SuiteReport
from .contracts import TraceSet
from .metrics import EVALUATORS


def _aggregate(
    policy: MetricPolicy,
    results: list[MetricResult],
) -> AggregateMetricResult:
    evaluated = [item for item in results if item.score is not None]
    if not evaluated:
        score = None
        status = "not_evaluated"
    elif policy.aggregation == "mean":
        score = mean(item.score for item in evaluated if item.score is not None)
        status = "passed" if score >= policy.threshold else "failed"
    elif policy.aggregation == "min":
        score = min(item.score for item in evaluated if item.score is not None)
        status = "passed" if score >= policy.threshold else "failed"
    else:
        score = min(item.score for item in evaluated if item.score is not None)
        status = (
            "passed"
            if len(evaluated) == len(results)
            and all(item.status == "passed" for item in evaluated)
            else "failed"
        )
    return AggregateMetricResult(
        metric_name=policy.name,
        kind=policy.kind,
        aggregation=policy.aggregation,
        score=score,
        threshold=policy.threshold,
        status=status,
        blocking=policy.blocking,
        evaluated_case_count=len(evaluated),
    )


def grade_trace_set(
    dataset: EvalDataset,
    trace_set: TraceSet,
    policies: tuple[MetricPolicy, ...],
) -> SuiteReport:
    """Return a release verdict without averaging away critical failures."""

    if trace_set.dataset_id != dataset.dataset_id:
        raise ValueError(
            "trace set references dataset "
            f"{trace_set.dataset_id!r}, expected {dataset.dataset_id!r}"
        )

    policy_by_name = {policy.name: policy for policy in policies}
    if len(policy_by_name) != len(policies):
        raise ValueError("metric policy names must be unique")

    case_by_id = {case.case_id: case for case in dataset.cases}
    observed_by_id = {
        observation.case_id: observation
        for observation in trace_set.observations
    }
    if set(case_by_id) != set(observed_by_id):
        missing = sorted(set(case_by_id) - set(observed_by_id))
        extra = sorted(set(observed_by_id) - set(case_by_id))
        raise ValueError(
            f"trace cases do not match dataset; missing={missing}, extra={extra}"
        )

    case_reports: list[CaseReport] = []
    results_by_metric: dict[str, list[MetricResult]] = {
        policy.name: [] for policy in policies
    }
    failures: list[str] = []
    for case in dataset.cases:
        observed = observed_by_id[case.case_id]
        if observed.phase != case.phase:
            raise ValueError(
                f"{case.case_id}: observed phase {observed.phase!r} does not "
                f"match dataset phase {case.phase!r}"
            )
        metric_results: list[MetricResult] = []
        for metric_name in case.metrics:
            if metric_name not in policy_by_name:
                raise ValueError(
                    f"{case.case_id}: no policy for metric {metric_name!r}"
                )
            if metric_name not in EVALUATORS:
                raise ValueError(
                    f"{case.case_id}: no evaluator for metric {metric_name!r}"
                )
            policy = policy_by_name[metric_name]
            result = EVALUATORS[metric_name](case, observed, policy)
            metric_results.append(result)
            results_by_metric[metric_name].append(result)
            if result.blocking and result.status != "passed":
                detail = "; ".join(result.reasons) or result.status
                failures.append(f"{case.case_id}:{metric_name}: {detail}")
        passed = all(
            not result.blocking or result.status == "passed"
            for result in metric_results
        )
        case_reports.append(
            CaseReport(
                case_id=case.case_id,
                phase=case.phase,
                passed=passed,
                metric_results=tuple(metric_results),
            )
        )

    aggregates = tuple(
        _aggregate(policy, results_by_metric[policy.name])
        for policy in policies
        if results_by_metric[policy.name]
    )
    for aggregate in aggregates:
        if aggregate.blocking and aggregate.status != "passed":
            failures.append(
                f"suite:{aggregate.metric_name}: "
                f"{aggregate.aggregation} aggregation {aggregate.status}"
            )

    return SuiteReport(
        report_id=f"{trace_set.trace_set_id}-grade",
        dataset_id=dataset.dataset_id,
        trace_set_id=trace_set.trace_set_id,
        variant=trace_set.variant,
        passed=not failures,
        case_reports=tuple(case_reports),
        aggregate_metrics=aggregates,
        blocking_failures=tuple(failures),
    )
