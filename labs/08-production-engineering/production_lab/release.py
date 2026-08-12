"""Append-only release history and target-specific rollback plans."""

from __future__ import annotations

from dataclasses import asdict
import re

from .contracts import PolicyIssue
from .contracts import ReleaseRecord
from .contracts import RollbackPlan
from .contracts import ScenarioReport


_HEX_64 = re.compile(r"^[0-9a-f]{64}$")


class ReleaseLedger:
    """Small in-memory model of a durable append-only release store."""

    def __init__(self) -> None:
        self._records: list[ReleaseRecord] = []

    @property
    def records(self) -> tuple[ReleaseRecord, ...]:
        return tuple(self._records)

    def append(self, record: ReleaseRecord) -> None:
        if any(item.release_id == record.release_id for item in self._records):
            raise ValueError(f"duplicate release ID: {record.release_id}")
        self._records.append(record)

    def get(self, release_id: str) -> ReleaseRecord:
        for record in self._records:
            if record.release_id == release_id:
                return record
        raise KeyError(release_id)

    def validate(self, *, scenario_id: str) -> ScenarioReport:
        issues: list[PolicyIssue] = []
        seen: set[str] = set()
        for record in self._records:
            path = f"releases.{record.release_id}"
            if record.release_id in seen:
                issues.append(
                    PolicyIssue(
                        code="duplicate_release_id",
                        path=path,
                        message="release IDs must be globally unique",
                    )
                )
            for field_name, value in (
                ("artifact_digest", record.artifact_digest),
                ("spec_digest", record.spec_digest),
                ("behavior_report_digest", record.behavior_report_digest),
            ):
                if not _HEX_64.fullmatch(value):
                    issues.append(
                        PolicyIssue(
                            code="release_digest_invalid",
                            path=f"{path}.{field_name}",
                            message="release evidence requires SHA-256 digests",
                        )
                    )
            if record.status != "succeeded":
                issues.append(
                    PolicyIssue(
                        code="release_not_succeeded",
                        path=f"{path}.status",
                        message="only a succeeded release can be promoted or restored",
                    )
                )
            if record.previous_release_id:
                if record.previous_release_id not in seen:
                    issues.append(
                        PolicyIssue(
                            code="previous_release_missing",
                            path=f"{path}.previous_release_id",
                            message="rollback target is absent from release history",
                        )
                    )
                else:
                    previous = self.get(record.previous_release_id)
                    if (
                        previous.target != record.target
                        or previous.environment != record.environment
                    ):
                        issues.append(
                            PolicyIssue(
                                code="previous_release_scope_mismatch",
                                path=f"{path}.previous_release_id",
                                message=(
                                    "rollback target must share target "
                                    "and environment"
                                ),
                            )
                        )
            if record.environment == "production":
                if not record.promoted_from_release_id:
                    issues.append(
                        PolicyIssue(
                            code="promotion_evidence_missing",
                            path=f"{path}.promoted_from_release_id",
                            message=(
                                "production release must name tested "
                                "staging evidence"
                            ),
                        )
                    )
                elif record.promoted_from_release_id not in seen:
                    issues.append(
                        PolicyIssue(
                            code="promotion_source_missing",
                            path=f"{path}.promoted_from_release_id",
                            message="staging release is absent from prior history",
                        )
                    )
                else:
                    staging = self.get(record.promoted_from_release_id)
                    if staging.target != record.target:
                        issues.append(
                            PolicyIssue(
                                code="promotion_target_mismatch",
                                path=f"{path}.promoted_from_release_id",
                                message="staging and production targets must match",
                            )
                        )
                    if staging.environment != "staging":
                        issues.append(
                            PolicyIssue(
                                code="promotion_source_not_staging",
                                path=f"{path}.promoted_from_release_id",
                                message=(
                                    "production promotion must originate "
                                    "in staging"
                                ),
                            )
                        )
                    if staging.artifact_digest != record.artifact_digest:
                        issues.append(
                            PolicyIssue(
                                code="promotion_artifact_changed",
                                path=f"{path}.artifact_digest",
                                message=(
                                    "production must use the artifact "
                                    "tested in staging"
                                ),
                            )
                        )
                    if (
                        staging.behavior_report_digest
                        != record.behavior_report_digest
                    ):
                        issues.append(
                            PolicyIssue(
                                code="promotion_gate_changed",
                                path=f"{path}.behavior_report_digest",
                                message=(
                                    "production must retain staging "
                                    "behavior evidence"
                                ),
                            )
                        )
            seen.add(record.release_id)
        return ScenarioReport(
            scenario_id=scenario_id,
            passed=not issues,
            issues=tuple(issues),
            evidence={
                "release_ids": [item.release_id for item in self._records],
            },
        )

    def rollback_plan(self, current_release_id: str) -> RollbackPlan:
        current = self.get(current_release_id)
        if not current.previous_release_id:
            raise ValueError(
                f"{current_release_id} has no previous immutable release"
            )
        previous = self.get(current.previous_release_id)
        if current.target == "cloud_run":
            command = (
                "gcloud",
                "run",
                "services",
                "update-traffic",
                current.platform_resource,
                f"--to-revisions={previous.platform_revision}=100",
            )
        elif current.target == "agent_runtime":
            command = (
                "release-orchestrator",
                "redeploy",
                "--target",
                "agent_runtime",
                "--artifact-ref",
                previous.artifact_ref,
            )
        else:
            command = (
                "local-runtime",
                "restart",
                "--artifact-ref",
                previous.artifact_ref,
            )
        return RollbackPlan(
            current_release_id=current.release_id,
            target_release_id=previous.release_id,
            target=current.target,
            strategy=current.rollback_strategy,
            command=command,
            artifact_ref=previous.artifact_ref,
            behavior_report_id=previous.behavior_report_id,
        )

    def as_dict(self) -> list[dict[str, object]]:
        return [asdict(item) for item in self._records]
