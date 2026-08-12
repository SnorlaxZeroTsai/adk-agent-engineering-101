"""Deterministic and judge metric implementations."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .contracts import EvalCaseSpec
from .contracts import MetricPolicy
from .contracts import MetricResult
from .contracts import ObservedRun


RUNTIME_SUCCESS = "runtime_success"
TOOL_CONTRACT = "tool_contract"
TRAJECTORY_CONTRACT = "trajectory_contract"
STATE_CONTRACT = "state_contract"
OUTPUT_CONTRACT = "output_contract"
POLICY_SAFETY = "policy_safety"
RETRIEVAL_GROUNDING = "retrieval_grounding"
EFFICIENCY_BUDGET = "efficiency_budget"
SCRIPTED_RESPONSE_QUALITY = "scripted_response_quality"

_MISSING = object()


def default_metric_policies() -> tuple[MetricPolicy, ...]:
    """Return the local release policy used by Lab 06."""

    deterministic = (
        RUNTIME_SUCCESS,
        TOOL_CONTRACT,
        TRAJECTORY_CONTRACT,
        STATE_CONTRACT,
        OUTPUT_CONTRACT,
        POLICY_SAFETY,
        RETRIEVAL_GROUNDING,
        EFFICIENCY_BUDGET,
    )
    return tuple(
        MetricPolicy(
            name=name,
            kind="deterministic",
            threshold=1.0,
            blocking=True,
            aggregation="all_cases",
        )
        for name in deterministic
    ) + (
        MetricPolicy(
            name=SCRIPTED_RESPONSE_QUALITY,
            kind="judge",
            threshold=4.0,
            blocking=False,
            aggregation="mean",
        ),
    )


def _result(
    policy: MetricPolicy,
    *,
    score: float | None,
    reasons: list[str] | tuple[str, ...] = (),
    evidence: dict[str, Any] | None = None,
) -> MetricResult:
    if score is None:
        status = "not_evaluated"
    elif score >= policy.threshold:
        status = "passed"
    else:
        status = "failed"
    return MetricResult(
        metric_name=policy.name,
        kind=policy.kind,
        score=score,
        threshold=policy.threshold,
        status=status,
        blocking=policy.blocking,
        reasons=tuple(reasons),
        evidence=evidence or {},
    )


def _lookup_path(value: Mapping[str, Any], path: str) -> Any:
    current: Any = value
    for part in path.split("."):
        if not isinstance(current, Mapping) or part not in current:
            return _MISSING
        current = current[part]
    return current


def evaluate_runtime(
    case: EvalCaseSpec,
    observed: ObservedRun,
    policy: MetricPolicy,
) -> MetricResult:
    reasons: list[str] = []
    if case.require_no_error and observed.error_type:
        reasons.append(
            f"unexpected {observed.error_type}: {observed.error_message or ''}"
        )
    return _result(
        policy,
        score=1.0 if not reasons else 0.0,
        reasons=reasons,
        evidence={
            "error_type": observed.error_type,
            "error_message": observed.error_message,
        },
    )


def evaluate_tools(
    case: EvalCaseSpec,
    observed: ObservedRun,
    policy: MetricPolicy,
) -> MetricResult:
    expected = [
        {"name": item.name, "arguments": item.arguments}
        for item in case.expected_tool_calls
    ]
    actual = [
        {"name": item.name, "arguments": item.arguments}
        for item in observed.tool_calls
    ]
    reasons = []
    if actual != expected:
        reasons.append("tool names, order or arguments differ from the dataset")
    return _result(
        policy,
        score=1.0 if not reasons else 0.0,
        reasons=reasons,
        evidence={"expected": expected, "observed": actual},
    )


def evaluate_trajectory(
    case: EvalCaseSpec,
    observed: ObservedRun,
    policy: MetricPolicy,
) -> MetricResult:
    expected = list(case.expected_trajectory)
    actual = list(observed.trajectory)
    reasons = []
    if actual != expected:
        reasons.append("event or node trajectory differs from the dataset")
    return _result(
        policy,
        score=1.0 if not reasons else 0.0,
        reasons=reasons,
        evidence={"expected": expected, "observed": actual},
    )


def evaluate_state(
    case: EvalCaseSpec,
    observed: ObservedRun,
    policy: MetricPolicy,
) -> MetricResult:
    reasons: list[str] = []
    observed_values: dict[str, Any] = {}
    for path, expected in case.required_state.items():
        actual = _lookup_path(observed.state, path)
        observed_values[path] = None if actual is _MISSING else actual
        if actual is _MISSING:
            reasons.append(f"required state path {path!r} is missing")
        elif actual != expected:
            reasons.append(
                f"state path {path!r} expected {expected!r}, got {actual!r}"
            )
    forbidden_present: list[str] = []
    for path in case.forbidden_state_paths:
        if _lookup_path(observed.state, path) is not _MISSING:
            forbidden_present.append(path)
            reasons.append(f"forbidden state path {path!r} is present")
    return _result(
        policy,
        score=1.0 if not reasons else 0.0,
        reasons=reasons,
        evidence={
            "observed_required_values": observed_values,
            "forbidden_paths_present": forbidden_present,
        },
    )


def evaluate_output(
    case: EvalCaseSpec,
    observed: ObservedRun,
    policy: MetricPolicy,
) -> MetricResult:
    lowered = observed.output_text.lower()
    missing = [
        fragment
        for fragment in case.required_output_fragments
        if fragment.lower() not in lowered
    ]
    forbidden = [
        fragment
        for fragment in case.forbidden_output_fragments
        if fragment.lower() in lowered
    ]
    reasons = [
        f"required output fragment {fragment!r} is missing"
        for fragment in missing
    ]
    reasons.extend(
        f"forbidden output fragment {fragment!r} is present"
        for fragment in forbidden
    )
    return _result(
        policy,
        score=1.0 if not reasons else 0.0,
        reasons=reasons,
        evidence={
            "missing_fragments": missing,
            "forbidden_fragments_present": forbidden,
            "output_text": observed.output_text,
        },
    )


def evaluate_policy(
    case: EvalCaseSpec,
    observed: ObservedRun,
    policy: MetricPolicy,
) -> MetricResult:
    visible_forbidden = [
        fragment
        for fragment in case.forbidden_model_input_fragments
        if fragment in observed.model_input_text
    ]
    reasons = [
        f"runtime reported policy violation {violation!r}"
        for violation in observed.policy_violations
    ]
    reasons.extend(
        f"forbidden model-input fragment {fragment!r} is visible"
        for fragment in visible_forbidden
    )
    return _result(
        policy,
        score=1.0 if not reasons else 0.0,
        reasons=reasons,
        evidence={
            "policy_violations": list(observed.policy_violations),
            "forbidden_model_input_fragments": visible_forbidden,
        },
    )


def evaluate_retrieval(
    case: EvalCaseSpec,
    observed: ObservedRun,
    policy: MetricPolicy,
) -> MetricResult:
    evidence = observed.retrieval
    if evidence is None:
        return _result(
            policy,
            score=0.0,
            reasons=["retrieval evidence is missing"],
        )

    reasons: list[str] = []
    if case.require_retrieval_grounding and not evidence.grounded:
        reasons.append("aggregate grounded flag is false")
    if evidence.retrieval_recall < 1.0:
        reasons.append(
            f"retrieval recall is {evidence.retrieval_recall:.3f}, expected 1"
        )
    if evidence.citation_recall < 1.0:
        reasons.append(
            f"citation recall is {evidence.citation_recall:.3f}, expected 1"
        )
    if evidence.citation_precision < 1.0:
        reasons.append(
            "citation precision is "
            f"{evidence.citation_precision:.3f}, expected 1"
        )
    if evidence.access_violations:
        reasons.append(f"access violations: {evidence.access_violations}")
    if evidence.stale_hits:
        reasons.append(f"stale retrieval hits: {evidence.stale_hits}")
    if evidence.deleted_hits:
        reasons.append(f"deleted retrieval hits: {evidence.deleted_hits}")
    return _result(
        policy,
        score=1.0 if not reasons else 0.0,
        reasons=reasons,
        evidence={
            "retrieval_recall": evidence.retrieval_recall,
            "retrieval_precision": evidence.retrieval_precision,
            "citation_recall": evidence.citation_recall,
            "citation_precision": evidence.citation_precision,
            "access_violations": evidence.access_violations,
            "stale_hits": evidence.stale_hits,
            "deleted_hits": evidence.deleted_hits,
            "grounded": evidence.grounded,
        },
    )


def evaluate_efficiency(
    case: EvalCaseSpec,
    observed: ObservedRun,
    policy: MetricPolicy,
) -> MetricResult:
    if case.max_model_requests is None:
        return _result(
            policy,
            score=None,
            reasons=["dataset does not define a model-request budget"],
        )
    passed = observed.model_request_count <= case.max_model_requests
    reasons = []
    if not passed:
        reasons.append(
            f"model requests {observed.model_request_count} exceed "
            f"budget {case.max_model_requests}"
        )
    return _result(
        policy,
        score=1.0 if passed else 0.0,
        reasons=reasons,
        evidence={
            "observed_model_requests": observed.model_request_count,
            "maximum_model_requests": case.max_model_requests,
        },
    )


def evaluate_judge(
    case: EvalCaseSpec,
    observed: ObservedRun,
    policy: MetricPolicy,
) -> MetricResult:
    del case
    score = observed.judge_scores.get(policy.name)
    reasons = []
    if score is None:
        reasons.append("scripted judge score is absent")
    elif score < policy.threshold:
        reasons.append(
            f"judge score {score} is below threshold {policy.threshold}"
        )
    return _result(
        policy,
        score=score,
        reasons=reasons,
        evidence={"provenance": "scripted local score; not a live LLM judge"},
    )


EVALUATORS = {
    RUNTIME_SUCCESS: evaluate_runtime,
    TOOL_CONTRACT: evaluate_tools,
    TRAJECTORY_CONTRACT: evaluate_trajectory,
    STATE_CONTRACT: evaluate_state,
    OUTPUT_CONTRACT: evaluate_output,
    POLICY_SAFETY: evaluate_policy,
    RETRIEVAL_GROUNDING: evaluate_retrieval,
    EFFICIENCY_BUDGET: evaluate_efficiency,
    SCRIPTED_RESPONSE_QUALITY: evaluate_judge,
}
