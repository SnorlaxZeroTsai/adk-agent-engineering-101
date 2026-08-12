"""Catalog and manifest loading."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .contracts import CatalogBundle


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def find_repository_root(start: Path | None = None) -> Path:
    """Find the repository root from a lab script or test."""

    current = (start or Path(__file__)).resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / "patterns" / "catalog.json").exists():
            return candidate
    raise FileNotFoundError("patterns/catalog.json was not found")


def load_catalog_bundle(root: Path | None = None) -> CatalogBundle:
    """Load the catalog and every index entry that can be resolved."""

    repository = (root or find_repository_root()).resolve()
    catalog_path = repository / "patterns" / "catalog.json"
    catalog = _load_json(catalog_path)
    manifests: dict[str, dict[str, Any]] = {}
    manifest_paths: dict[str, Path] = {}
    entries = catalog.get("patterns", [])
    if isinstance(entries, list):
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            pattern_id = entry.get("id")
            manifest_name = entry.get("manifest")
            if not isinstance(pattern_id, str) or not isinstance(
                manifest_name,
                str,
            ):
                continue
            path = (repository / manifest_name).resolve()
            if not path.exists() or not path.is_file():
                continue
            try:
                manifests[pattern_id] = _load_json(path)
                manifest_paths[pattern_id] = path
            except (json.JSONDecodeError, ValueError):
                continue
    return CatalogBundle(
        root=repository,
        catalog_path=catalog_path,
        catalog=catalog,
        manifests=manifests,
        manifest_paths=manifest_paths,
    )
