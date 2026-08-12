"""Load Agent Garden discovery artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .contracts import DiscoveryBundle


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def find_repository_root(start: Path | None = None) -> Path:
    """Find the learning repository from a lab file or directory."""

    current = (start or Path(__file__)).resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / "agent-garden" / "discovery-catalog.json").is_file():
            return candidate
    raise FileNotFoundError("agent-garden/discovery-catalog.json was not found")


def load_discovery_bundle(root: Path | None = None) -> DiscoveryBundle:
    """Load the canonical discovery artifacts."""

    repository = (root or find_repository_root()).resolve()
    garden = repository / "agent-garden"
    return DiscoveryBundle(
        root=repository,
        catalog=_load_json(garden / "discovery-catalog.json"),
        metadata=_load_json(garden / "metadata-surfaces.json"),
        schema=_load_json(garden / "catalog-entry.schema.json"),
    )
