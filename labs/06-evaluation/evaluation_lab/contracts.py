"""Typed dataset, trace and grade-result contracts."""

from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from typing import Any


VALID_METRIC_KINDS = {"deterministic", "judge"}
VALID_AGGREGATIONS = {"all_cases", "min", "mean"}
VALID_STATUSES = {"passed", "failed", "not_evaluated"}


@dataclass(frozen=True)
class ToolCall:
    """One exact tool name and argument contract."""

    name: str
    arguments: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("tool call name must not be empty")


@dataclass(frozen=True)
class RetrievalEvidence:
    """Normalized RAG evidence independent of the retrieval adapter."""

    retrieval_recall: float
    retrieval_precision: float
    citation_recall: float
    citation_precision: float
    access_violations: int
    stale_hits: int
    deleted_hits: int
    grounded: bool


@dataclass(frozen=True)
class EvalCaseSpec:
    """Expected observable behavior for one architecture case."""

    case_id: str
    phase: str
    metrics: tuple[str, ...]
    expected_tool_calls: tuple[ToolCall, ...] = ()
    expected_trajectory: tuple[str, ...] = ()
    required_state: dict[str, Any] = field(default_factory=dict)
    forbidden_state_paths: tuple[str, ...] = ()
    required_output_fragments: tuple[str, ...] = ()
    forbidden_output_fragments: tuple[str, ...] = ()
    forbidden_model_input_fragments: tuple[str, ...] = ()
    max_model_requests: int | None = None
    require_no_error: bool = True
    require_retrieval_grounding: bool = False

    def __post_init__(self) -> None:
        if not self.case_id.strip():
            raise ValueError("case_id must not be empty")
        if not self.phase.strip():
            raise ValueError("phase must not be empty")
        if not self.metrics:
            raise ValueError(f"{self.case_id}: at least one metric is required")
        if len(set(self.metrics)) != len(self.metrics):
            raise ValueError(f"{self.case_id}: metric names must be unique")
        if self.max_model_requests is not None and self.max_model_requests < 0:
            raise ValueError("max_model_requests must be non-negative")


@dataclass(frozen=True)
class EvalDataset:
    """Stage 1: immutable case expectations."""

    dataset_id: str
    cases: tuple[EvalCaseSpec, ...]

    def __post_init__(self) -> None:
        if not self.dataset_id.strip():
            raise ValueError("dataset_id must not be empty")
        case_ids = [case.case_id for case in self.cases]
        if len(case_ids) != len(set(case_ids)):
            raise ValueError("dataset case IDs must be unique")
        if not case_ids:
            raise ValueError("dataset must contain at least one case")

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ObservedRun:
    """One normalized runtime trace produced independently of grading."""

    case_id: str
    phase: str
    output_text: str = ""
    tool_calls: tuple[ToolCall, ...] = ()
    trajectory: tuple[str, ...] = ()
    state: dict[str, Any] = field(default_factory=dict)
    model_input_text: str = ""
    model_request_count: int = 0
    error_type: str | None = None
    error_message: str | None = None
    policy_violations: tuple[str, ...] = ()
    retrieval: RetrievalEvidence | None = None
    judge_scores: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.model_request_count < 0:
            raise ValueError("model_request_count must be non-negative")


@dataclass(frozen=True)
class TraceSet:
    """Stage 2: populated observations without metric verdicts."""

    trace_set_id: str
    dataset_id: str
    variant: str
    observations: tuple[ObservedRun, ...]

    def __post_init__(self) -> None:
        case_ids = [item.case_id for item in self.observations]
        if len(case_ids) != len(set(case_ids)):
            raise ValueError("trace observation case IDs must be unique")

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MetricPolicy:
    """Threshold, blocking behavior and suite aggregation for one metric."""

    name: str
    kind: str
    threshold: float
    blocking: bool
    aggregation: str

    def __post_init__(self) -> None:
        if self.kind not in VALID_METRIC_KINDS:
            raise ValueError(f"unsupported metric kind: {self.kind}")
        if self.aggregation not in VALID_AGGREGATIONS:
            raise ValueError(
                f"unsupported metric aggregation: {self.aggregation}"
            )


@dataclass(frozen=True)
class MetricResult:
    """Stage 3 per-case metric result with actionable evidence."""

    metric_name: str
    kind: str
    score: float | None
    threshold: float
    status: str
    blocking: bool
    reasons: tuple[str, ...] = ()
    evidence: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.status not in VALID_STATUSES:
            raise ValueError(f"unsupported metric status: {self.status}")


@dataclass(frozen=True)
class CaseReport:
    """All metric outcomes for one dataset case."""

    case_id: str
    phase: str
    passed: bool
    metric_results: tuple[MetricResult, ...]


@dataclass(frozen=True)
class AggregateMetricResult:
    """Suite-level rollup that preserves its aggregation policy."""

    metric_name: str
    kind: str
    aggregation: str
    score: float | None
    threshold: float
    status: str
    blocking: bool
    evaluated_case_count: int


@dataclass(frozen=True)
class SuiteReport:
    """CI-consumable verdict for one dataset and trace set."""

    report_id: str
    dataset_id: str
    trace_set_id: str
    variant: str
    passed: bool
    case_reports: tuple[CaseReport, ...]
    aggregate_metrics: tuple[AggregateMetricResult, ...]
    blocking_failures: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)
