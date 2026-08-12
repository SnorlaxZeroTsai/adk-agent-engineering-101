"""Deterministic Blueprint schema migration."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from .contracts import MigrationResult


def migrate_v0_1_to_v1(value: dict[str, Any]) -> MigrationResult:
    """Migrate the supported flat single-Agent v0.1 contract to v1.0."""

    if value.get("schema_version") != "0.1":
        raise ValueError("only Blueprint schema version 0.1 is supported")
    if value.get("architecture_kind") != "single-agent":
        raise ValueError("v0.1 migration only supports single-agent")
    entrypoint_path, entrypoint_symbol = value["entrypoint_ref"].split(
        "#",
        1,
    )
    catalog_ref = {
        "entry_id": value["catalog_entry_id"],
        "implementation_id": value["implementation_id"],
    }
    blueprint = {
        "schema_version": "1.0",
        "id": value["id"],
        "catalog_ref": catalog_ref,
        "architecture": {
            "kind": value["architecture_kind"],
            "root_agent": value["root_agent"],
            "model_slot": value["model"]["id"],
            "tools": deepcopy(value["tools"]),
        },
        "runtime": {
            "entrypoint": {
                "path": entrypoint_path,
                "symbol": entrypoint_symbol,
            },
            "model_slots": [deepcopy(value["model"])],
            "services": deepcopy(value["services"]),
            "state_contracts": deepcopy(value["state_contracts"]),
            "retrieval_contracts": [],
        },
        "policy": {
            "enforcement_refs": deepcopy(value["enforcement_refs"]),
            "approval": deepcopy(value["approval"]),
            "credentials": deepcopy(value["credentials"]),
        },
        "evaluation": {
            "dataset_ref": value["dataset_ref"],
            "gate_ref": value["gate_ref"],
            "blocking_metrics": deepcopy(value["blocking_metrics"]),
        },
        "lifecycle": {
            "production_profile_ref": value["production_profile_ref"],
            "upgrade_policy": value["upgrade_policy"],
            "rollback_contract_ref": value["rollback_contract_ref"],
        },
        "extensions": deepcopy(value["extensions"]),
    }
    return MigrationResult(
        source_version="0.1",
        target_version="1.0",
        source_id=value["id"],
        target_id=blueprint["id"],
        catalog_ref_preserved=(
            catalog_ref["entry_id"] == value["catalog_entry_id"]
            and catalog_ref["implementation_id"]
            == value["implementation_id"]
        ),
        blueprint=blueprint,
    )
