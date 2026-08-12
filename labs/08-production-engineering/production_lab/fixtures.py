"""Fixed production envelopes and deliberate failure scenarios."""

from __future__ import annotations

from dataclasses import replace
import hashlib

from .contracts import BehaviorGate
from .contracts import EnvironmentVariable
from .contracts import ProjectSpec
from .contracts import ReleaseRecord
from .contracts import ScenarioReport
from .contracts import SecretReference
from .contracts import ServiceBindings
from .contracts import TargetProfile
from .contracts import TelemetryPolicy
from .gate import build_suite
from .policy import audit_mutable_metadata
from .policy import detect_environment_drift
from .policy import validate_envelope
from .release import ReleaseLedger
from .rendering import diff_projects
from .rendering import render_project


FIXED_DEPLOYED_AT = "2026-08-12T08:00:00+00:00"
SOURCE_COMMIT = "4f6ea50f8d433cc118ffb7216caf53b6e9f413b8"
OLD_SOURCE_COMMIT = "dbd74394e556f90991a60ca24a96ebc41a735594"


def _sha(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


SOURCE_DIGEST = _sha("support-agent-source-v4")
OLD_SOURCE_DIGEST = _sha("support-agent-source-v3")
BEHAVIOR_DIGEST = _sha("behavior-report-six-cases-passed")
OLD_BEHAVIOR_DIGEST = _sha("behavior-report-six-cases-passed-v3")
LOCAL_DIGEST = _sha("support-agent-local-source-v4")
CLOUD_DIGEST = _sha("support-agent-container-v4")
RUNTIME_DIGEST = _sha("support-agent-source-bundle-v4")
OLD_LOCAL_DIGEST = _sha("support-agent-local-source-v3")
OLD_CLOUD_DIGEST = _sha("support-agent-container-v3")
OLD_RUNTIME_DIGEST = _sha("support-agent-source-bundle-v3")


def build_project() -> ProjectSpec:
    return ProjectSpec(
        project_name="support-agent",
        agent_directory="app",
        source_commit=SOURCE_COMMIT,
        source_digest=SOURCE_DIGEST,
        plain_env=(
            EnvironmentVariable("AGENT_VERSION", "1.4.0"),
            EnvironmentVariable(
                "ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS",
                "false",
            ),
            EnvironmentVariable("LOG_LEVEL", "INFO"),
            EnvironmentVariable(
                "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT",
                "NO_CONTENT",
            ),
        ),
        secret_refs=(
            SecretReference(
                env_name="PAYMENTS_API_KEY",
                secret_id="payments-api-key",
                version="7",
            ),
        ),
        telemetry=TelemetryPolicy(
            trace_export=True,
            span_content_mode="NO_CONTENT",
            prompt_response_capture=False,
        ),
        behavior_gate=BehaviorGate(
            report_id="eval-support-agent-20260812-01",
            report_digest=BEHAVIOR_DIGEST,
            dataset_id="architecture-contract-v1",
            passed=True,
            blocking_failures=0,
        ),
    )


def build_old_project() -> ProjectSpec:
    project = build_project()
    return replace(
        project,
        source_commit=OLD_SOURCE_COMMIT,
        source_digest=OLD_SOURCE_DIGEST,
        behavior_gate=replace(
            project.behavior_gate,
            report_id="eval-support-agent-20260805-01",
            report_digest=OLD_BEHAVIOR_DIGEST,
        ),
    )


def build_profile(
    target: str,
    *,
    environment: str = "production",
) -> TargetProfile:
    if target == "local":
        return TargetProfile(
            target="local",
            environment="local",
            region="local",
            artifact_kind="source_tree",
            artifact_ref=(
                "source://support-agent"
                f"@sha256:{LOCAL_DIGEST}"
            ),
            artifact_digest=LOCAL_DIGEST,
            runtime_identity="developer_adc",
            ingress="loopback",
            services=ServiceBindings(
                session_service="in_memory",
                artifact_service="in_memory",
                memory_service="in_memory",
            ),
            rollback_strategy="restart_prior_artifact",
        )
    if target == "cloud_run":
        return TargetProfile(
            target="cloud_run",
            environment=environment,
            region="us-east1",
            artifact_kind="container_image",
            artifact_ref=(
                "us-east1-docker.pkg.dev/acme-agents/releases/support-agent"
                f"@sha256:{CLOUD_DIGEST}"
            ),
            artifact_digest=CLOUD_DIGEST,
            runtime_identity="support-agent-runtime@acme-agents.iam",
            ingress="internal-and-iap",
            services=ServiceBindings(
                session_service="cloud_sql",
                artifact_service="gcs",
                memory_service="memory_bank",
            ),
            rollback_strategy="traffic_shift",
        )
    if target == "agent_runtime":
        return TargetProfile(
            target="agent_runtime",
            environment=environment,
            region="us-east1",
            artifact_kind="source_bundle",
            artifact_ref=(
                "gs://acme-agent-releases/support-agent-v4.tar.gz"
                f"@sha256:{RUNTIME_DIGEST}"
            ),
            artifact_digest=RUNTIME_DIGEST,
            runtime_identity="support-agent-runtime@acme-agents.iam",
            ingress="agent-platform-api",
            services=ServiceBindings(
                session_service="vertex_ai_session",
                artifact_service="gcs",
                memory_service="memory_bank",
            ),
            rollback_strategy="redeploy_immutable_bundle",
        )
    raise ValueError(f"unsupported target: {target}")


def _record(
    release_id: str,
    profile: TargetProfile,
    project: ProjectSpec,
    *,
    artifact_ref: str | None = None,
    artifact_digest: str | None = None,
    previous_release_id: str | None = None,
    promoted_from_release_id: str | None = None,
    platform_resource: str,
    platform_revision: str,
) -> ReleaseRecord:
    rendered = render_project(project, profile)
    candidate = rendered.file("release/candidate.json").content
    selected_digest = artifact_digest or profile.artifact_digest
    selected_ref = artifact_ref or profile.artifact_ref
    return ReleaseRecord(
        release_id=release_id,
        target=profile.target,
        environment=profile.environment,
        artifact_ref=selected_ref,
        artifact_digest=selected_digest,
        spec_digest=str(candidate["spec_digest"]),
        source_commit=project.source_commit,
        behavior_report_id=project.behavior_gate.report_id,
        behavior_report_digest=project.behavior_gate.report_digest,
        platform_resource=platform_resource,
        platform_revision=platform_revision,
        rollback_strategy=profile.rollback_strategy,
        status="succeeded",
        deployed_at=FIXED_DEPLOYED_AT,
        previous_release_id=previous_release_id,
        promoted_from_release_id=promoted_from_release_id,
    )


def build_release_ledger() -> ReleaseLedger:
    project = build_project()
    old_project = build_old_project()
    ledger = ReleaseLedger()

    local = build_profile("local")
    old_local = replace(
        local,
        artifact_ref=(
            "source://support-agent"
            f"@sha256:{OLD_LOCAL_DIGEST}"
        ),
        artifact_digest=OLD_LOCAL_DIGEST,
    )
    ledger.append(
        _record(
            "local-v3",
            old_local,
            old_project,
            platform_resource="support-agent",
            platform_revision="local-v3",
        )
    )
    ledger.append(
        _record(
            "local-v4",
            local,
            project,
            previous_release_id="local-v3",
            platform_resource="support-agent",
            platform_revision="local-v4",
        )
    )

    cloud_staging = build_profile("cloud_run", environment="staging")
    old_cloud_staging = replace(
        cloud_staging,
        artifact_ref=(
            "us-east1-docker.pkg.dev/acme-agents/releases/support-agent"
            f"@sha256:{OLD_CLOUD_DIGEST}"
        ),
        artifact_digest=OLD_CLOUD_DIGEST,
    )
    ledger.append(
        _record(
            "cloud-staging-v3",
            old_cloud_staging,
            old_project,
            platform_resource="support-agent",
            platform_revision="support-agent-staging-00003",
        )
    )
    ledger.append(
        _record(
            "cloud-staging-v4",
            cloud_staging,
            project,
            platform_resource="support-agent",
            platform_revision="support-agent-staging-00004",
        )
    )
    cloud_prod = build_profile("cloud_run")
    old_cloud_prod = replace(
        cloud_prod,
        artifact_ref=(
            "us-east1-docker.pkg.dev/acme-agents/releases/support-agent"
            f"@sha256:{OLD_CLOUD_DIGEST}"
        ),
        artifact_digest=OLD_CLOUD_DIGEST,
    )
    ledger.append(
        _record(
            "cloud-prod-v3",
            old_cloud_prod,
            old_project,
            promoted_from_release_id="cloud-staging-v3",
            platform_resource="support-agent",
            platform_revision="support-agent-00003",
        )
    )
    ledger.append(
        _record(
            "cloud-prod-v4",
            cloud_prod,
            project,
            previous_release_id="cloud-prod-v3",
            promoted_from_release_id="cloud-staging-v4",
            platform_resource="support-agent",
            platform_revision="support-agent-00004",
        )
    )

    runtime_staging = build_profile("agent_runtime", environment="staging")
    old_runtime_staging = replace(
        runtime_staging,
        artifact_ref=(
            "gs://acme-agent-releases/support-agent-v3.tar.gz"
            f"@sha256:{OLD_RUNTIME_DIGEST}"
        ),
        artifact_digest=OLD_RUNTIME_DIGEST,
    )
    ledger.append(
        _record(
            "runtime-staging-v3",
            old_runtime_staging,
            old_project,
            platform_resource=(
                "projects/acme/locations/us-east1/"
                "reasoningEngines/staging"
            ),
            platform_revision="reasoningEngines/staging-v3",
        )
    )
    ledger.append(
        _record(
            "runtime-staging-v4",
            runtime_staging,
            project,
            platform_resource=(
                "projects/acme/locations/us-east1/"
                "reasoningEngines/staging"
            ),
            platform_revision="reasoningEngines/staging-v4",
        )
    )
    runtime_prod = build_profile("agent_runtime")
    old_runtime_prod = replace(
        runtime_prod,
        artifact_ref=(
            "gs://acme-agent-releases/support-agent-v3.tar.gz"
            f"@sha256:{OLD_RUNTIME_DIGEST}"
        ),
        artifact_digest=OLD_RUNTIME_DIGEST,
    )
    ledger.append(
        _record(
            "runtime-prod-v3",
            old_runtime_prod,
            old_project,
            promoted_from_release_id="runtime-staging-v3",
            platform_resource="projects/acme/locations/us-east1/reasoningEngines/prod",
            platform_revision="reasoningEngines/prod-v3",
        )
    )
    ledger.append(
        _record(
            "runtime-prod-v4",
            runtime_prod,
            project,
            previous_release_id="runtime-prod-v3",
            promoted_from_release_id="runtime-staging-v4",
            platform_resource="projects/acme/locations/us-east1/reasoningEngines/prod",
            platform_revision="reasoningEngines/prod-v4",
        )
    )
    return ledger


def _baseline_scenarios() -> tuple[ScenarioReport, ...]:
    project = build_project()
    profiles = tuple(
        build_profile(target)
        for target in ("local", "cloud_run", "agent_runtime")
    )
    rendered = tuple(render_project(project, profile) for profile in profiles)
    scenarios = [
        validate_envelope(
            project,
            profile,
            output,
            scenario_id=f"{profile.target}-envelope",
        )
        for profile, output in zip(profiles, rendered)
    ]
    desired = {item.name: item.value for item in project.plain_env}
    scenarios.append(
        detect_environment_drift(
            desired,
            dict(desired),
            scenario_id="reviewed-environment",
        )
    )
    ledger = build_release_ledger()
    scenarios.append(
        ledger.validate(scenario_id="append-only-release-ledger")
    )
    rollback_plans = {
        release_id: ledger.rollback_plan(release_id)
        for release_id in (
            "local-v4",
            "cloud-prod-v4",
            "runtime-prod-v4",
        )
    }
    scenarios.append(
        ScenarioReport(
            scenario_id="target-specific-rollback",
            passed=True,
            evidence={
                key: {
                    "strategy": value.strategy,
                    "target_release_id": value.target_release_id,
                    "artifact_ref": value.artifact_ref,
                    "command": list(value.command),
                }
                for key, value in rollback_plans.items()
            },
        )
    )
    scenarios.append(
        ScenarioReport(
            scenario_id="replaceable-target-diff",
            passed=True,
            evidence={
                "local_to_cloud_run": [
                    item.path
                    for item in diff_projects(rendered[0], rendered[1])
                ],
                "cloud_run_to_agent_runtime": [
                    item.path
                    for item in diff_projects(rendered[1], rendered[2])
                ],
            },
        )
    )
    return tuple(scenarios)


def _broken_scenarios() -> tuple[ScenarioReport, ...]:
    project = build_project()
    cloud = build_profile("cloud_run")
    runtime = build_profile("agent_runtime")
    scenarios: list[ScenarioReport] = []

    plain_secret = replace(
        project,
        plain_env=(
            *project.plain_env,
            EnvironmentVariable(
                "PAYMENTS_API_KEY",
                "secret-material-for-payments-api-key",
            ),
        ),
    )
    scenarios.append(
        validate_envelope(
            plain_secret,
            cloud,
            render_project(plain_secret, cloud),
            scenario_id="plaintext-secret",
        )
    )

    content_capture = replace(
        project,
        telemetry=TelemetryPolicy(
            trace_export=True,
            span_content_mode="FULL_CONTENT",
            prompt_response_capture=True,
            content_sink=None,
            retention_days=None,
            content_capture_approved=False,
        ),
    )
    scenarios.append(
        validate_envelope(
            content_capture,
            cloud,
            render_project(content_capture, cloud),
            scenario_id="unapproved-content-telemetry",
        )
    )

    missing_gate = replace(
        project,
        behavior_gate=BehaviorGate(
            report_id="",
            report_digest="",
            dataset_id="architecture-contract-v1",
            passed=False,
            blocking_failures=3,
        ),
    )
    scenarios.append(
        validate_envelope(
            missing_gate,
            cloud,
            render_project(missing_gate, cloud),
            scenario_id="missing-behavior-gate",
        )
    )

    mutable_artifact = replace(
        cloud,
        artifact_ref=(
            "us-east1-docker.pkg.dev/acme-agents/releases/support-agent:latest"
        ),
    )
    scenarios.append(
        validate_envelope(
            project,
            mutable_artifact,
            render_project(project, mutable_artifact),
            scenario_id="mutable-artifact-tag",
        )
    )

    target_mismatch = replace(
        runtime,
        artifact_kind="container_image",
        rollback_strategy="traffic_shift",
    )
    scenarios.append(
        validate_envelope(
            project,
            target_mismatch,
            render_project(project, target_mismatch),
            scenario_id="target-capability-mismatch",
        )
    )

    desired = {item.name: item.value for item in project.plain_env}
    live = {
        **desired,
        "LOG_LEVEL": "DEBUG",
        "DEBUG_BYPASS": "true",
    }
    scenarios.append(
        detect_environment_drift(
            desired,
            live,
            scenario_id="silent-live-config-preservation",
        )
    )

    scenarios.append(
        audit_mutable_metadata(
            {
                "remote_agent_runtime_id": (
                    "projects/123/locations/us-east1/"
                    "reasoningEngines/456"
                ),
                "deployment_target": "agent_runtime",
                "deployment_timestamp": FIXED_DEPLOYED_AT,
            },
            scenario_id="mutable-current-resource-metadata",
        )
    )

    broken_ledger = ReleaseLedger()
    broken_ledger.append(
        _record(
            "cloud-prod-orphan",
            cloud,
            project,
            previous_release_id="cloud-prod-missing",
            promoted_from_release_id="staging-missing",
            platform_resource="support-agent",
            platform_revision="support-agent-00005",
        )
    )
    scenarios.append(
        broken_ledger.validate(
            scenario_id="orphaned-rollback-history"
        )
    )
    return tuple(scenarios)


def build_baseline_suite():
    return build_suite("baseline", _baseline_scenarios())


def build_broken_suite():
    return build_suite("broken", _broken_scenarios())


def build_evidence_bundle() -> dict[str, object]:
    project = build_project()
    rendered = {
        target: render_project(project, build_profile(target))
        for target in ("local", "cloud_run", "agent_runtime")
    }
    ledger = build_release_ledger()
    return {
        "source_commit": SOURCE_COMMIT,
        "renders": {
            target: output.as_dict()
            for target, output in rendered.items()
        },
        "diffs": {
            "local_to_cloud_run": [
                item.__dict__
                for item in diff_projects(
                    rendered["local"],
                    rendered["cloud_run"],
                )
            ],
            "cloud_run_to_agent_runtime": [
                item.__dict__
                for item in diff_projects(
                    rendered["cloud_run"],
                    rendered["agent_runtime"],
                )
            ],
        },
        "release_ledger": ledger.as_dict(),
        "rollback_plans": {
            release_id: ledger.rollback_plan(release_id).__dict__
            for release_id in (
                "local-v4",
                "cloud-prod-v4",
                "runtime-prod-v4",
            )
        },
        "gate_results": {
            "baseline": build_baseline_suite().as_dict(),
            "broken": build_broken_suite().as_dict(),
        },
    }
