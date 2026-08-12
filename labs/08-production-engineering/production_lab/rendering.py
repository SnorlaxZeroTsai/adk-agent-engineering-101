"""Deterministic rendering and ownership-aware diffing."""

from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from typing import Any

from .contracts import ProjectSpec
from .contracts import RenderChange
from .contracts import RenderedFile
from .contracts import RenderedProject
from .contracts import TargetProfile


def canonical_json(value: Any) -> str:
    """Return stable JSON suitable for hashing and evidence bundles."""

    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )


def digest(value: Any) -> str:
    """SHA-256 over canonical structured data."""

    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _runtime_content(project: ProjectSpec, profile: TargetProfile) -> dict[str, Any]:
    return {
        "environment": profile.environment,
        "plain_env": [asdict(item) for item in project.plain_env],
        "secret_refs": [asdict(item) for item in project.secret_refs],
        "services": asdict(profile.services),
        "telemetry": asdict(project.telemetry),
    }


def _deployment_content(profile: TargetProfile) -> dict[str, Any]:
    return {
        "target": profile.target,
        "environment": profile.environment,
        "region": profile.region,
        "artifact_kind": profile.artifact_kind,
        "artifact_ref": profile.artifact_ref,
        "artifact_digest": profile.artifact_digest,
        "runtime_identity": profile.runtime_identity,
        "ingress": profile.ingress,
        "rollback_strategy": profile.rollback_strategy,
    }


def render_project(
    project: ProjectSpec,
    profile: TargetProfile,
) -> RenderedProject:
    """Render replaceable lifecycle artifacts for one target."""

    agent_contract = {
        "project_name": project.project_name,
        "agent_directory": project.agent_directory,
        "source_commit": project.source_commit,
        "source_digest": project.source_digest,
    }
    behavior_gate = asdict(project.behavior_gate)
    runtime_config = _runtime_content(project, profile)
    deployment_spec = _deployment_content(profile)
    lifecycle_manifest = {
        "schema_version": "1",
        "project_name": project.project_name,
        "target": profile.target,
        "environment": profile.environment,
        "generated_by": "production-envelope-lab/1",
    }
    spec_digest = digest(
        {
            "runtime_config": runtime_config,
            "deployment_spec": deployment_spec,
        }
    )
    release_candidate = {
        "source_commit": project.source_commit,
        "source_digest": project.source_digest,
        "artifact_ref": profile.artifact_ref,
        "artifact_digest": profile.artifact_digest,
        "behavior_report_id": project.behavior_gate.report_id,
        "behavior_report_digest": project.behavior_gate.report_digest,
        "spec_digest": spec_digest,
    }
    files = (
        RenderedFile(
            path="agent/contract.json",
            owner="agent-team",
            authority="authoritative",
            content=agent_contract,
        ),
        RenderedFile(
            path="quality/behavior-gate.json",
            owner="quality-team",
            authority="authoritative",
            content=behavior_gate,
        ),
        RenderedFile(
            path="runtime/config.json",
            owner="service-operator",
            authority="authoritative",
            content=runtime_config,
        ),
        RenderedFile(
            path="deployment/spec.json",
            owner="platform-team",
            authority="authoritative",
            content=deployment_spec,
        ),
        RenderedFile(
            path="lifecycle/manifest.json",
            owner="developer-platform",
            authority="authoritative",
            content=lifecycle_manifest,
        ),
        RenderedFile(
            path="release/candidate.json",
            owner="release-engineering",
            authority="derived",
            content=release_candidate,
        ),
    )
    return RenderedProject(
        target=profile.target,
        environment=profile.environment,
        files=files,
    )


def diff_projects(
    before: RenderedProject,
    after: RenderedProject,
) -> tuple[RenderChange, ...]:
    """Compare render artifacts without line-oriented template noise."""

    before_files = {item.path: item for item in before.files}
    after_files = {item.path: item for item in after.files}
    changes: list[RenderChange] = []
    for path in sorted(before_files.keys() | after_files.keys()):
        old = before_files.get(path)
        new = after_files.get(path)
        old_digest = digest(old.content) if old else ""
        new_digest = digest(new.content) if new else ""
        if old_digest == new_digest:
            continue
        owner = new.owner if new else old.owner
        changes.append(
            RenderChange(
                path=path,
                owner=owner,
                before_digest=old_digest,
                after_digest=new_digest,
            )
        )
    return tuple(changes)
