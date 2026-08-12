"""Resolve ADR, Markdown, JSON Pointer, and Python contract references."""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

from .contracts import ValidationIssue


def _issue(
    issues: list[ValidationIssue],
    code: str,
    path: str,
    message: str,
) -> None:
    issues.append(ValidationIssue(code=code, path=path, message=message))


def _safe_path(root: Path, raw_path: str) -> Path | None:
    value = (root / raw_path).resolve()
    return value if value.is_relative_to(root) else None


def _module_symbols(source: str) -> set[str]:
    tree = ast.parse(source)
    symbols: set[str] = set()
    for node in tree.body:
        if isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
        ):
            symbols.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    symbols.add(target.id)
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name):
                symbols.add(node.target.id)
    return symbols


def _json_pointer(value: Any, pointer: str) -> Any:
    current = value
    for part in pointer.lstrip("/").split("/"):
        if not part:
            continue
        key = part.replace("~1", "/").replace("~0", "~")
        if isinstance(current, list):
            current = current[int(key)]
        else:
            current = current[key]
    return current


def validate_repository_ref(
    root: Path,
    value: Any,
    path: str,
    issues: list[ValidationIssue],
) -> None:
    if not isinstance(value, str) or "#" not in value:
        _issue(
            issues,
            "repository_ref_invalid",
            path,
            "expected repository/path#fragment",
        )
        return
    raw_path, fragment = value.split("#", 1)
    file_path = _safe_path(root, raw_path)
    if file_path is None:
        _issue(issues, "repository_ref_outside", path, raw_path)
        return
    if not file_path.is_file():
        _issue(issues, "repository_ref_file_missing", path, raw_path)
        return
    if file_path.suffix == ".py":
        try:
            symbols = _module_symbols(file_path.read_text(encoding="utf-8"))
        except SyntaxError as error:
            _issue(issues, "repository_ref_python_invalid", path, str(error))
            return
        if fragment not in symbols:
            _issue(
                issues,
                "repository_ref_symbol_missing",
                path,
                fragment,
            )
    elif file_path.suffix == ".md":
        headings = {
            line.lstrip("#").strip()
            for line in file_path.read_text(encoding="utf-8").splitlines()
            if line.startswith("#")
        }
        if fragment not in headings:
            _issue(
                issues,
                "repository_ref_heading_missing",
                path,
                fragment,
            )
    elif file_path.suffix == ".json":
        try:
            _json_pointer(
                json.loads(file_path.read_text(encoding="utf-8")),
                fragment,
            )
        except (KeyError, IndexError, TypeError, ValueError) as error:
            _issue(
                issues,
                "repository_ref_pointer_missing",
                path,
                str(error),
            )
    else:
        _issue(
            issues,
            "repository_ref_type_unsupported",
            path,
            file_path.suffix,
        )


def validate_adr(
    root: Path,
    value: dict[str, Any],
    path: str,
    issues: list[ValidationIssue],
) -> None:
    raw_path = value.get("path")
    file_path = _safe_path(root, raw_path) if isinstance(raw_path, str) else None
    if file_path is None or not file_path.is_file():
        _issue(issues, "adr_file_missing", f"{path}.path", str(raw_path))
        return
    text = file_path.read_text(encoding="utf-8")
    for section in (
        "Status: Accepted",
        "## Context",
        "## Decision",
        "## Consequences",
        "## Evidence",
    ):
        if section not in text:
            _issue(
                issues,
                "adr_section_missing",
                f"{path}.path",
                section,
            )
