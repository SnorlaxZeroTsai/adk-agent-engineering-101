"""Load the machine-readable MVP architecture and Blueprint inputs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .contracts import ArchitectureBundle


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def find_repository_root(start: Path | None = None) -> Path:
    current = (start or Path(__file__)).resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / "agent-garden" / "mvp-architecture.json").is_file():
            return candidate
    raise FileNotFoundError("agent-garden/mvp-architecture.json was not found")


def load_architecture_bundle(root: Path | None = None) -> ArchitectureBundle:
    repository = (root or find_repository_root()).resolve()
    garden = repository / "agent-garden"
    examples = sorted((garden / "blueprints" / "examples").glob("*.json"))
    loaded = [_load_json(path) for path in examples]
    return ArchitectureBundle(
        root=repository,
        architecture=_load_json(garden / "mvp-architecture.json"),
        schema=_load_json(garden / "mvp-architecture.schema.json"),
        blueprints={item["id"]: item for item in loaded},
        catalog=_load_json(garden / "blueprints" / "catalog-snapshot.json"),
    )
