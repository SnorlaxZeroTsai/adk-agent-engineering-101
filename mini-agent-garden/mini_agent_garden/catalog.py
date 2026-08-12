"""Catalog Registry adapter over the Phase 11 immutable snapshot."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .canonical import load_json
from .contracts import ImplementationSelection
from .errors import UnknownBlueprintError


class CatalogRegistry:
    """Resolve stable entries, Blueprints, and immutable implementations."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        garden = self.root / "agent-garden"
        self.catalog = load_json(
            garden / "blueprints" / "catalog-snapshot.json"
        )
        example_root = garden / "blueprints" / "examples"
        loaded = [
            (path, load_json(path))
            for path in sorted(example_root.glob("*.json"))
        ]
        self.blueprints = {
            value["id"]: value
            for _, value in loaded
        }
        self.blueprint_paths = {
            value["id"]: path
            for path, value in loaded
        }
        self.entries = {
            entry["id"]: entry
            for entry in self.catalog["entries"]
        }

    def list(
        self,
        *,
        architecture: str | None = None,
        tag: str | None = None,
    ) -> list[dict[str, Any]]:
        rows = []
        for blueprint_id in sorted(self.blueprints):
            blueprint = self.blueprints[blueprint_id]
            entry = self.entries[blueprint["catalog_ref"]["entry_id"]]
            kind = blueprint["architecture"]["kind"]
            tags = entry["classification"]["tags"]
            if architecture and kind != architecture:
                continue
            if tag and tag not in tags:
                continue
            rows.append(
                {
                    "blueprint_id": blueprint_id,
                    "entry_id": entry["id"],
                    "display_name": entry["display_name"],
                    "summary": entry["summary"],
                    "architecture": kind,
                    "tags": sorted(tags),
                    "implementation_ids": sorted(
                        item["id"]
                        for item in entry["implementations"]
                    ),
                }
            )
        return rows

    def load_blueprint(
        self,
        reference: str | Path | dict[str, Any],
    ) -> dict[str, Any]:
        if isinstance(reference, dict):
            return reference
        raw = str(reference)
        if raw in self.blueprints:
            return self.blueprints[raw]
        path = Path(raw)
        if not path.is_absolute():
            path = self.root / path
        path = path.resolve()
        if path.is_file() and path.is_relative_to(self.root):
            return load_json(path)
        raise UnknownBlueprintError(f"unknown Blueprint: {reference}")

    def inspect(
        self,
        reference: str | Path | dict[str, Any],
    ) -> dict[str, Any]:
        blueprint = self.load_blueprint(reference)
        entry_id = blueprint["catalog_ref"]["entry_id"]
        entry = self.entries.get(entry_id)
        if entry is None:
            raise UnknownBlueprintError(
                f"Blueprint references unknown CatalogEntry: {entry_id}"
            )
        selection = self.resolve(blueprint)
        return {
            "entry": entry,
            "blueprint": blueprint,
            "selection": selection.as_dict(),
            "selection_digest": selection.digest,
        }

    def resolve(
        self,
        blueprint: dict[str, Any],
    ) -> ImplementationSelection:
        catalog_ref = blueprint.get("catalog_ref", {})
        entry_id = catalog_ref.get("entry_id")
        implementation_id = catalog_ref.get("implementation_id")
        entry = self.entries.get(entry_id)
        if entry is None or entry["lifecycle"]["status"] != "active":
            raise UnknownBlueprintError(
                f"CatalogEntry is unavailable: {entry_id}"
            )
        implementations = {
            item["id"]: item
            for item in entry["implementations"]
        }
        implementation = implementations.get(implementation_id)
        if implementation is None or implementation["status"] != "active":
            raise UnknownBlueprintError(
                f"Implementation is unavailable: {implementation_id}"
            )
        source = implementation["source"]
        framework = implementation["framework"]
        assurance = tuple(
            sorted(
                item["digest"]
                for item in entry["assurance"]
                if item["implementation_id"] == implementation_id
            )
        )
        return ImplementationSelection(
            entry_id=entry_id,
            implementation_id=implementation_id,
            repository=source["repository"],
            revision=source["revision"],
            source_path=source["path"],
            language=implementation["language"],
            framework_package=framework["package"],
            framework_version=framework["version_constraint"],
            assurance_digests=assurance,
        )
