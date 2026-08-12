"""Mutation fixtures for invalid MVP component boundaries."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

from .contracts import ArchitectureBundle


def load_invalid_cases(path: Path) -> tuple[dict[str, Any], ...]:
    value = json.loads(path.read_text(encoding="utf-8"))
    cases = value.get("cases")
    if value.get("schema_version") != "1.0" or not isinstance(cases, list):
        raise ValueError("invalid MVP architecture fixture contract")
    return tuple(cases)


def _resolve_path(value: Any, path: list[Any]) -> tuple[Any, Any]:
    if not path:
        raise ValueError("mutation path must not be empty")
    current = value
    for part in path[:-1]:
        current = current[part]
    return current, path[-1]


def apply_invalid_case(
    bundle: ArchitectureBundle,
    case: dict[str, Any],
) -> ArchitectureBundle:
    mutated = ArchitectureBundle(
        root=bundle.root,
        architecture=deepcopy(bundle.architecture),
        schema=deepcopy(bundle.schema),
        blueprints=deepcopy(bundle.blueprints),
        catalog=deepcopy(bundle.catalog),
    )
    parent, key = _resolve_path(mutated.architecture, case["path"])
    operation = case["operation"]
    if operation == "set":
        parent[key] = deepcopy(case["value"])
    elif operation == "remove":
        del parent[key]
    elif operation == "append":
        parent[key].append(deepcopy(case["value"]))
    else:
        raise ValueError(f"unknown fixture operation: {operation}")
    return mutated
