"""Semantic validation for the minimal Agent Garden component model."""

from __future__ import annotations

from collections import Counter
from typing import Any

from .contracts import ArchitectureBundle
from .contracts import ValidationIssue
from .contracts import ValidationReport
from .references import validate_adr
from .references import validate_repository_ref


TOP_FIELDS = {
    "schema_version",
    "principles",
    "components",
    "artifacts",
    "storage_classes",
    "trust_boundaries",
    "extension_points",
    "lifecycle",
    "blueprint_walkthroughs",
    "adrs",
}
COMPONENT_FIELDS = {
    "id",
    "responsibility",
    "capabilities",
    "owns",
    "consumes",
    "produces",
    "credential_scope",
    "storage_dependencies",
    "extension_points",
    "forbidden_responsibilities",
    "evidence_refs",
}
ARTIFACT_FIELDS = {
    "id",
    "authority",
    "owner",
    "mutability",
    "storage",
    "digest_required",
    "secret_material_allowed",
    "producers",
    "consumers",
}
STORAGE_FIELDS = {
    "id",
    "purpose",
    "durability",
    "write_model",
    "allowed_artifacts",
    "forbidden_content",
}
TRUST_FIELDS = {
    "id",
    "from_actor",
    "to_actor",
    "artifacts",
    "controls",
}
EXTENSION_FIELDS = {
    "id",
    "kind",
    "owner",
    "contract_ref",
    "core_change_required",
    "cannot_override",
}
LIFECYCLE_FIELDS = {"initial_artifacts", "release_path", "rollback_path"}
STAGE_FIELDS = {"id", "component", "consumes", "produces", "requires"}
WALKTHROUGH_FIELDS = {
    "blueprint_id",
    "architecture",
    "target_adapter",
    "stages",
    "required_validators",
    "required_metrics",
    "required_extensions",
    "rollback_supported",
}
ADR_FIELDS = {"id", "path", "status"}

EXPECTED_COMPONENTS = {
    "catalog-registry",
    "contract-validator",
    "project-renderer",
    "deployment-controller",
    "behavior-gate",
    "release-ledger",
}
EXPECTED_CREDENTIAL_SCOPES = {
    "catalog-registry": "none",
    "contract-validator": "source-read",
    "project-renderer": "none",
    "deployment-controller": "target-scoped",
    "behavior-gate": "sandboxed-execution",
    "release-ledger": "ledger-write",
}
EXPECTED_RELEASE_STAGES = [
    "discover",
    "validate",
    "render",
    "stage",
    "evaluate",
    "promote",
    "record",
]
EXPECTED_ROLLBACK_STAGES = ["plan-rollback", "execute-rollback"]
COMMON_VALIDATORS = {
    "catalog-resolution",
    "source-assurance",
    "local-reference",
    "state-ownership",
    "common-policy-evaluation-lifecycle",
}
ARCHITECTURE_VALIDATORS = {
    "single-agent": {"single-agent-tools"},
    "workflow": {"workflow-graph", "retrieval-provenance"},
    "multi-agent": {"multi-agent-delegation", "approval-replay"},
}
EXTENSION_GUARDS = {
    "architecture-kind": {
        "catalog-identity",
        "state-ownership",
        "policy-gate",
        "evaluation-gate",
    },
    "source-resolver": {
        "immutable-revision",
        "assurance-digest",
        "trust-policy",
    },
    "scaffold-renderer": {
        "catalog-authority",
        "policy-gate",
        "evaluation-gate",
    },
    "runtime-service-binding": {
        "state-ownership",
        "secret-policy",
        "durability-declaration",
    },
    "evaluation-metric": {
        "case-completeness",
        "blocking-semantics",
        "report-candidate-binding",
    },
    "deployment-target": {
        "artifact-digest",
        "behavior-gate",
        "secret-policy",
        "release-evidence",
    },
    "release-store": {
        "append-only-history",
        "promotion-evidence",
        "previous-release",
    },
}


def _issue(
    issues: list[ValidationIssue],
    code: str,
    path: str,
    message: str,
) -> None:
    issues.append(ValidationIssue(code=code, path=path, message=message))


def _duplicates(values: list[Any]) -> set[Any]:
    return {
        value
        for value, count in Counter(values).items()
        if value is not None and count > 1
    }


def _require_fields(
    value: dict[str, Any],
    expected: set[str],
    path: str,
    issues: list[ValidationIssue],
) -> None:
    for field in sorted(expected - value.keys()):
        _issue(
            issues,
            "required_field_missing",
            f"{path}.{field}",
            "required field is absent",
        )
    for field in sorted(value.keys() - expected):
        _issue(
            issues,
            "unknown_field",
            f"{path}.{field}",
            "field is not part of the architecture contract",
        )


def _index(
    values: list[dict[str, Any]],
    path: str,
    issues: list[ValidationIssue],
) -> dict[str, dict[str, Any]]:
    ids = [item.get("id") for item in values if isinstance(item, dict)]
    for duplicate in sorted(_duplicates(ids)):
        _issue(issues, "id_duplicate", path, str(duplicate))
    return {
        item["id"]: item
        for item in values
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }


def _validate_published_schema(
    bundle: ArchitectureBundle,
    issues: list[ValidationIssue],
) -> None:
    schema = bundle.schema
    if set(schema.get("required", [])) != TOP_FIELDS:
        _issue(
            issues,
            "published_schema_field_drift",
            "schema.required",
            "top-level required fields differ from the stdlib validator",
        )
    if set(schema.get("properties", {})) != TOP_FIELDS:
        _issue(
            issues,
            "published_schema_field_drift",
            "schema.properties",
            "top-level properties differ from the stdlib validator",
        )
    expected = {
        "component": COMPONENT_FIELDS,
        "artifact": ARTIFACT_FIELDS,
        "storage_class": STORAGE_FIELDS,
        "trust_boundary": TRUST_FIELDS,
        "extension_point": EXTENSION_FIELDS,
        "lifecycle": LIFECYCLE_FIELDS,
        "stage": STAGE_FIELDS,
        "walkthrough": WALKTHROUGH_FIELDS,
        "adr": ADR_FIELDS,
    }
    for name, fields in expected.items():
        definition = schema.get("$defs", {}).get(name, {})
        if set(definition.get("required", [])) != fields:
            _issue(
                issues,
                "published_schema_field_drift",
                f"schema.$defs.{name}.required",
                str(sorted(fields)),
            )
        if set(definition.get("properties", {})) != fields:
            _issue(
                issues,
                "published_schema_field_drift",
                f"schema.$defs.{name}.properties",
                str(sorted(fields)),
            )


def _validate_structure(
    architecture: dict[str, Any],
    issues: list[ValidationIssue],
) -> None:
    _require_fields(architecture, TOP_FIELDS, "architecture", issues)
    for field, expected in (
        ("components", COMPONENT_FIELDS),
        ("artifacts", ARTIFACT_FIELDS),
        ("storage_classes", STORAGE_FIELDS),
        ("trust_boundaries", TRUST_FIELDS),
        ("extension_points", EXTENSION_FIELDS),
        ("blueprint_walkthroughs", WALKTHROUGH_FIELDS),
        ("adrs", ADR_FIELDS),
    ):
        values = architecture.get(field, [])
        if not isinstance(values, list):
            _issue(
                issues,
                "field_type_invalid",
                f"architecture.{field}",
                "expected array",
            )
            continue
        for index, value in enumerate(values):
            if not isinstance(value, dict):
                _issue(
                    issues,
                    "field_type_invalid",
                    f"architecture.{field}[{index}]",
                    "expected object",
                )
                continue
            _require_fields(
                value,
                expected,
                f"architecture.{field}[{index}]",
                issues,
            )
    lifecycle = architecture.get("lifecycle", {})
    if isinstance(lifecycle, dict):
        _require_fields(
            lifecycle,
            LIFECYCLE_FIELDS,
            "architecture.lifecycle",
            issues,
        )
        for field in ("release_path", "rollback_path"):
            for index, stage in enumerate(lifecycle.get(field, [])):
                if isinstance(stage, dict):
                    _require_fields(
                        stage,
                        STAGE_FIELDS,
                        f"architecture.lifecycle.{field}[{index}]",
                        issues,
                    )


def _validate_components_and_artifacts(
    architecture: dict[str, Any],
    components: dict[str, dict[str, Any]],
    artifacts: dict[str, dict[str, Any]],
    issues: list[ValidationIssue],
) -> None:
    if set(components) != EXPECTED_COMPONENTS:
        _issue(
            issues,
            "mvp_component_set_invalid",
            "architecture.components",
            str(sorted(set(components) ^ EXPECTED_COMPONENTS)),
        )
    for component_id, component in components.items():
        path = f"components.{component_id}"
        expected_scope = EXPECTED_CREDENTIAL_SCOPES.get(component_id)
        if component.get("credential_scope") != expected_scope:
            _issue(
                issues,
                "credential_scope_violation",
                f"{path}.credential_scope",
                f"expected {expected_scope}",
            )
        for artifact_id in component.get("owns", []):
            artifact = artifacts.get(artifact_id)
            if artifact is None:
                _issue(
                    issues,
                    "component_artifact_unknown",
                    f"{path}.owns",
                    str(artifact_id),
                )
            elif artifact.get("owner") != component_id:
                _issue(
                    issues,
                    "artifact_owner_component_mismatch",
                    f"{path}.owns",
                    str(artifact_id),
                )
        for artifact_id in component.get("produces", []):
            artifact = artifacts.get(artifact_id)
            if artifact is None:
                _issue(
                    issues,
                    "component_artifact_unknown",
                    f"{path}.produces",
                    str(artifact_id),
                )
            elif component_id not in artifact.get("producers", []):
                _issue(
                    issues,
                    "artifact_producer_mismatch",
                    f"{path}.produces",
                    str(artifact_id),
                )
        for artifact_id in component.get("consumes", []):
            artifact = artifacts.get(artifact_id)
            if artifact is None:
                _issue(
                    issues,
                    "component_artifact_unknown",
                    f"{path}.consumes",
                    str(artifact_id),
                )
            elif component_id not in artifact.get("consumers", []):
                _issue(
                    issues,
                    "artifact_consumer_mismatch",
                    f"{path}.consumes",
                    str(artifact_id),
                )
        if len(component.get("forbidden_responsibilities", [])) < 2:
            _issue(
                issues,
                "component_boundary_underspecified",
                f"{path}.forbidden_responsibilities",
                "at least two explicit exclusions are required",
            )
    for artifact_id, artifact in artifacts.items():
        owner = artifact.get("owner")
        if isinstance(owner, str) and not owner.startswith("external:"):
            component = components.get(owner)
            if component is None:
                _issue(
                    issues,
                    "artifact_owner_unknown",
                    f"artifacts.{artifact_id}.owner",
                    owner,
                )
            elif artifact_id not in component.get("owns", []):
                _issue(
                    issues,
                    "component_owns_mismatch",
                    f"artifacts.{artifact_id}.owner",
                    owner,
                )
        for producer in artifact.get("producers", []):
            if producer in components and artifact_id not in components[
                producer
            ].get("produces", []):
                _issue(
                    issues,
                    "component_produces_mismatch",
                    f"artifacts.{artifact_id}.producers",
                    producer,
                )
        for consumer in artifact.get("consumers", []):
            if consumer in components and artifact_id not in components[
                consumer
            ].get("consumes", []):
                _issue(
                    issues,
                    "component_consumes_mismatch",
                    f"artifacts.{artifact_id}.consumers",
                    consumer,
                )


def _validate_storage(
    artifacts: dict[str, dict[str, Any]],
    storage: dict[str, dict[str, Any]],
    issues: list[ValidationIssue],
) -> None:
    for artifact_id, artifact in artifacts.items():
        path = f"artifacts.{artifact_id}"
        storage_id = artifact.get("storage")
        storage_class = storage.get(storage_id)
        if storage_class is None:
            _issue(
                issues,
                "artifact_storage_unknown",
                f"{path}.storage",
                str(storage_id),
            )
        elif artifact_id not in storage_class.get("allowed_artifacts", []):
            _issue(
                issues,
                "storage_mapping_mismatch",
                f"{path}.storage",
                str(storage_id),
            )
        if artifact.get("secret_material_allowed"):
            _issue(
                issues,
                "secret_material_forbidden",
                f"{path}.secret_material_allowed",
                "Garden artifacts transport references, never secret material",
            )
    for storage_id, storage_class in storage.items():
        for artifact_id in storage_class.get("allowed_artifacts", []):
            artifact = artifacts.get(artifact_id)
            if artifact is None or artifact.get("storage") != storage_id:
                _issue(
                    issues,
                    "storage_mapping_mismatch",
                    f"storage_classes.{storage_id}.allowed_artifacts",
                    str(artifact_id),
                )
    candidate = artifacts.get("release-candidate", {})
    if (
        candidate.get("mutability") != "immutable"
        or not candidate.get("digest_required")
        or candidate.get("storage") != "content-addressed-store"
    ):
        _issue(
            issues,
            "candidate_not_immutable",
            "artifacts.release-candidate",
            "candidate must be immutable, digested and content-addressed",
        )
    report = artifacts.get("behavior-report", {})
    if (
        report.get("mutability") != "immutable"
        or not report.get("digest_required")
    ):
        _issue(
            issues,
            "behavior_report_digest_missing",
            "artifacts.behavior-report",
            "behavior evidence must be immutable and digested",
        )
    status = artifacts.get("deployment-status", {})
    if (
        status.get("authority") != "cache"
        or status.get("mutability") != "mutable-cache"
        or status.get("storage") != "target-control-plane"
    ):
        _issue(
            issues,
            "deployment_status_must_be_cache",
            "artifacts.deployment-status",
            "platform status cannot own release history",
        )
    release = artifacts.get("release-record", {})
    if (
        release.get("mutability") != "append-only"
        or release.get("storage") != "append-only-ledger"
        or not release.get("digest_required")
    ):
        _issue(
            issues,
            "release_record_not_append_only",
            "artifacts.release-record",
            "release truth must be append-only and digested",
        )


def _validate_extensions(
    root,
    components: dict[str, dict[str, Any]],
    extensions: dict[str, dict[str, Any]],
    issues: list[ValidationIssue],
) -> None:
    for extension_id, extension in extensions.items():
        path = f"extension_points.{extension_id}"
        owner = extension.get("owner")
        if owner not in components:
            _issue(
                issues,
                "extension_owner_unknown",
                f"{path}.owner",
                str(owner),
            )
        elif extension_id not in components[owner].get(
            "extension_points",
            [],
        ):
            _issue(
                issues,
                "component_extension_mismatch",
                f"{path}.owner",
                str(owner),
            )
        validate_repository_ref(
            root,
            extension.get("contract_ref"),
            f"{path}.contract_ref",
            issues,
        )
        if extension_id == "architecture-kind":
            if (
                extension.get("kind") != "typed-union"
                or not extension.get("core_change_required")
            ):
                _issue(
                    issues,
                    "architecture_extension_not_typed",
                    path,
                    "new architecture requires a reviewed core union change",
                )
        elif (
            extension.get("kind") != "external-adapter"
            or extension.get("core_change_required")
        ):
            _issue(
                issues,
                "adapter_extension_invalid",
                path,
                "provider integration must remain a constrained adapter",
            )
        missing_guards = EXTENSION_GUARDS.get(extension_id, set()) - set(
            extension.get("cannot_override", [])
        )
        if missing_guards:
            _issue(
                issues,
                "extension_guard_incomplete",
                f"{path}.cannot_override",
                ", ".join(sorted(missing_guards)),
            )
    for component_id, component in components.items():
        expected = {
            extension_id
            for extension_id, extension in extensions.items()
            if extension.get("owner") == component_id
        }
        if set(component.get("extension_points", [])) != expected:
            _issue(
                issues,
                "component_extension_mismatch",
                f"components.{component_id}.extension_points",
                str(sorted(expected)),
            )


def _validate_trust(
    components: dict[str, dict[str, Any]],
    artifacts: dict[str, dict[str, Any]],
    boundaries: dict[str, dict[str, Any]],
    issues: list[ValidationIssue],
) -> None:
    for boundary_id, boundary in boundaries.items():
        path = f"trust_boundaries.{boundary_id}"
        for actor_field in ("from_actor", "to_actor"):
            actor = boundary.get(actor_field)
            if (
                actor not in components
                and not str(actor).startswith("external:")
            ):
                _issue(
                    issues,
                    "trust_actor_unknown",
                    f"{path}.{actor_field}",
                    str(actor),
                )
        for artifact_id in boundary.get("artifacts", []):
            if artifact_id not in artifacts:
                _issue(
                    issues,
                    "trust_artifact_unknown",
                    f"{path}.artifacts",
                    str(artifact_id),
                )
        if len(boundary.get("controls", [])) < 2:
            _issue(
                issues,
                "trust_controls_incomplete",
                f"{path}.controls",
                "at least two controls are required",
            )
    required = {
        "registry-to-validation",
        "source-to-validation",
        "validation-to-render",
        "render-to-deployment",
        "secret-to-deployment",
        "candidate-to-evaluation",
        "evaluation-to-promotion",
        "deployment-to-ledger",
        "ledger-to-rollback",
    }
    if set(boundaries) != required:
        _issue(
            issues,
            "trust_boundary_set_invalid",
            "architecture.trust_boundaries",
            str(sorted(set(boundaries) ^ required)),
        )


def _validate_lifecycle(
    architecture: dict[str, Any],
    components: dict[str, dict[str, Any]],
    artifacts: dict[str, dict[str, Any]],
    issues: list[ValidationIssue],
) -> tuple[list[str], list[str]]:
    lifecycle = architecture.get("lifecycle", {})
    release_path = lifecycle.get("release_path", [])
    rollback_path = lifecycle.get("rollback_path", [])
    release_ids = [
        item.get("id") for item in release_path if isinstance(item, dict)
    ]
    rollback_ids = [
        item.get("id") for item in rollback_path if isinstance(item, dict)
    ]
    if release_ids != EXPECTED_RELEASE_STAGES:
        _issue(
            issues,
            "release_stage_sequence_invalid",
            "lifecycle.release_path",
            str(release_ids),
        )
    if rollback_ids != EXPECTED_ROLLBACK_STAGES:
        _issue(
            issues,
            "rollback_stage_sequence_invalid",
            "lifecycle.rollback_path",
            str(rollback_ids),
        )
    available = set(lifecycle.get("initial_artifacts", []))
    used_components: set[str] = set()
    for lane, stages in (
        ("release_path", release_path),
        ("rollback_path", rollback_path),
    ):
        lane_available = set(available)
        for index, stage in enumerate(stages):
            if not isinstance(stage, dict):
                continue
            path = f"lifecycle.{lane}[{index}]"
            component_id = stage.get("component")
            component = components.get(component_id)
            if component is None:
                _issue(
                    issues,
                    "stage_component_unknown",
                    f"{path}.component",
                    str(component_id),
                )
                continue
            used_components.add(component_id)
            consumes = set(stage.get("consumes", []))
            produces = set(stage.get("produces", []))
            missing = consumes - lane_available
            if missing:
                _issue(
                    issues,
                    "artifact_consumed_before_production",
                    f"{path}.consumes",
                    ", ".join(sorted(missing)),
                )
            if not consumes <= set(component.get("consumes", [])):
                _issue(
                    issues,
                    "stage_component_contract_mismatch",
                    f"{path}.consumes",
                    component_id,
                )
            if not produces <= set(component.get("produces", [])):
                _issue(
                    issues,
                    "stage_component_contract_mismatch",
                    f"{path}.produces",
                    component_id,
                )
            for artifact_id in produces:
                if artifact_id not in artifacts:
                    _issue(
                        issues,
                        "stage_artifact_unknown",
                        f"{path}.produces",
                        artifact_id,
                    )
                    continue
                if (
                    artifact_id in lane_available
                    and artifacts[artifact_id].get("mutability")
                    not in {"mutable-cache", "append-only"}
                ):
                    _issue(
                        issues,
                        "immutable_artifact_reproduced",
                        f"{path}.produces",
                        artifact_id,
                    )
            lane_available.update(produces)
    if used_components != set(components):
        _issue(
            issues,
            "component_unused",
            "architecture.components",
            str(sorted(set(components) - used_components)),
        )
    release_by_id = {
        stage.get("id"): stage
        for stage in release_path
        if isinstance(stage, dict)
    }
    promote = release_by_id.get("promote", {})
    if "behavior-report" not in promote.get("consumes", []):
        _issue(
            issues,
            "promotion_behavior_report_missing",
            "lifecycle.release_path.promote.consumes",
            "promotion must consume passing behavior evidence",
        )
    record = release_by_id.get("record", {})
    required_record = {
        "release-candidate",
        "behavior-report",
        "deployment-status",
    }
    if not required_record <= set(record.get("consumes", [])):
        _issue(
            issues,
            "release_record_evidence_incomplete",
            "lifecycle.release_path.record.consumes",
            str(sorted(required_record - set(record.get("consumes", [])))),
        )
    rollback_by_id = {
        stage.get("id"): stage
        for stage in rollback_path
        if isinstance(stage, dict)
    }
    if rollback_by_id.get("plan-rollback", {}).get(
        "component"
    ) != "release-ledger" or rollback_by_id.get(
        "execute-rollback",
        {},
    ).get(
        "component"
    ) != "deployment-controller":
        _issue(
            issues,
            "rollback_authority_mismatch",
            "lifecycle.rollback_path",
            "ledger plans and credentialed controller executes",
        )
    return release_ids, rollback_ids


def _validate_walkthroughs(
    bundle: ArchitectureBundle,
    components: dict[str, dict[str, Any]],
    extensions: dict[str, dict[str, Any]],
    release_ids: list[str],
    issues: list[ValidationIssue],
) -> None:
    walkthroughs = bundle.architecture.get("blueprint_walkthroughs", [])
    ids = [
        item.get("blueprint_id")
        for item in walkthroughs
        if isinstance(item, dict)
    ]
    if set(ids) != set(bundle.blueprints):
        _issue(
            issues,
            "walkthrough_set_invalid",
            "architecture.blueprint_walkthroughs",
            str(sorted(set(ids) ^ set(bundle.blueprints))),
        )
    validator_capabilities = set(
        components.get("contract-validator", {}).get("capabilities", [])
    )
    for index, walkthrough in enumerate(walkthroughs):
        if not isinstance(walkthrough, dict):
            continue
        path = f"blueprint_walkthroughs[{index}]"
        blueprint_id = walkthrough.get("blueprint_id")
        blueprint = bundle.blueprints.get(blueprint_id)
        if blueprint is None:
            continue
        architecture = blueprint.get("architecture", {}).get("kind")
        if walkthrough.get("architecture") != architecture:
            _issue(
                issues,
                "walkthrough_architecture_mismatch",
                f"{path}.architecture",
                str(architecture),
            )
        if walkthrough.get("stages") != release_ids:
            _issue(
                issues,
                "walkthrough_stage_mismatch",
                f"{path}.stages",
                str(release_ids),
            )
        expected_validators = COMMON_VALIDATORS | ARCHITECTURE_VALIDATORS[
            architecture
        ]
        observed_validators = set(
            walkthrough.get("required_validators", [])
        )
        if observed_validators != expected_validators:
            _issue(
                issues,
                "walkthrough_validator_missing",
                f"{path}.required_validators",
                str(sorted(expected_validators - observed_validators)),
            )
        if not observed_validators <= validator_capabilities:
            _issue(
                issues,
                "walkthrough_validator_unknown",
                f"{path}.required_validators",
                str(sorted(observed_validators - validator_capabilities)),
            )
        expected_metrics = blueprint.get("evaluation", {}).get(
            "blocking_metrics",
            [],
        )
        if walkthrough.get("required_metrics") != expected_metrics:
            _issue(
                issues,
                "walkthrough_metric_mismatch",
                f"{path}.required_metrics",
                str(expected_metrics),
            )
        if set(walkthrough.get("required_extensions", [])) != set(extensions):
            _issue(
                issues,
                "walkthrough_extension_mismatch",
                f"{path}.required_extensions",
                str(sorted(set(extensions))),
            )
        if walkthrough.get("rollback_supported") is not True:
            _issue(
                issues,
                "walkthrough_rollback_missing",
                f"{path}.rollback_supported",
                "every production target needs an explicit rollback path",
            )


def _summary(architecture: dict[str, Any]) -> dict[str, Any]:
    return {
        "component_count": len(architecture.get("components", [])),
        "artifact_count": len(architecture.get("artifacts", [])),
        "storage_class_count": len(
            architecture.get("storage_classes", [])
        ),
        "trust_boundary_count": len(
            architecture.get("trust_boundaries", [])
        ),
        "extension_point_count": len(
            architecture.get("extension_points", [])
        ),
        "release_stage_count": len(
            architecture.get("lifecycle", {}).get("release_path", [])
        ),
        "rollback_stage_count": len(
            architecture.get("lifecycle", {}).get("rollback_path", [])
        ),
        "walkthrough_count": len(
            architecture.get("blueprint_walkthroughs", [])
        ),
        "adr_count": len(architecture.get("adrs", [])),
    }


def validate_architecture_bundle(
    bundle: ArchitectureBundle,
) -> ValidationReport:
    issues: list[ValidationIssue] = []
    architecture = bundle.architecture
    _validate_published_schema(bundle, issues)
    _validate_structure(architecture, issues)
    components = _index(
        architecture.get("components", []),
        "architecture.components",
        issues,
    )
    artifacts = _index(
        architecture.get("artifacts", []),
        "architecture.artifacts",
        issues,
    )
    storage = _index(
        architecture.get("storage_classes", []),
        "architecture.storage_classes",
        issues,
    )
    boundaries = _index(
        architecture.get("trust_boundaries", []),
        "architecture.trust_boundaries",
        issues,
    )
    extensions = _index(
        architecture.get("extension_points", []),
        "architecture.extension_points",
        issues,
    )
    _validate_components_and_artifacts(
        architecture,
        components,
        artifacts,
        issues,
    )
    _validate_storage(artifacts, storage, issues)
    _validate_extensions(
        bundle.root,
        components,
        extensions,
        issues,
    )
    _validate_trust(components, artifacts, boundaries, issues)
    release_ids, _ = _validate_lifecycle(
        architecture,
        components,
        artifacts,
        issues,
    )
    _validate_walkthroughs(
        bundle,
        components,
        extensions,
        release_ids,
        issues,
    )
    for component_id, component in components.items():
        for index, reference in enumerate(component.get("evidence_refs", [])):
            validate_repository_ref(
                bundle.root,
                reference,
                f"components.{component_id}.evidence_refs[{index}]",
                issues,
            )
    adrs = architecture.get("adrs", [])
    adr_ids = [
        item.get("id")
        for item in adrs
        if isinstance(item, dict)
    ]
    for duplicate in sorted(_duplicates(adr_ids)):
        _issue(issues, "adr_id_duplicate", "architecture.adrs", duplicate)
    for index, adr in enumerate(adrs):
        if isinstance(adr, dict):
            validate_adr(
                bundle.root,
                adr,
                f"architecture.adrs[{index}]",
                issues,
            )
    ordered = tuple(
        sorted(
            issues,
            key=lambda item: (item.path, item.code, item.message),
        )
    )
    return ValidationReport(
        passed=not ordered,
        issues=ordered,
        summary=_summary(architecture),
    )
