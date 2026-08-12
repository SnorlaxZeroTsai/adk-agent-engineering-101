"""Fail-closed production policy and drift checks."""

from __future__ import annotations

import re
from typing import Any

from .contracts import PolicyIssue
from .contracts import ProjectSpec
from .contracts import RenderedProject
from .contracts import ScenarioReport
from .contracts import TargetProfile
from .rendering import canonical_json


_HEX_64 = re.compile(r"^[0-9a-f]{64}$")
_HEX_40 = re.compile(r"^[0-9a-f]{40}$")
_SENSITIVE_NAME_PARTS = (
    "API_KEY",
    "CREDENTIAL",
    "PASSWORD",
    "PRIVATE_KEY",
    "SECRET",
    "TOKEN",
)


def _issue(code: str, path: str, message: str) -> PolicyIssue:
    return PolicyIssue(code=code, path=path, message=message)


def _looks_sensitive(name: str) -> bool:
    upper = name.upper()
    return any(part in upper for part in _SENSITIVE_NAME_PARTS)


def validate_envelope(
    project: ProjectSpec,
    profile: TargetProfile,
    rendered: RenderedProject,
    *,
    scenario_id: str,
) -> ScenarioReport:
    """Validate one target without requiring a cloud control plane."""

    issues: list[PolicyIssue] = []
    if not _HEX_40.fullmatch(project.source_commit):
        issues.append(
            _issue(
                "source_commit_not_immutable",
                "agent.source_commit",
                "source commit must be a full 40-character Git SHA",
            )
        )
    if not _HEX_64.fullmatch(project.source_digest):
        issues.append(
            _issue(
                "source_digest_invalid",
                "agent.source_digest",
                "source digest must be a SHA-256 hex value",
            )
        )

    gate = project.behavior_gate
    if not gate.passed or gate.blocking_failures:
        issues.append(
            _issue(
                "behavior_gate_failed",
                "quality.behavior_gate",
                "a candidate with blocking behavior failures cannot deploy",
            )
        )
    if not gate.report_id or not _HEX_64.fullmatch(gate.report_digest):
        issues.append(
            _issue(
                "behavior_evidence_missing",
                "quality.behavior_gate",
                "immutable behavior report identity and digest are required",
            )
        )

    plain = {item.name: item.value for item in project.plain_env}
    secrets = {item.env_name: item for item in project.secret_refs}
    duplicate_plain = len(plain) != len(project.plain_env)
    duplicate_secret = len(secrets) != len(project.secret_refs)
    if duplicate_plain or duplicate_secret:
        issues.append(
            _issue(
                "duplicate_runtime_key",
                "runtime.config",
                "runtime configuration keys must be unique",
            )
        )
    overlap = sorted(plain.keys() & secrets.keys())
    if overlap:
        issues.append(
            _issue(
                "plain_secret_overlap",
                "runtime.config",
                f"keys cannot be both plain env and secret refs: {overlap}",
            )
        )
    for name in sorted(plain):
        if _looks_sensitive(name):
            issues.append(
                _issue(
                    "plaintext_secret",
                    f"runtime.plain_env.{name}",
                    "secret-shaped settings must use a secret reference",
                )
            )
            if plain[name] and plain[name] in canonical_json(rendered.as_dict()):
                issues.append(
                    _issue(
                        "secret_material_rendered",
                        f"rendered.runtime.plain_env.{name}",
                        "render output exposes the configured secret material",
                    )
                )
    if profile.environment in {"staging", "production"}:
        for secret in project.secret_refs:
            if secret.version == "latest":
                issues.append(
                    _issue(
                        "secret_version_unpinned",
                        f"runtime.secret_refs.{secret.env_name}",
                        "remote releases require an immutable secret version",
                    )
                )

    telemetry = project.telemetry
    if telemetry.span_content_mode == "FULL_CONTENT":
        issues.append(
            _issue(
                "trace_content_enabled",
                "runtime.telemetry.span_content_mode",
                "full prompt/response content must stay out of trace spans",
            )
        )
    if telemetry.prompt_response_capture:
        if not telemetry.content_capture_approved:
            issues.append(
                _issue(
                    "content_capture_unapproved",
                    "runtime.telemetry",
                    "full content capture requires explicit data-governance approval",
                )
            )
        if not telemetry.content_sink or telemetry.retention_days is None:
            issues.append(
                _issue(
                    "content_lifecycle_missing",
                    "runtime.telemetry",
                    "content capture requires a named sink and retention policy",
                )
            )

    digest_suffix = f"@sha256:{profile.artifact_digest}"
    if not _HEX_64.fullmatch(profile.artifact_digest):
        issues.append(
            _issue(
                "artifact_digest_invalid",
                "deployment.artifact_digest",
                "artifact digest must be a SHA-256 hex value",
            )
        )
    if not profile.artifact_ref.endswith(digest_suffix):
        issues.append(
            _issue(
                "artifact_not_immutable",
                "deployment.artifact_ref",
                "artifact reference must bind the declared SHA-256 digest",
            )
        )

    expected = {
        "local": (
            "source_tree",
            "restart_prior_artifact",
            {"in_memory"},
        ),
        "cloud_run": (
            "container_image",
            "traffic_shift",
            set(),
        ),
        "agent_runtime": (
            "source_bundle",
            "redeploy_immutable_bundle",
            set(),
        ),
    }[profile.target]
    expected_kind, expected_rollback, allowed_in_memory = expected
    if profile.artifact_kind != expected_kind:
        issues.append(
            _issue(
                "target_artifact_mismatch",
                "deployment.artifact_kind",
                f"{profile.target} requires {expected_kind}",
            )
        )
    if profile.rollback_strategy != expected_rollback:
        issues.append(
            _issue(
                "target_rollback_mismatch",
                "deployment.rollback_strategy",
                f"{profile.target} requires {expected_rollback}",
            )
        )
    services = profile.services
    if profile.target != "local":
        for field_name, value in (
            ("session_service", services.session_service),
            ("artifact_service", services.artifact_service),
            ("memory_service", services.memory_service),
        ):
            if value in allowed_in_memory or value == "in_memory":
                issues.append(
                    _issue(
                        "ephemeral_remote_service",
                        f"runtime.services.{field_name}",
                        "remote targets require an explicitly durable service",
                    )
                )
        if profile.runtime_identity in {"developer_adc", "default"}:
            issues.append(
                _issue(
                    "runtime_identity_implicit",
                    "deployment.runtime_identity",
                    "remote deployment requires a named runtime identity",
                )
            )
    if profile.target == "agent_runtime" and "GOOGLE_CLOUD_PROJECT" in plain:
        issues.append(
            _issue(
                "reserved_runtime_env",
                "runtime.plain_env.GOOGLE_CLOUD_PROJECT",
                "Agent Runtime injects GOOGLE_CLOUD_PROJECT",
            )
        )

    return ScenarioReport(
        scenario_id=scenario_id,
        passed=not issues,
        issues=tuple(issues),
        evidence={
            "target": profile.target,
            "environment": profile.environment,
            "rendered_paths": [item.path for item in rendered.files],
        },
    )


def detect_environment_drift(
    desired: dict[str, str],
    live: dict[str, str],
    *,
    scenario_id: str,
) -> ScenarioReport:
    """Make out-of-band values visible before an update preserves them."""

    issues: list[PolicyIssue] = []
    missing = sorted(desired.keys() - live.keys())
    unmanaged = sorted(live.keys() - desired.keys())
    changed = sorted(
        key
        for key in desired.keys() & live.keys()
        if desired[key] != live[key]
    )
    for key in missing:
        issues.append(
            _issue(
                "live_env_missing",
                f"live_env.{key}",
                "desired setting is absent from the live service",
            )
        )
    for key in unmanaged:
        issues.append(
            _issue(
                "live_env_unmanaged",
                f"live_env.{key}",
                "out-of-band setting would survive a merge-style update",
            )
        )
    for key in changed:
        issues.append(
            _issue(
                "live_env_changed",
                f"live_env.{key}",
                "live value differs from the reviewed desired configuration",
            )
        )
    preserved = dict(live)
    preserved.update(desired)
    return ScenarioReport(
        scenario_id=scenario_id,
        passed=not issues,
        issues=tuple(issues),
        evidence={
            "missing": missing,
            "unmanaged": unmanaged,
            "changed": changed,
            "merge_style_result": dict(sorted(preserved.items())),
        },
    )


def audit_mutable_metadata(
    metadata: dict[str, Any],
    *,
    scenario_id: str,
) -> ScenarioReport:
    """Show why current-resource metadata is not a release ledger."""

    required = {
        "release_id",
        "artifact_ref",
        "artifact_digest",
        "spec_digest",
        "source_commit",
        "behavior_report_id",
        "behavior_report_digest",
        "previous_release_id",
    }
    issues = tuple(
        _issue(
            "release_evidence_missing",
            f"deployment_metadata.{field}",
            "rollback requires append-only immutable release evidence",
        )
        for field in sorted(required - metadata.keys())
    )
    return ScenarioReport(
        scenario_id=scenario_id,
        passed=not issues,
        issues=issues,
        evidence={"available_fields": sorted(metadata)},
    )
