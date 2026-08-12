"""Typed contracts for configuration, deployment and release evidence."""

from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from typing import Any


VALID_TARGETS = {"local", "cloud_run", "agent_runtime"}
VALID_ENVIRONMENTS = {"local", "staging", "production"}
VALID_ARTIFACT_KINDS = {"source_tree", "container_image", "source_bundle"}
VALID_ROLLBACK_STRATEGIES = {
    "restart_prior_artifact",
    "traffic_shift",
    "redeploy_immutable_bundle",
}
VALID_CONTENT_MODES = {"NO_CONTENT", "METADATA_ONLY", "FULL_CONTENT"}
VALID_STATUSES = {"succeeded", "failed", "pending"}


def _require_text(value: str, field_name: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")


@dataclass(frozen=True)
class EnvironmentVariable:
    """One non-secret runtime setting."""

    name: str
    value: str

    def __post_init__(self) -> None:
        _require_text(self.name, "environment variable name")


@dataclass(frozen=True)
class SecretReference:
    """A secret binding that never contains secret material."""

    env_name: str
    secret_id: str
    version: str

    def __post_init__(self) -> None:
        _require_text(self.env_name, "secret env_name")
        _require_text(self.secret_id, "secret_id")
        _require_text(self.version, "secret version")


@dataclass(frozen=True)
class TelemetryPolicy:
    """Privacy and retention policy for production telemetry."""

    trace_export: bool
    span_content_mode: str
    prompt_response_capture: bool
    content_sink: str | None = None
    retention_days: int | None = None
    content_capture_approved: bool = False

    def __post_init__(self) -> None:
        if self.span_content_mode not in VALID_CONTENT_MODES:
            raise ValueError(
                f"unsupported span content mode: {self.span_content_mode}"
            )
        if self.retention_days is not None and self.retention_days <= 0:
            raise ValueError("retention_days must be positive")


@dataclass(frozen=True)
class ServiceBindings:
    """Stateful service ownership outside the Agent object."""

    session_service: str
    artifact_service: str
    memory_service: str

    def __post_init__(self) -> None:
        _require_text(self.session_service, "session_service")
        _require_text(self.artifact_service, "artifact_service")
        _require_text(self.memory_service, "memory_service")


@dataclass(frozen=True)
class BehaviorGate:
    """Immutable evidence that the candidate passed its behavior contract."""

    report_id: str
    report_digest: str
    dataset_id: str
    passed: bool
    blocking_failures: int

    def __post_init__(self) -> None:
        if self.blocking_failures < 0:
            raise ValueError("blocking_failures must be non-negative")


@dataclass(frozen=True)
class ProjectSpec:
    """Target-independent Agent source and runtime policy."""

    project_name: str
    agent_directory: str
    source_commit: str
    source_digest: str
    plain_env: tuple[EnvironmentVariable, ...]
    secret_refs: tuple[SecretReference, ...]
    telemetry: TelemetryPolicy
    behavior_gate: BehaviorGate

    def __post_init__(self) -> None:
        _require_text(self.project_name, "project_name")
        _require_text(self.agent_directory, "agent_directory")


@dataclass(frozen=True)
class TargetProfile:
    """Replaceable deployment-target topology."""

    target: str
    environment: str
    region: str
    artifact_kind: str
    artifact_ref: str
    artifact_digest: str
    runtime_identity: str
    ingress: str
    services: ServiceBindings
    rollback_strategy: str

    def __post_init__(self) -> None:
        if self.target not in VALID_TARGETS:
            raise ValueError(f"unsupported target: {self.target}")
        if self.environment not in VALID_ENVIRONMENTS:
            raise ValueError(f"unsupported environment: {self.environment}")
        if self.artifact_kind not in VALID_ARTIFACT_KINDS:
            raise ValueError(
                f"unsupported artifact kind: {self.artifact_kind}"
            )
        if self.rollback_strategy not in VALID_ROLLBACK_STRATEGIES:
            raise ValueError(
                f"unsupported rollback strategy: {self.rollback_strategy}"
            )


@dataclass(frozen=True)
class RenderedFile:
    """One rendered lifecycle artifact with explicit ownership."""

    path: str
    owner: str
    authority: str
    content: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RenderedProject:
    """Structured render output, independent of a template engine."""

    target: str
    environment: str
    files: tuple[RenderedFile, ...]

    def file(self, path: str) -> RenderedFile:
        for item in self.files:
            if item.path == path:
                return item
        raise KeyError(path)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RenderChange:
    """Digest-level diff for one owned artifact."""

    path: str
    owner: str
    before_digest: str
    after_digest: str


@dataclass(frozen=True)
class ReleaseRecord:
    """Append-only release evidence required for rollback."""

    release_id: str
    target: str
    environment: str
    artifact_ref: str
    artifact_digest: str
    spec_digest: str
    source_commit: str
    behavior_report_id: str
    behavior_report_digest: str
    platform_resource: str
    platform_revision: str
    rollback_strategy: str
    status: str
    deployed_at: str
    previous_release_id: str | None = None
    promoted_from_release_id: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.release_id, "release_id")
        if self.target not in VALID_TARGETS:
            raise ValueError(f"unsupported target: {self.target}")
        if self.environment not in VALID_ENVIRONMENTS:
            raise ValueError(f"unsupported environment: {self.environment}")
        if self.rollback_strategy not in VALID_ROLLBACK_STRATEGIES:
            raise ValueError(
                f"unsupported rollback strategy: {self.rollback_strategy}"
            )
        if self.status not in VALID_STATUSES:
            raise ValueError(f"unsupported release status: {self.status}")


@dataclass(frozen=True)
class RollbackPlan:
    """Target-specific rollback action over immutable release evidence."""

    current_release_id: str
    target_release_id: str
    target: str
    strategy: str
    command: tuple[str, ...]
    artifact_ref: str
    behavior_report_id: str


@dataclass(frozen=True)
class PolicyIssue:
    """One blocking production-contract violation."""

    code: str
    path: str
    message: str


@dataclass(frozen=True)
class ScenarioReport:
    """One production scenario and its blocking evidence."""

    scenario_id: str
    passed: bool
    issues: tuple[PolicyIssue, ...] = ()
    evidence: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProductionSuiteReport:
    """CI-style verdict across production-envelope scenarios."""

    variant: str
    passed: bool
    scenarios: tuple[ScenarioReport, ...]
    blocking_failures: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)
