"""Typed contracts for Blueprint validation and migration evidence."""

from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class BlueprintBundle:
    """Published schema, catalog snapshot, and executable examples."""

    root: Path
    schema: dict[str, Any]
    catalog_schema: dict[str, Any]
    catalog: dict[str, Any]
    blueprints: dict[str, dict[str, Any]]
    blueprint_paths: dict[str, Path]


@dataclass(frozen=True)
class ValidationIssue:
    """One deterministic Blueprint contract violation."""

    code: str
    path: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class ValidationReport:
    """Validation verdict and normalized Blueprint summary."""

    passed: bool
    issues: tuple[ValidationIssue, ...]
    summary: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MigrationResult:
    """One deterministic schema-version migration."""

    source_version: str
    target_version: str
    source_id: str
    target_id: str
    catalog_ref_preserved: bool
    blueprint: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)
