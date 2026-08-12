"""Resolve worktree symbols and immutable implementation evidence."""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path
import re
import subprocess
from typing import Any

from .contracts import ValidationIssue


LOCAL_REF_RE = re.compile(
    r"^(?P<path>.+\.py)#(?P<symbol>[A-Za-z_][A-Za-z0-9_]*)$"
)
PINNED_BLOB_RE = re.compile(
    r"^(?P<repository>https://github\.com/[^/]+/[^/]+)/blob/"
    r"(?P<revision>[0-9a-f]{40})/(?P<path>.+)$"
)


def _issue(
    issues: list[ValidationIssue],
    code: str,
    path: str,
    message: str,
) -> None:
    issues.append(ValidationIssue(code=code, path=path, message=message))


def _safe_path(
    root: Path,
    raw_path: str,
) -> Path | None:
    resolved = (root / raw_path).resolve()
    if not resolved.is_relative_to(root):
        return None
    return resolved


def module_symbols(source: str) -> set[str]:
    """Return top-level Python definitions and assignments."""

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


def validate_local_ref(
    root: Path,
    value: Any,
    path: str,
    issues: list[ValidationIssue],
) -> None:
    """Require a repository-local Python file and top-level symbol."""

    match = LOCAL_REF_RE.fullmatch(value) if isinstance(value, str) else None
    if match is None:
        _issue(
            issues,
            "local_ref_invalid",
            path,
            "expected path.py#TopLevelSymbol",
        )
        return
    file_path = _safe_path(root, match.group("path"))
    if file_path is None:
        _issue(
            issues,
            "local_ref_outside_repository",
            path,
            str(value),
        )
        return
    if not file_path.is_file():
        _issue(
            issues,
            "local_ref_file_missing",
            path,
            match.group("path"),
        )
        return
    try:
        symbols = module_symbols(file_path.read_text(encoding="utf-8"))
    except SyntaxError as error:
        _issue(
            issues,
            "local_ref_python_invalid",
            path,
            str(error),
        )
        return
    if match.group("symbol") not in symbols:
        _issue(
            issues,
            "local_ref_symbol_missing",
            path,
            match.group("symbol"),
        )


def collect_local_refs(value: Any, path: str = "blueprint") -> list[tuple[str, str]]:
    """Collect every local Python reference with a deterministic JSON path."""

    refs: list[tuple[str, str]] = []
    if isinstance(value, dict):
        for field in sorted(value):
            refs.extend(
                collect_local_refs(value[field], f"{path}.{field}")
            )
    elif isinstance(value, list):
        for index, item in enumerate(value):
            refs.extend(collect_local_refs(item, f"{path}[{index}]"))
    elif isinstance(value, str) and ".py#" in value:
        refs.append((path, value))
    return refs


def _git(
    root: Path,
    *args: str,
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        check=False,
    )


def git_blob(
    root: Path,
    revision: str,
    path: str,
) -> bytes | None:
    result = _git(root, "show", f"{revision}:{path}")
    return result.stdout if result.returncode == 0 else None


def validate_catalog_sources(
    root: Path,
    catalog: dict[str, Any],
    issues: list[ValidationIssue],
) -> None:
    """Verify immutable source, entrypoint evidence, and assurance digests."""

    remote = _git(root, "remote", "get-url", "origin")
    remote_url = remote.stdout.decode().strip().removesuffix(".git")
    for entry_index, entry in enumerate(catalog.get("entries", [])):
        entry_path = f"catalog.entries[{entry_index}]"
        implementations = entry.get("implementations", [])
        assurance = entry.get("assurance", [])
        for impl_index, implementation in enumerate(implementations):
            impl_path = f"{entry_path}.implementations[{impl_index}]"
            source = implementation.get("source", {})
            repository = source.get("repository")
            revision = source.get("revision")
            source_path = source.get("path")
            if repository != remote_url:
                _issue(
                    issues,
                    "implementation_repository_mismatch",
                    f"{impl_path}.source.repository",
                    f"expected {remote_url}",
                )
            if not isinstance(revision, str):
                continue
            commit = _git(root, "cat-file", "-e", f"{revision}^{{commit}}")
            if commit.returncode != 0:
                _issue(
                    issues,
                    "implementation_revision_missing",
                    f"{impl_path}.source.revision",
                    revision,
                )
            if isinstance(source_path, str):
                tree = _git(
                    root,
                    "cat-file",
                    "-e",
                    f"{revision}:{source_path}",
                )
                if tree.returncode != 0:
                    _issue(
                        issues,
                        "implementation_path_missing",
                        f"{impl_path}.source.path",
                        source_path,
                    )
            impl_id = implementation.get("id")
            matches = [
                (index, item)
                for index, item in enumerate(assurance)
                if item.get("implementation_id") == impl_id
            ]
            if not matches:
                _issue(
                    issues,
                    "implementation_assurance_missing",
                    impl_path,
                    str(impl_id),
                )
            for evidence_index, evidence in matches:
                evidence_path = (
                    f"{entry_path}.assurance[{evidence_index}]"
                )
                match = PINNED_BLOB_RE.fullmatch(
                    evidence.get("ref", "")
                )
                if match is None:
                    _issue(
                        issues,
                        "assurance_ref_not_pinned",
                        f"{evidence_path}.ref",
                        str(evidence.get("ref")),
                    )
                    continue
                if (
                    match.group("repository") != repository
                    or match.group("revision") != revision
                ):
                    _issue(
                        issues,
                        "assurance_source_mismatch",
                        f"{evidence_path}.ref",
                        evidence["ref"],
                    )
                    continue
                blob = git_blob(root, revision, match.group("path"))
                if blob is None:
                    _issue(
                        issues,
                        "assurance_blob_missing",
                        f"{evidence_path}.ref",
                        match.group("path"),
                    )
                    continue
                digest = "sha256:" + hashlib.sha256(blob).hexdigest()
                if evidence.get("digest") != digest:
                    _issue(
                        issues,
                        "assurance_digest_mismatch",
                        f"{evidence_path}.digest",
                        digest,
                    )


def validate_pinned_entrypoint(
    root: Path,
    implementation: dict[str, Any],
    entrypoint: dict[str, Any],
    path: str,
    issues: list[ValidationIssue],
) -> None:
    """Resolve the Blueprint entrypoint inside its immutable implementation."""

    source = implementation.get("source", {})
    revision = source.get("revision")
    base_path = source.get("path")
    relative_path = entrypoint.get("path")
    symbol = entrypoint.get("symbol")
    if not all(
        isinstance(item, str)
        for item in (revision, base_path, relative_path, symbol)
    ):
        return
    full_path = f"{base_path.rstrip('/')}/{relative_path}"
    blob = git_blob(root, revision, full_path)
    if blob is None:
        _issue(
            issues,
            "entrypoint_blob_missing",
            f"{path}.path",
            f"{revision}:{full_path}",
        )
        return
    try:
        symbols = module_symbols(blob.decode())
    except (SyntaxError, UnicodeDecodeError) as error:
        _issue(
            issues,
            "entrypoint_python_invalid",
            path,
            str(error),
        )
        return
    if symbol not in symbols:
        _issue(
            issues,
            "entrypoint_symbol_missing",
            f"{path}.symbol",
            symbol,
        )
