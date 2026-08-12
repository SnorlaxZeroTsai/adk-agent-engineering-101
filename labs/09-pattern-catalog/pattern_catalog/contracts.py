"""Typed validation results for the pattern catalog."""

from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class CatalogBundle:
    """Loaded catalog index and its canonical pattern manifests."""

    root: Path
    catalog_path: Path
    catalog: dict[str, Any]
    manifests: dict[str, dict[str, Any]]
    manifest_paths: dict[str, Path]


@dataclass(frozen=True)
class ValidationIssue:
    """One deterministic catalog contract violation."""

    code: str
    path: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class ValidationReport:
    """Catalog verdict and normalized summary."""

    passed: bool
    issues: tuple[ValidationIssue, ...]
    summary: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)
