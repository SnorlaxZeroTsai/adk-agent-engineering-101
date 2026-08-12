"""Typed results for discoverability validation."""

from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class DiscoveryBundle:
    """Loaded catalog, source-surface inventory, and published schema."""

    root: Path
    catalog: dict[str, Any]
    metadata: dict[str, Any]
    schema: dict[str, Any]


@dataclass(frozen=True)
class ValidationIssue:
    """One deterministic discoverability violation."""

    code: str
    path: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class ValidationReport:
    """Validation verdict and normalized catalog summary."""

    passed: bool
    issues: tuple[ValidationIssue, ...]
    summary: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)
