"""Coverage projections for source metadata and the registry contract."""

from __future__ import annotations

from typing import Any


def assess_source_surfaces(metadata: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    """Report which required discovery facts each upstream surface provides."""

    required = set(metadata["required_discovery_facts"])
    assessments = []
    for contract in metadata["source_contracts"]:
        provided = set(contract["provides"])
        assessments.append(
            {
                "id": contract["id"],
                "provided": sorted(provided),
                "missing": sorted(required - provided),
                "complete": required <= provided,
            }
        )
    return tuple(assessments)


def catalog_fact_coverage(entry: dict[str, Any]) -> dict[str, Any]:
    """Map one catalog entry to the minimum discovery fact set."""

    implementations = entry.get("implementations")
    assurance = entry.get("assurance")
    provided = {
        "stable_identity"
        if isinstance(entry.get("id"), str) and entry["id"]
        else "",
        "display"
        if entry.get("display_name") and entry.get("summary")
        else "",
        "lifecycle" if isinstance(entry.get("lifecycle"), dict) else "",
        "ownership" if isinstance(entry.get("ownership"), dict) else "",
        "classification"
        if isinstance(entry.get("classification"), dict)
        else "",
        "immutable_source"
        if isinstance(implementations, list) and implementations
        else "",
        "compatibility"
        if isinstance(implementations, list) and implementations
        else "",
        "reuse_locator"
        if isinstance(implementations, list) and implementations
        else "",
        "assurance" if isinstance(assurance, list) and assurance else "",
    }
    provided.discard("")
    return {
        "provided": sorted(provided),
        "complete": len(provided) == 9,
    }
