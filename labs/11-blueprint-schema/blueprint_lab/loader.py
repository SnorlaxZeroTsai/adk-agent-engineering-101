"""Load the Agent Garden Blueprint artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .contracts import BlueprintBundle


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
        schema_path = (
            candidate
            / "agent-garden"
            / "blueprints"
            / "schema"
            / "blueprint.schema.json"
        )
        if schema_path.is_file():
            return candidate
    raise FileNotFoundError("Blueprint schema was not found")


def load_blueprint_bundle(root: Path | None = None) -> BlueprintBundle:
    """Load the canonical catalog snapshot, schema, and examples."""

    repository = (root or find_repository_root()).resolve()
    garden = repository / "agent-garden"
    blueprint_root = garden / "blueprints"
    paths = sorted((blueprint_root / "examples").glob("*.json"))
    loaded = [(path, _load_json(path)) for path in paths]
    blueprints = {
        value["id"]: value
        for path, value in loaded
    }
    blueprint_paths = {
        value["id"]: path
        for path, value in loaded
    }
    return BlueprintBundle(
        root=repository,
        schema=_load_json(
            blueprint_root / "schema" / "blueprint.schema.json"
        ),
        catalog_schema=_load_json(garden / "catalog-entry.schema.json"),
        catalog=_load_json(blueprint_root / "catalog-snapshot.json"),
        blueprints=blueprints,
        blueprint_paths=blueprint_paths,
    )
