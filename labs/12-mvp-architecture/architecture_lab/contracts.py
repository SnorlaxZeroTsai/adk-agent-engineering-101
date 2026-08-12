"""Typed results for MVP architecture validation."""

from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class ArchitectureBundle:
    """Architecture model, schema, and Phase 11 Blueprint examples."""

    root: Path
    architecture: dict[str, Any]
    schema: dict[str, Any]
    blueprints: dict[str, dict[str, Any]]
    catalog: dict[str, Any]


@dataclass(frozen=True)
class ValidationIssue:
    """One deterministic architecture-boundary violation."""

    code: str
    path: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class ValidationReport:
    """Validation verdict and normalized MVP summary."""

    passed: bool
    issues: tuple[ValidationIssue, ...]
    summary: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)
