"""Typed artifacts exchanged by Mini Agent Garden components."""

from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .canonical import digest_json


@dataclass(frozen=True)
class ImplementationSelection:
    entry_id: str
    implementation_id: str
    repository: str
    revision: str
    source_path: str
    language: str
    framework_package: str
    framework_version: str
    assurance_digests: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def digest(self) -> str:
        return digest_json(self.as_dict())


@dataclass(frozen=True)
class ContractReport:
    blueprint_id: str
    passed: bool
    issues: tuple[dict[str, str], ...]
    suite_summary: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def digest(self) -> str:
        return digest_json(self.as_dict())


@dataclass(frozen=True)
class ManagedFile:
    path: str
    digest: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class RenderPlan:
    blueprint: dict[str, Any]
    selection: ImplementationSelection
    validation: ContractReport
    files: dict[str, bytes]
    manifest: dict[str, Any]


@dataclass(frozen=True)
class Candidate:
    project_root: Path
    candidate_digest: str
    payload: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "candidate_digest": self.candidate_digest,
            **self.payload,
        }


@dataclass(frozen=True)
class TestSpec:
    command: tuple[str, ...]
    working_directory: str


@dataclass(frozen=True)
class UpgradePlan:
    project_root: Path
    categories: tuple[str, ...]
    requires_review: bool
    migration: dict[str, Any] | None
    current_manifest: dict[str, Any]
    target_plan: RenderPlan

    def as_dict(self) -> dict[str, Any]:
        target = self.target_plan.manifest
        payload = {
            "project_id": self.current_manifest["project_id"],
            "categories": list(self.categories),
            "requires_review": self.requires_review,
            "migration": self.migration,
            "from": {
                "project_digest": self.current_manifest["project_digest"],
                "blueprint_digest": self.current_manifest[
                    "blueprint_digest"
                ],
                "selection_digest": self.current_manifest[
                    "selection_digest"
                ],
            },
            "to": {
                "project_digest": target["project_digest"],
                "blueprint_digest": target["blueprint_digest"],
                "selection_digest": target["selection_digest"],
            },
        }
        return {
            **payload,
            "plan_digest": digest_json(payload),
        }
