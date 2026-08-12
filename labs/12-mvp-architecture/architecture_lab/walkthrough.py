"""Build deterministic digest-chained lifecycle walkthroughs."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from .contracts import ArchitectureBundle


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _catalog_coordinate(
    bundle: ArchitectureBundle,
    blueprint: dict[str, Any],
) -> dict[str, Any]:
    entry_id = blueprint["catalog_ref"]["entry_id"]
    implementation_id = blueprint["catalog_ref"]["implementation_id"]
    entry = next(
        item
        for item in bundle.catalog["entries"]
        if item["id"] == entry_id
    )
    implementation = next(
        item
        for item in entry["implementations"]
        if item["id"] == implementation_id
    )
    return {
        "entry_id": entry_id,
        "implementation_id": implementation_id,
        "source": implementation["source"],
    }


def build_walkthrough(
    bundle: ArchitectureBundle,
    walkthrough: dict[str, Any],
) -> dict[str, Any]:
    blueprint = bundle.blueprints[walkthrough["blueprint_id"]]
    coordinate = _catalog_coordinate(bundle, blueprint)
    available = {
        "catalog-index": digest(bundle.catalog),
        "blueprint": digest(blueprint),
        "implementation-source": digest(coordinate),
        "secret-reference": digest(
            {
                "secret_id": "runtime-api",
                "version": "7",
                "reference_only": True,
            }
        ),
        "release-record": digest(
            {
                "previous_release": "release-previous",
                "status": "succeeded",
            }
        ),
    }
    stages = {
        stage["id"]: stage
        for stage in bundle.architecture["lifecycle"]["release_path"]
    }
    receipts = []
    for stage_id in walkthrough["stages"]:
        stage = stages[stage_id]
        inputs = {
            artifact: available[artifact]
            for artifact in stage["consumes"]
        }
        base = {
            "blueprint_id": walkthrough["blueprint_id"],
            "architecture": walkthrough["architecture"],
            "target_adapter": walkthrough["target_adapter"],
            "stage": stage_id,
            "component": stage["component"],
            "inputs": inputs,
            "requires": stage["requires"],
        }
        if stage_id == "validate":
            base["validators"] = walkthrough["required_validators"]
        if stage_id == "evaluate":
            base["blocking_metrics"] = walkthrough["required_metrics"]
        outputs = {}
        for artifact in stage["produces"]:
            artifact_digest = digest(
                {
                    "artifact": artifact,
                    "receipt": base,
                }
            )
            available[artifact] = artifact_digest
            outputs[artifact] = artifact_digest
        receipts.append(
            {
                "stage": stage_id,
                "component": stage["component"],
                "inputs": inputs,
                "outputs": outputs,
            }
        )
    return {
        "blueprint_id": walkthrough["blueprint_id"],
        "architecture": walkthrough["architecture"],
        "target_adapter": walkthrough["target_adapter"],
        "stage_receipts": receipts,
        "candidate_digest": available["release-candidate"],
        "behavior_report_digest": available["behavior-report"],
        "release_record_digest": available["release-record"],
        "secret_material_present": False,
    }


def build_walkthroughs(bundle: ArchitectureBundle) -> list[dict[str, Any]]:
    return [
        build_walkthrough(bundle, walkthrough)
        for walkthrough in bundle.architecture["blueprint_walkthroughs"]
    ]
