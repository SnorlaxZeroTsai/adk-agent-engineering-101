"""Deterministic validation for pattern manifests and their relation graph."""

from __future__ import annotations

from collections import Counter
import re
from typing import Any

from .contracts import CatalogBundle
from .contracts import ValidationIssue
from .contracts import ValidationReport


ID_RE = re.compile(r"^[a-z][a-z0-9-]*$")
PINNED_GITHUB_RE = re.compile(
    r"^https://github\.com/(?P<owner>[^/]+)/(?P<repository>[^/]+)/blob/"
    r"(?P<commit>[0-9a-f]{40})/.+"
)
LOCKED_SOURCE_RE = re.compile(
    r'url:\s*"(?P<url>https://github\.com/[^"]+)"\s*\n'
    r'\s*commit:\s*"(?P<commit>[0-9a-f]{40})"'
)
VALID_STATUSES = {"candidate", "validated", "rejected"}
VALID_PORTABILITY = {"portable", "version-specific"}
VALID_RELATIONS = {"constrains", "depends-on", "specializes", "verifies"}
PATTERN_FIELDS = {
    "schema_version",
    "id",
    "name",
    "status",
    "portability",
    "doc",
    "summary",
    "context",
    "forces",
    "decision",
    "implementation",
    "observable_contract",
    "failure_modes",
    "counterexamples",
    "adk_versions",
    "source_evidence",
    "lab_evidence",
    "rejected_decisions",
}
CATALOG_FIELDS = {
    "schema_version",
    "patterns",
    "relations",
    "decision_boundaries",
}
REQUIRED_DOC_SECTIONS = (
    "## Problem",
    "## Context",
    "## Forces",
    "## Decision",
    "## Architecture",
    "## Observable Contract",
    "## When To Use",
    "## When Not To Use",
    "## Implementation",
    "## Failure Modes",
    "## Counterexamples",
    "## ADK Versions",
    "## Evidence",
    "## Rejected Decisions",
)


def _issue(
    issues: list[ValidationIssue],
    code: str,
    path: str,
    message: str,
) -> None:
    issues.append(ValidationIssue(code=code, path=path, message=message))


def _valid_id(value: Any) -> bool:
    return isinstance(value, str) and bool(ID_RE.fullmatch(value))


def _require_fields(
    value: dict[str, Any],
    required: set[str],
    path: str,
    issues: list[ValidationIssue],
) -> None:
    for field in sorted(required - value.keys()):
        _issue(
            issues,
            "required_field_missing",
            f"{path}.{field}",
            "required field is absent",
        )
    for field in sorted(value.keys() - required):
        _issue(
            issues,
            "unknown_field",
            f"{path}.{field}",
            "field is not part of the catalog contract",
        )


def _validate_string_list(
    value: Any,
    path: str,
    issues: list[ValidationIssue],
) -> None:
    if not isinstance(value, list):
        _issue(issues, "field_type_invalid", path, "expected an array")
        return
    if not value:
        _issue(issues, "array_empty", path, "array must not be empty")
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            _issue(
                issues,
                "string_empty",
                f"{path}[{index}]",
                "expected a non-empty string",
            )


def _safe_repository_path(
    root,
    raw_path: Any,
    path: str,
    issues: list[ValidationIssue],
):
    if not isinstance(raw_path, str) or not raw_path:
        _issue(issues, "path_invalid", path, "expected a non-empty path")
        return None
    resolved = (root / raw_path).resolve()
    if not resolved.is_relative_to(root):
        _issue(issues, "path_outside_repository", path, raw_path)
        return None
    return resolved


def _locked_sources(bundle: CatalogBundle) -> dict[str, str]:
    lock_path = bundle.root / "references" / "upstream-lock.yaml"
    if not lock_path.is_file():
        return {}
    return {
        match.group("url"): match.group("commit")
        for match in LOCKED_SOURCE_RE.finditer(
            lock_path.read_text(encoding="utf-8")
        )
    }


def _validate_evidence_definitions(
    pattern: dict[str, Any],
    manifest_path: str,
    bundle: CatalogBundle,
    issues: list[ValidationIssue],
) -> tuple[set[str], set[str]]:
    locked_sources = _locked_sources(bundle)
    source_ids: set[str] = set()
    sources = pattern.get("source_evidence")
    if not isinstance(sources, list):
        _issue(
            issues,
            "field_type_invalid",
            f"{manifest_path}.source_evidence",
            "expected an array",
        )
    else:
        if not sources:
            _issue(
                issues,
                "array_empty",
                f"{manifest_path}.source_evidence",
                "source evidence must not be empty",
            )
        for index, item in enumerate(sources):
            item_path = f"{manifest_path}.source_evidence[{index}]"
            if not isinstance(item, dict):
                _issue(issues, "field_type_invalid", item_path, "expected object")
                continue
            _require_fields(item, {"id", "ref", "claim"}, item_path, issues)
            evidence_id = item.get("id")
            if not _valid_id(evidence_id):
                _issue(
                    issues,
                    "id_invalid",
                    f"{item_path}.id",
                    "evidence ID must use lowercase kebab-case",
                )
            elif evidence_id in source_ids:
                _issue(
                    issues,
                    "evidence_id_duplicate",
                    f"{item_path}.id",
                    str(evidence_id),
                )
            else:
                source_ids.add(evidence_id)
            ref = item.get("ref")
            match = (
                PINNED_GITHUB_RE.fullmatch(ref)
                if isinstance(ref, str)
                else None
            )
            if match is None:
                _issue(
                    issues,
                    "source_not_pinned",
                    f"{item_path}.ref",
                    "source URL must contain a full 40-character Git commit",
                )
            else:
                repository_url = (
                    "https://github.com/"
                    f"{match.group('owner')}/{match.group('repository')}"
                )
                locked_commit = locked_sources.get(repository_url)
                if locked_commit is None:
                    _issue(
                        issues,
                        "source_repository_not_locked",
                        f"{item_path}.ref",
                        "source repository is absent from upstream-lock.yaml",
                    )
                elif match.group("commit") != locked_commit:
                    _issue(
                        issues,
                        "source_commit_not_locked",
                        f"{item_path}.ref",
                        "source commit does not match the locked repository",
                    )
            if not isinstance(item.get("claim"), str) or not item["claim"].strip():
                _issue(
                    issues,
                    "string_empty",
                    f"{item_path}.claim",
                    "source claim must not be empty",
                )

    lab_ids: set[str] = set()
    labs = pattern.get("lab_evidence")
    if not isinstance(labs, list):
        _issue(
            issues,
            "field_type_invalid",
            f"{manifest_path}.lab_evidence",
            "expected an array",
        )
    else:
        if not labs:
            _issue(
                issues,
                "array_empty",
                f"{manifest_path}.lab_evidence",
                "lab evidence must not be empty",
            )
        for index, item in enumerate(labs):
            item_path = f"{manifest_path}.lab_evidence[{index}]"
            if not isinstance(item, dict):
                _issue(issues, "field_type_invalid", item_path, "expected object")
                continue
            _require_fields(item, {"id", "path", "claim"}, item_path, issues)
            evidence_id = item.get("id")
            if not _valid_id(evidence_id):
                _issue(
                    issues,
                    "id_invalid",
                    f"{item_path}.id",
                    "evidence ID must use lowercase kebab-case",
                )
            elif evidence_id in lab_ids:
                _issue(
                    issues,
                    "evidence_id_duplicate",
                    f"{item_path}.id",
                    str(evidence_id),
                )
            else:
                lab_ids.add(evidence_id)
            resolved = _safe_repository_path(
                bundle.root,
                item.get("path"),
                f"{item_path}.path",
                issues,
            )
            if resolved is not None and not resolved.is_file():
                _issue(
                    issues,
                    "lab_path_missing",
                    f"{item_path}.path",
                    str(item.get("path")),
                )
            if not isinstance(item.get("claim"), str) or not item["claim"].strip():
                _issue(
                    issues,
                    "string_empty",
                    f"{item_path}.claim",
                    "lab claim must not be empty",
                )
    return source_ids, lab_ids


def _validate_evidenced_claims(
    pattern: dict[str, Any],
    field: str,
    manifest_path: str,
    source_ids: set[str],
    lab_ids: set[str],
    issues: list[ValidationIssue],
) -> set[str]:
    claims = pattern.get(field)
    claim_ids: set[str] = set()
    field_path = f"{manifest_path}.{field}"
    if not isinstance(claims, list):
        _issue(issues, "field_type_invalid", field_path, "expected an array")
        return claim_ids
    if not claims:
        _issue(issues, "array_empty", field_path, "claims must not be empty")
    for index, claim in enumerate(claims):
        claim_path = f"{field_path}[{index}]"
        if not isinstance(claim, dict):
            _issue(issues, "field_type_invalid", claim_path, "expected object")
            continue
        _require_fields(claim, {"id", "statement", "evidence"}, claim_path, issues)
        claim_id = claim.get("id")
        if not _valid_id(claim_id):
            _issue(
                issues,
                "id_invalid",
                f"{claim_path}.id",
                "claim ID must use lowercase kebab-case",
            )
        elif claim_id in claim_ids:
            _issue(
                issues,
                "claim_id_duplicate",
                f"{claim_path}.id",
                str(claim_id),
            )
        else:
            claim_ids.add(claim_id)
        statement = claim.get("statement")
        if not isinstance(statement, str) or not statement.strip():
            _issue(
                issues,
                "string_empty",
                f"{claim_path}.statement",
                "claim statement must not be empty",
            )
        refs = claim.get("evidence")
        if not isinstance(refs, list):
            _issue(
                issues,
                "field_type_invalid",
                f"{claim_path}.evidence",
                "expected an array",
            )
            continue
        kinds = {
            ref.split(":", 1)[0]
            for ref in refs
            if isinstance(ref, str) and ":" in ref
        }
        if not {"source", "lab"}.issubset(kinds):
            _issue(
                issues,
                "claim_evidence_kinds_missing",
                f"{claim_path}.evidence",
                "every claim requires at least one source and one lab reference",
            )
        for ref in refs:
            if not isinstance(ref, str) or ":" not in ref:
                _issue(
                    issues,
                    "evidence_ref_invalid",
                    f"{claim_path}.evidence",
                    str(ref),
                )
                continue
            kind, evidence_id = ref.split(":", 1)
            if kind == "source":
                known = source_ids
            elif kind == "lab":
                known = lab_ids
            else:
                known = set()
            if evidence_id not in known:
                _issue(
                    issues,
                    "evidence_ref_unknown",
                    f"{claim_path}.evidence",
                    ref,
                )
    return claim_ids


def _validate_markdown(
    pattern: dict[str, Any],
    manifest_path: str,
    documented_ids: set[str],
    bundle: CatalogBundle,
    issues: list[ValidationIssue],
) -> None:
    resolved = _safe_repository_path(
        bundle.root,
        pattern.get("doc"),
        f"{manifest_path}.doc",
        issues,
    )
    if resolved is None or not resolved.is_file():
        _issue(
            issues,
            "doc_path_missing",
            f"{manifest_path}.doc",
            str(pattern.get("doc")),
        )
        return
    text = resolved.read_text(encoding="utf-8")
    if f"# {pattern.get('name')}" not in text:
        _issue(
            issues,
            "doc_name_mismatch",
            f"{manifest_path}.doc",
            "Markdown H1 must match manifest name",
        )
    if f"Status: `{pattern.get('status')}`." not in text:
        _issue(
            issues,
            "doc_status_mismatch",
            f"{manifest_path}.doc",
            "Markdown status must match manifest",
        )
    if f"Portability: `{pattern.get('portability')}`." not in text:
        _issue(
            issues,
            "doc_portability_mismatch",
            f"{manifest_path}.doc",
            "Markdown portability must match manifest",
        )
    if f"manifests/{pattern.get('id')}.json" not in text:
        _issue(
            issues,
            "doc_manifest_link_missing",
            f"{manifest_path}.doc",
            "Markdown card must link its canonical manifest",
        )
    for section in REQUIRED_DOC_SECTIONS:
        if section not in text:
            _issue(
                issues,
                "doc_section_missing",
                f"{manifest_path}.doc",
                section,
            )
    for documented_id in sorted(documented_ids):
        if f"`{documented_id}`" not in text:
            _issue(
                issues,
                "doc_claim_id_missing",
                f"{manifest_path}.doc",
                documented_id,
            )


def _validate_pattern(
    pattern: dict[str, Any],
    manifest_path: str,
    bundle: CatalogBundle,
    issues: list[ValidationIssue],
) -> None:
    _require_fields(pattern, PATTERN_FIELDS, manifest_path, issues)
    if pattern.get("schema_version") != "1.0":
        _issue(
            issues,
            "schema_version_invalid",
            f"{manifest_path}.schema_version",
            "expected 1.0",
        )
    pattern_id = pattern.get("id")
    if not _valid_id(pattern_id):
        _issue(
            issues,
            "id_invalid",
            f"{manifest_path}.id",
            "pattern ID must use lowercase kebab-case",
        )
    if isinstance(pattern_id, str) and not manifest_path.endswith(
        f"/{pattern_id}.json"
    ):
        _issue(
            issues,
            "manifest_id_mismatch",
            f"{manifest_path}.id",
            "manifest filename must match pattern ID",
        )
    for field in ("name", "summary"):
        if not isinstance(pattern.get(field), str) or not pattern[field].strip():
            _issue(
                issues,
                "string_empty",
                f"{manifest_path}.{field}",
                "expected a non-empty string",
            )
    if pattern.get("status") not in VALID_STATUSES:
        _issue(
            issues,
            "status_invalid",
            f"{manifest_path}.status",
            str(pattern.get("status")),
        )
    if pattern.get("portability") not in VALID_PORTABILITY:
        _issue(
            issues,
            "portability_invalid",
            f"{manifest_path}.portability",
            str(pattern.get("portability")),
        )
    for field in ("context", "forces", "decision", "implementation"):
        _validate_string_list(
            pattern.get(field),
            f"{manifest_path}.{field}",
            issues,
        )

    source_ids, lab_ids = _validate_evidence_definitions(
        pattern,
        manifest_path,
        bundle,
        issues,
    )
    contract_ids = _validate_evidenced_claims(
        pattern,
        "observable_contract",
        manifest_path,
        source_ids,
        lab_ids,
        issues,
    )
    failure_ids = _validate_evidenced_claims(
        pattern,
        "failure_modes",
        manifest_path,
        source_ids,
        lab_ids,
        issues,
    )
    duplicates = contract_ids & failure_ids
    for claim_id in sorted(duplicates):
        _issue(
            issues,
            "claim_id_duplicate",
            manifest_path,
            claim_id,
        )

    counterexamples = pattern.get("counterexamples")
    if not isinstance(counterexamples, list):
        _issue(
            issues,
            "field_type_invalid",
            f"{manifest_path}.counterexamples",
            "expected an array",
        )
    elif not counterexamples:
        _issue(
            issues,
            "array_empty",
            f"{manifest_path}.counterexamples",
            "counterexamples must not be empty",
        )
    else:
        for index, item in enumerate(counterexamples):
            item_path = f"{manifest_path}.counterexamples[{index}]"
            if not isinstance(item, dict):
                _issue(issues, "field_type_invalid", item_path, "expected object")
                continue
            _require_fields(item, {"context", "preferred"}, item_path, issues)
            for field in ("context", "preferred"):
                if not isinstance(item.get(field), str) or not item[field].strip():
                    _issue(
                        issues,
                        "string_empty",
                        f"{item_path}.{field}",
                        "expected a non-empty string",
                    )

    versions = pattern.get("adk_versions")
    validated_version = False
    if not isinstance(versions, list):
        _issue(
            issues,
            "field_type_invalid",
            f"{manifest_path}.adk_versions",
            "expected an array",
        )
    elif not versions:
        _issue(
            issues,
            "array_empty",
            f"{manifest_path}.adk_versions",
            "version evidence must not be empty",
        )
    else:
        for index, item in enumerate(versions):
            item_path = f"{manifest_path}.adk_versions[{index}]"
            if not isinstance(item, dict):
                _issue(issues, "field_type_invalid", item_path, "expected object")
                continue
            _require_fields(
                item,
                {"version", "support", "notes"},
                item_path,
                issues,
            )
            if item.get("support") == "validated":
                validated_version = True
            if item.get("support") not in {
                "validated",
                "comparative",
                "not-validated",
            }:
                _issue(
                    issues,
                    "version_support_invalid",
                    f"{item_path}.support",
                    str(item.get("support")),
                )
            for field in ("version", "notes"):
                if not isinstance(item.get(field), str) or not item[field].strip():
                    _issue(
                        issues,
                        "string_empty",
                        f"{item_path}.{field}",
                        "expected a non-empty string",
                    )
    if (
        pattern.get("portability") == "version-specific"
        and not validated_version
    ):
        _issue(
            issues,
            "version_specific_unvalidated",
            f"{manifest_path}.adk_versions",
            "version-specific pattern needs one validated runtime version",
        )

    rejected_ids: set[str] = set()
    rejected = pattern.get("rejected_decisions")
    if not isinstance(rejected, list):
        _issue(
            issues,
            "field_type_invalid",
            f"{manifest_path}.rejected_decisions",
            "expected an array",
        )
    elif not rejected:
        _issue(
            issues,
            "array_empty",
            f"{manifest_path}.rejected_decisions",
            "at least one rejected decision is required",
        )
    else:
        for index, item in enumerate(rejected):
            item_path = f"{manifest_path}.rejected_decisions[{index}]"
            if not isinstance(item, dict):
                _issue(issues, "field_type_invalid", item_path, "expected object")
                continue
            _require_fields(
                item,
                {"id", "decision", "reason", "replacement"},
                item_path,
                issues,
            )
            item_id = item.get("id")
            if not _valid_id(item_id):
                _issue(
                    issues,
                    "id_invalid",
                    f"{item_path}.id",
                    "rejected decision ID must use lowercase kebab-case",
                )
            elif item_id in rejected_ids:
                _issue(
                    issues,
                    "rejected_decision_duplicate",
                    f"{item_path}.id",
                    str(item_id),
                )
            else:
                rejected_ids.add(item_id)
            for field in ("decision", "reason", "replacement"):
                if not isinstance(item.get(field), str) or not item[field].strip():
                    _issue(
                        issues,
                        "string_empty",
                        f"{item_path}.{field}",
                        "expected a non-empty string",
                    )

    _validate_markdown(
        pattern,
        manifest_path,
        contract_ids | failure_ids | rejected_ids,
        bundle,
        issues,
    )


def _validate_relations(
    catalog: dict[str, Any],
    pattern_ids: set[str],
    issues: list[ValidationIssue],
) -> None:
    relations = catalog.get("relations")
    if not isinstance(relations, list):
        _issue(issues, "field_type_invalid", "catalog.relations", "expected array")
        return
    if not relations:
        _issue(issues, "array_empty", "catalog.relations", "relations required")
    seen: set[tuple[str, str, str]] = set()
    covered: set[str] = set()
    for index, relation in enumerate(relations):
        path = f"catalog.relations[{index}]"
        if not isinstance(relation, dict):
            _issue(issues, "field_type_invalid", path, "expected object")
            continue
        _require_fields(
            relation,
            {"source", "type", "target", "reason"},
            path,
            issues,
        )
        source = relation.get("source")
        target = relation.get("target")
        relation_type = relation.get("type")
        for field, value in (("source", source), ("target", target)):
            if value not in pattern_ids:
                _issue(
                    issues,
                    "relation_pattern_unknown",
                    f"{path}.{field}",
                    str(value),
                )
            elif isinstance(value, str):
                covered.add(value)
        if source == target:
            _issue(
                issues,
                "relation_self_reference",
                path,
                str(source),
            )
        if relation_type not in VALID_RELATIONS:
            _issue(
                issues,
                "relation_type_invalid",
                f"{path}.type",
                str(relation_type),
            )
        key = (str(source), str(relation_type), str(target))
        if key in seen:
            _issue(issues, "relation_duplicate", path, str(key))
        seen.add(key)
        reason = relation.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            _issue(
                issues,
                "string_empty",
                f"{path}.reason",
                "relation reason must not be empty",
            )
    for pattern_id in sorted(pattern_ids - covered):
        _issue(
            issues,
            "relation_coverage_missing",
            "catalog.relations",
            pattern_id,
        )


def _validate_boundaries(
    catalog: dict[str, Any],
    pattern_ids: set[str],
    issues: list[ValidationIssue],
) -> None:
    boundaries = catalog.get("decision_boundaries")
    if not isinstance(boundaries, list):
        _issue(
            issues,
            "field_type_invalid",
            "catalog.decision_boundaries",
            "expected array",
        )
        return
    if not boundaries:
        _issue(
            issues,
            "array_empty",
            "catalog.decision_boundaries",
            "decision boundaries required",
        )
    seen: set[str] = set()
    covered: set[str] = set()
    for index, boundary in enumerate(boundaries):
        path = f"catalog.decision_boundaries[{index}]"
        if not isinstance(boundary, dict):
            _issue(issues, "field_type_invalid", path, "expected object")
            continue
        _require_fields(
            boundary,
            {
                "id",
                "patterns",
                "tension",
                "resolution",
                "rejected_decision",
            },
            path,
            issues,
        )
        boundary_id = boundary.get("id")
        if not _valid_id(boundary_id):
            _issue(issues, "id_invalid", f"{path}.id", str(boundary_id))
        elif boundary_id in seen:
            _issue(
                issues,
                "decision_boundary_duplicate",
                f"{path}.id",
                str(boundary_id),
            )
        else:
            seen.add(boundary_id)
        members = boundary.get("patterns")
        if not isinstance(members, list) or len(members) < 2:
            _issue(
                issues,
                "decision_boundary_too_small",
                f"{path}.patterns",
                "at least two patterns are required",
            )
        else:
            for member in members:
                if member not in pattern_ids:
                    _issue(
                        issues,
                        "decision_boundary_pattern_unknown",
                        f"{path}.patterns",
                        str(member),
                    )
                elif isinstance(member, str):
                    covered.add(member)
        for field in ("tension", "resolution", "rejected_decision"):
            if not isinstance(boundary.get(field), str) or not boundary[field].strip():
                _issue(
                    issues,
                    "string_empty",
                    f"{path}.{field}",
                    "expected a non-empty string",
                )
    for pattern_id in sorted(pattern_ids - covered):
        _issue(
            issues,
            "decision_boundary_coverage_missing",
            "catalog.decision_boundaries",
            pattern_id,
        )


def validate_catalog(bundle: CatalogBundle) -> ValidationReport:
    """Validate index, manifests, Markdown cards and cross-pattern decisions."""

    issues: list[ValidationIssue] = []
    catalog = bundle.catalog
    _require_fields(catalog, CATALOG_FIELDS, "catalog", issues)
    if catalog.get("schema_version") != "1.0":
        _issue(
            issues,
            "schema_version_invalid",
            "catalog.schema_version",
            "expected 1.0",
        )

    entries = catalog.get("patterns")
    pattern_ids: set[str] = set()
    manifest_names: set[str] = set()
    if not isinstance(entries, list):
        _issue(issues, "field_type_invalid", "catalog.patterns", "expected array")
        entries = []
    elif not entries:
        _issue(issues, "array_empty", "catalog.patterns", "patterns required")
    for index, entry in enumerate(entries):
        path = f"catalog.patterns[{index}]"
        if not isinstance(entry, dict):
            _issue(issues, "field_type_invalid", path, "expected object")
            continue
        _require_fields(entry, {"id", "manifest"}, path, issues)
        pattern_id = entry.get("id")
        manifest_name = entry.get("manifest")
        if not _valid_id(pattern_id):
            _issue(issues, "id_invalid", f"{path}.id", str(pattern_id))
        elif pattern_id in pattern_ids:
            _issue(
                issues,
                "catalog_pattern_duplicate",
                f"{path}.id",
                str(pattern_id),
            )
        else:
            pattern_ids.add(pattern_id)
        if not isinstance(manifest_name, str) or not manifest_name:
            _issue(
                issues,
                "path_invalid",
                f"{path}.manifest",
                str(manifest_name),
            )
        elif manifest_name in manifest_names:
            _issue(
                issues,
                "catalog_manifest_duplicate",
                f"{path}.manifest",
                manifest_name,
            )
        else:
            manifest_names.add(manifest_name)
        resolved = _safe_repository_path(
            bundle.root,
            manifest_name,
            f"{path}.manifest",
            issues,
        )
        if resolved is not None and not resolved.is_file():
            _issue(
                issues,
                "manifest_path_missing",
                f"{path}.manifest",
                str(manifest_name),
            )
        manifest = bundle.manifests.get(str(pattern_id))
        if manifest is None:
            _issue(
                issues,
                "manifest_not_loaded",
                f"{path}.manifest",
                str(manifest_name),
            )
            continue
        if manifest.get("id") != pattern_id:
            _issue(
                issues,
                "catalog_manifest_id_mismatch",
                f"{path}.id",
                str(pattern_id),
            )
        _validate_pattern(
            manifest,
            str(manifest_name),
            bundle,
            issues,
        )

    manifest_dir = bundle.root / "patterns" / "manifests"
    actual_manifests = {
        str(path.relative_to(bundle.root))
        for path in manifest_dir.glob("*.json")
    }
    for extra in sorted(actual_manifests - manifest_names):
        _issue(
            issues,
            "manifest_unindexed",
            "catalog.patterns",
            extra,
        )

    _validate_relations(catalog, pattern_ids, issues)
    _validate_boundaries(catalog, pattern_ids, issues)

    loaded = [
        bundle.manifests[pattern_id]
        for pattern_id in sorted(pattern_ids)
        if pattern_id in bundle.manifests
    ]
    summary = {
        "pattern_count": len(pattern_ids),
        "status": dict(sorted(Counter(
            item.get("status") for item in loaded
        ).items())),
        "portability": dict(sorted(Counter(
            item.get("portability") for item in loaded
        ).items())),
        "observable_contract_count": sum(
            len(item.get("observable_contract", [])) for item in loaded
        ),
        "failure_mode_count": sum(
            len(item.get("failure_modes", [])) for item in loaded
        ),
        "rejected_decision_count": sum(
            len(item.get("rejected_decisions", [])) for item in loaded
        ),
        "relation_count": len(catalog.get("relations", []))
        if isinstance(catalog.get("relations"), list)
        else 0,
        "decision_boundary_count": len(
            catalog.get("decision_boundaries", [])
        )
        if isinstance(catalog.get("decision_boundaries"), list)
        else 0,
    }
    return ValidationReport(
        passed=not issues,
        issues=tuple(issues),
        summary=summary,
    )
