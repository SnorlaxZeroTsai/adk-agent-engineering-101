"""Dependency-free validation for the published JSON Schema subset."""

from __future__ import annotations

import json
import re
from typing import Any

from .contracts import ValidationIssue


def _issue(
    issues: list[ValidationIssue],
    code: str,
    path: str,
    message: str,
) -> None:
    issues.append(ValidationIssue(code=code, path=path, message=message))


def _resolve_ref(
    root_schema: dict[str, Any],
    reference: str,
) -> dict[str, Any]:
    if not reference.startswith("#/"):
        raise ValueError(f"only local schema refs are supported: {reference}")
    value: Any = root_schema
    for part in reference[2:].split("/"):
        value = value[part.replace("~1", "/").replace("~0", "~")]
    if not isinstance(value, dict):
        raise ValueError(f"schema ref does not resolve to an object: {reference}")
    return value


def _matches_type(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    raise ValueError(f"unsupported schema type: {expected}")


def _validate_node(
    value: Any,
    schema: dict[str, Any],
    root_schema: dict[str, Any],
    path: str,
    issues: list[ValidationIssue],
) -> None:
    if "$ref" in schema:
        _validate_node(
            value,
            _resolve_ref(root_schema, schema["$ref"]),
            root_schema,
            path,
            issues,
        )
        return

    if "oneOf" in schema:
        matches = 0
        for branch in schema["oneOf"]:
            branch_issues: list[ValidationIssue] = []
            _validate_node(
                value,
                branch,
                root_schema,
                path,
                branch_issues,
            )
            if not branch_issues:
                matches += 1
        if matches != 1:
            _issue(
                issues,
                "schema_one_of",
                path,
                f"expected exactly one matching branch; found {matches}",
            )
        return

    expected_type = schema.get("type")
    if expected_type is not None:
        types = (
            expected_type
            if isinstance(expected_type, list)
            else [expected_type]
        )
        if not any(_matches_type(value, item) for item in types):
            _issue(
                issues,
                "schema_type",
                path,
                f"expected {types}; found {type(value).__name__}",
            )
            return

    if "const" in schema and value != schema["const"]:
        _issue(
            issues,
            "schema_const",
            path,
            f"expected {schema['const']!r}",
        )
    if "enum" in schema and value not in schema["enum"]:
        _issue(
            issues,
            "schema_enum",
            path,
            f"{value!r} is not an allowed value",
        )

    if isinstance(value, dict):
        required = schema.get("required", [])
        for field in required:
            if field not in value:
                _issue(
                    issues,
                    "schema_required",
                    f"{path}.{field}",
                    "required field is absent",
                )
        properties = schema.get("properties", {})
        for field, item in value.items():
            item_path = f"{path}.{field}"
            if field in properties:
                _validate_node(
                    item,
                    properties[field],
                    root_schema,
                    item_path,
                    issues,
                )
            elif schema.get("additionalProperties") is False:
                _issue(
                    issues,
                    "schema_additional_property",
                    item_path,
                    "field is not part of this contract",
                )
            elif isinstance(schema.get("additionalProperties"), dict):
                _validate_node(
                    item,
                    schema["additionalProperties"],
                    root_schema,
                    item_path,
                    issues,
                )
        property_names = schema.get("propertyNames")
        if isinstance(property_names, dict):
            pattern = property_names.get("pattern")
            if pattern:
                for field in value:
                    if re.fullmatch(pattern, field) is None:
                        _issue(
                            issues,
                            "schema_property_name",
                            f"{path}.{field}",
                            f"property does not match {pattern}",
                        )

    if isinstance(value, list):
        minimum = schema.get("minItems")
        if isinstance(minimum, int) and len(value) < minimum:
            _issue(
                issues,
                "schema_min_items",
                path,
                f"expected at least {minimum} items",
            )
        if schema.get("uniqueItems"):
            normalized = [
                json.dumps(item, sort_keys=True, separators=(",", ":"))
                for item in value
            ]
            if len(normalized) != len(set(normalized)):
                _issue(
                    issues,
                    "schema_unique_items",
                    path,
                    "array items must be unique",
                )
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                _validate_node(
                    item,
                    item_schema,
                    root_schema,
                    f"{path}[{index}]",
                    issues,
                )

    if isinstance(value, str):
        minimum = schema.get("minLength")
        if isinstance(minimum, int) and len(value) < minimum:
            _issue(
                issues,
                "schema_min_length",
                path,
                f"expected at least {minimum} characters",
            )
        pattern = schema.get("pattern")
        if pattern and re.fullmatch(pattern, value) is None:
            _issue(
                issues,
                "schema_pattern",
                path,
                f"value does not match {pattern}",
            )

    if (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and "minimum" in schema
        and value < schema["minimum"]
    ):
        _issue(
            issues,
            "schema_minimum",
            path,
            f"value must be at least {schema['minimum']}",
        )


def validate_schema_instance(
    value: Any,
    schema: dict[str, Any],
    *,
    path: str,
) -> tuple[ValidationIssue, ...]:
    """Validate the schema features used by the two published contracts."""

    issues: list[ValidationIssue] = []
    _validate_node(value, schema, schema, path, issues)
    return tuple(issues)
