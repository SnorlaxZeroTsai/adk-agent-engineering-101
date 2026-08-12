"""Mutation fixtures for misleading catalog entries."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

from .contracts import DiscoveryBundle


def load_invalid_cases(path: Path) -> tuple[dict[str, Any], ...]:
    value = json.loads(path.read_text(encoding="utf-8"))
    cases = value.get("cases")
    if value.get("schema_version") != "1.0" or not isinstance(cases, list):
        raise ValueError("invalid fixture contract")
    return tuple(cases)


def _resolve_path(value: Any, path: list[Any]) -> tuple[Any, Any]:
    if not path:
        raise ValueError("mutation path must not be empty")
    current = value
    for part in path[:-1]:
        current = current[part]
    return current, path[-1]


def apply_invalid_case(
    bundle: DiscoveryBundle,
    case: dict[str, Any],
) -> DiscoveryBundle:
    """Return an isolated bundle with one deliberate catalog mutation."""

    mutated = DiscoveryBundle(
        root=bundle.root,
        catalog=deepcopy(bundle.catalog),
        metadata=deepcopy(bundle.metadata),
        schema=deepcopy(bundle.schema),
    )
    parent, key = _resolve_path(mutated.catalog, case["path"])
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
