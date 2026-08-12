"""Deterministic validation for Agent Garden discoverability metadata."""

from __future__ import annotations

from collections import Counter
import re
from typing import Any

from .contracts import DiscoveryBundle
from .contracts import ValidationIssue
from .contracts import ValidationReport
from .projection import catalog_fact_coverage


ID_RE = re.compile(r"^[a-z][a-z0-9-]*$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
PINNED_BLOB_RE = re.compile(
    r"^(?P<repository>https://github\.com/[^/]+/[^/]+)/blob/"
    r"(?P<revision>[0-9a-f]{40})/(?P<path>.+)$"
)
PINNED_TREE_RE = re.compile(
    r"^(?P<repository>https://github\.com/[^/]+/[^/]+)/tree/"
    r"(?P<revision>[0-9a-f]{40})/(?P<path>.+)$"
)
LOCKED_SOURCE_RE = re.compile(
    r'url:\s*"(?P<url>https://github\.com/[^"]+)"\s*\n'
    r'\s*commit:\s*"(?P<commit>[0-9a-f]{40})"'
)

VALID_PLANES = {"catalog", "scaffold", "runtime", "governance"}
VALID_STATUSES = {"active", "deprecated", "retired"}
VALID_KINDS = {"standalone", "module"}
VALID_REUSE_MODES = {"reference", "remote-template", "import"}
VALID_ASSURANCE_KINDS = {"structure", "runnability", "behavior"}

CATALOG_FIELDS = {"schema_version", "entries"}
ENTRY_FIELDS = {
    "id",
    "display_name",
    "summary",
    "lifecycle",
    "ownership",
    "classification",
    "implementations",
    "assurance",
}
LIFECYCLE_FIELDS = {"status", "replacement_id"}
OWNERSHIP_FIELDS = {"team", "contacts"}
CLASSIFICATION_FIELDS = {"kind", "tags"}
IMPLEMENTATION_FIELDS = {
    "id",
    "status",
    "language",
    "framework",
    "source",
    "reuse",
}
FRAMEWORK_FIELDS = {"package", "version_constraint"}
SOURCE_FIELDS = {"repository", "revision", "path"}
REUSE_FIELDS = {"mode", "template_ref"}
ASSURANCE_FIELDS = {"kind", "implementation_id", "ref", "digest"}


def _issue(
    issues: list[ValidationIssue],
    code: str,
    path: str,
    message: str,
) -> None:
    issues.append(ValidationIssue(code=code, path=path, message=message))


def _require_fields(
    value: dict[str, Any],
    expected: set[str],
    path: str,
    issues: list[ValidationIssue],
) -> None:
    for field in sorted(expected - value.keys()):
        _issue(
            issues,
            "required_field_missing",
            f"{path}.{field}",
            "required field is absent",
        )
    for field in sorted(value.keys() - expected):
        _issue(
            issues,
            "unknown_field",
            f"{path}.{field}",
            "field belongs to another metadata authority",
        )


def _require_text(
    value: Any,
    path: str,
    issues: list[ValidationIssue],
    *,
    minimum: int = 1,
) -> bool:
    if not isinstance(value, str) or len(value.strip()) < minimum:
        _issue(issues, "text_invalid", path, "expected non-empty text")
        return False
    return True


def _validate_string_list(
    value: Any,
    path: str,
    issues: list[ValidationIssue],
) -> list[str]:
    if not isinstance(value, list):
        _issue(issues, "field_type_invalid", path, "expected an array")
        return []
    if not value:
        _issue(issues, "array_empty", path, "array must not be empty")
    result = []
    for index, item in enumerate(value):
        if not _require_text(item, f"{path}[{index}]", issues):
            continue
        result.append(item)
    if len(result) != len(set(result)):
        _issue(issues, "array_duplicate", path, "values must be unique")
    return result


def _locked_sources(bundle: DiscoveryBundle) -> dict[str, str]:
    lock_path = bundle.root / "references" / "upstream-lock.yaml"
    if not lock_path.is_file():
        return {}
    return {
        match.group("url"): match.group("commit")
        for match in LOCKED_SOURCE_RE.finditer(
            lock_path.read_text(encoding="utf-8")
        )
    }


def _validate_pinned_url(
    value: Any,
    pattern: re.Pattern[str],
    path: str,
    locked_sources: dict[str, str],
    issues: list[ValidationIssue],
) -> re.Match[str] | None:
    match = pattern.fullmatch(value) if isinstance(value, str) else None
    if match is None:
        _issue(
            issues,
            "source_not_pinned",
            path,
            "expected a full Git commit in the source URL",
        )
        return None
    repository = match.group("repository")
    revision = match.group("revision")
    if repository not in locked_sources:
        _issue(
            issues,
            "source_repository_not_locked",
            path,
            repository,
        )
    elif locked_sources[repository] != revision:
        _issue(
            issues,
            "source_revision_not_locked",
            path,
            revision,
        )
    return match


def _validate_metadata(
    bundle: DiscoveryBundle,
    issues: list[ValidationIssue],
) -> None:
    metadata = bundle.metadata
    if metadata.get("schema_version") != "1.0":
        _issue(
            issues,
            "metadata_schema_version_invalid",
            "metadata.schema_version",
            "expected 1.0",
        )
    plane_ids = {
        item.get("id")
        for item in metadata.get("planes", [])
        if isinstance(item, dict)
    }
    if plane_ids != VALID_PLANES:
        _issue(
            issues,
            "ownership_planes_invalid",
            "metadata.planes",
            str(sorted(plane_ids)),
        )
    required = metadata.get("required_discovery_facts")
    required_facts = set(
        _validate_string_list(
            required,
            "metadata.required_discovery_facts",
            issues,
        )
    )
    locked_sources = _locked_sources(bundle)
    observations = bundle.metadata.get("consumer_observations")
    if not isinstance(observations, list) or not observations:
        _issue(
            issues,
            "consumer_observations_invalid",
            "metadata.consumer_observations",
            "expected pinned consumer behavior evidence",
        )
    else:
        observation_ids = []
        for index, observation in enumerate(observations):
            path = f"metadata.consumer_observations[{index}]"
            if not isinstance(observation, dict):
                _issue(
                    issues,
                    "field_type_invalid",
                    path,
                    "expected object",
                )
                continue
            observation_ids.append(observation.get("id"))
            _validate_pinned_url(
                observation.get("source"),
                PINNED_BLOB_RE,
                f"{path}.source",
                locked_sources,
                issues,
            )
            _require_text(
                observation.get("finding"),
                f"{path}.finding",
                issues,
                minimum=10,
            )
        if len(observation_ids) != len(set(observation_ids)):
            _issue(
                issues,
                "consumer_observation_duplicate",
                "metadata.consumer_observations",
                "observation IDs must be unique",
            )
    covered_planes: set[str] = set()
    contracts = metadata.get("source_contracts")
    if not isinstance(contracts, list) or not contracts:
        _issue(
            issues,
            "source_contracts_invalid",
            "metadata.source_contracts",
            "expected source contracts",
        )
        return
    contract_ids = []
    for index, contract in enumerate(contracts):
        path = f"metadata.source_contracts[{index}]"
        if not isinstance(contract, dict):
            _issue(issues, "field_type_invalid", path, "expected object")
            continue
        contract_ids.append(contract.get("id"))
        _validate_pinned_url(
            contract.get("source"),
            PINNED_BLOB_RE,
            f"{path}.source",
            locked_sources,
            issues,
        )
        provides = set(
            _validate_string_list(
                contract.get("provides"),
                f"{path}.provides",
                issues,
            )
        )
        if not provides <= required_facts:
            _issue(
                issues,
                "surface_fact_unknown",
                f"{path}.provides",
                str(sorted(provides - required_facts)),
            )
        fields = contract.get("fields")
        if not isinstance(fields, list) or not fields:
            _issue(
                issues,
                "surface_fields_empty",
                f"{path}.fields",
                "field-level comparison is required",
            )
            continue
        names = []
        for field_index, field in enumerate(fields):
            field_path = f"{path}.fields[{field_index}]"
            if not isinstance(field, dict):
                _issue(
                    issues,
                    "field_type_invalid",
                    field_path,
                    "expected object",
                )
                continue
            names.append(field.get("field"))
            planes = set(
                _validate_string_list(
                    field.get("planes"),
                    f"{field_path}.planes",
                    issues,
                )
            )
            covered_planes.update(planes)
            if not planes <= VALID_PLANES:
                _issue(
                    issues,
                    "ownership_plane_unknown",
                    f"{field_path}.planes",
                    str(sorted(planes - VALID_PLANES)),
                )
        if len(names) != len(set(names)):
            _issue(
                issues,
                "surface_field_duplicate",
                f"{path}.fields",
                "field names must be unique within a source contract",
            )
    if len(contract_ids) != len(set(contract_ids)):
        _issue(
            issues,
            "source_contract_duplicate",
            "metadata.source_contracts",
            "contract IDs must be unique",
        )
    if covered_planes != VALID_PLANES:
        _issue(
            issues,
            "ownership_plane_uncovered",
            "metadata.source_contracts",
            str(sorted(VALID_PLANES - covered_planes)),
        )


def _facts_by_source(
    metadata: dict[str, Any],
) -> dict[tuple[str, str, str], dict[str, Any]]:
    facts = {}
    for item in metadata.get("implementation_facts", []):
        source = item.get("source", {})
        key = (
            source.get("repository"),
            source.get("revision"),
            source.get("path"),
        )
        facts[key] = item
    return facts


def _validate_lifecycle(
    value: Any,
    path: str,
    issues: list[ValidationIssue],
) -> str | None:
    if not isinstance(value, dict):
        _issue(issues, "field_type_invalid", path, "expected object")
        return None
    _require_fields(value, LIFECYCLE_FIELDS, path, issues)
    status = value.get("status")
    replacement = value.get("replacement_id")
    if status not in VALID_STATUSES:
        _issue(
            issues,
            "lifecycle_status_invalid",
            f"{path}.status",
            str(status),
        )
    if status == "active" and replacement is not None:
        _issue(
            issues,
            "active_replacement_invalid",
            f"{path}.replacement_id",
            "active entries do not declare a replacement",
        )
    if status in {"deprecated", "retired"} and not _require_text(
        replacement,
        f"{path}.replacement_id",
        issues,
    ):
        _issue(
            issues,
            "replacement_required",
            f"{path}.replacement_id",
            "deprecated and retired entries require a replacement",
        )
    return status if isinstance(status, str) else None


def _validate_ownership(
    value: Any,
    path: str,
    issues: list[ValidationIssue],
) -> tuple[str | None, list[str]]:
    if not isinstance(value, dict):
        _issue(issues, "field_type_invalid", path, "expected object")
        return None, []
    _require_fields(value, OWNERSHIP_FIELDS, path, issues)
    team = value.get("team")
    _require_text(team, f"{path}.team", issues)
    contacts = _validate_string_list(
        value.get("contacts"),
        f"{path}.contacts",
        issues,
    )
    if not contacts:
        _issue(
            issues,
            "owner_contacts_empty",
            f"{path}.contacts",
            "at least one accountable contact is required",
        )
    return team if isinstance(team, str) else None, contacts


def _validate_classification(
    value: Any,
    path: str,
    issues: list[ValidationIssue],
) -> tuple[str | None, list[str]]:
    if not isinstance(value, dict):
        _issue(issues, "field_type_invalid", path, "expected object")
        return None, []
    _require_fields(value, CLASSIFICATION_FIELDS, path, issues)
    kind = value.get("kind")
    if kind not in VALID_KINDS:
        _issue(
            issues,
            "classification_kind_invalid",
            f"{path}.kind",
            str(kind),
        )
    tags = _validate_string_list(value.get("tags"), f"{path}.tags", issues)
    for index, tag in enumerate(tags):
        if not ID_RE.fullmatch(tag):
            _issue(
                issues,
                "tag_invalid",
                f"{path}.tags[{index}]",
                tag,
            )
    return kind if isinstance(kind, str) else None, tags


def _validate_source(
    value: Any,
    path: str,
    locked_sources: dict[str, str],
    frozen_prefixes: tuple[str, ...],
    status: Any,
    issues: list[ValidationIssue],
) -> tuple[str, str, str] | None:
    if not isinstance(value, dict):
        _issue(issues, "field_type_invalid", path, "expected object")
        return None
    _require_fields(value, SOURCE_FIELDS, path, issues)
    repository = value.get("repository")
    revision = value.get("revision")
    source_path = value.get("path")
    if not isinstance(repository, str) or repository not in locked_sources:
        _issue(
            issues,
            "source_repository_not_locked",
            f"{path}.repository",
            str(repository),
        )
    if not isinstance(revision, str) or not SHA_RE.fullmatch(revision):
        _issue(
            issues,
            "source_revision_unpinned",
            f"{path}.revision",
            "expected a full 40-character Git commit",
        )
    elif isinstance(repository, str) and (
        locked_sources.get(repository) != revision
    ):
        _issue(
            issues,
            "source_revision_not_locked",
            f"{path}.revision",
            revision,
        )
    if (
        not isinstance(source_path, str)
        or not source_path
        or source_path.startswith("/")
        or ".." in source_path.split("/")
    ):
        _issue(
            issues,
            "source_path_invalid",
            f"{path}.path",
            str(source_path),
        )
    elif status == "active" and source_path.startswith(frozen_prefixes):
        _issue(
            issues,
            "active_source_frozen",
            f"{path}.path",
            source_path,
        )
    if not all(isinstance(item, str) for item in (repository, revision, source_path)):
        return None
    return repository, revision, source_path


def _validate_framework(
    value: Any,
    path: str,
    issues: list[ValidationIssue],
) -> tuple[str | None, str | None]:
    if not isinstance(value, dict):
        _issue(issues, "field_type_invalid", path, "expected object")
        return None, None
    _require_fields(value, FRAMEWORK_FIELDS, path, issues)
    package = value.get("package")
    constraint = value.get("version_constraint")
    _require_text(package, f"{path}.package", issues)
    _require_text(constraint, f"{path}.version_constraint", issues)
    return (
        package if isinstance(package, str) else None,
        constraint if isinstance(constraint, str) else None,
    )


def _validate_reuse(
    value: Any,
    path: str,
    source_key: tuple[str, str, str] | None,
    locked_sources: dict[str, str],
    issues: list[ValidationIssue],
) -> tuple[str | None, str | None]:
    if not isinstance(value, dict):
        _issue(issues, "field_type_invalid", path, "expected object")
        return None, None
    _require_fields(value, REUSE_FIELDS, path, issues)
    mode = value.get("mode")
    template_ref = value.get("template_ref")
    if mode not in VALID_REUSE_MODES:
        _issue(issues, "reuse_mode_invalid", f"{path}.mode", str(mode))
    if mode == "remote-template":
        match = _validate_pinned_url(
            template_ref,
            PINNED_TREE_RE,
            f"{path}.template_ref",
            locked_sources,
            issues,
        )
        if match is not None and source_key is not None:
            observed = (
                match.group("repository"),
                match.group("revision"),
                match.group("path"),
            )
            if observed != source_key:
                _issue(
                    issues,
                    "reuse_source_mismatch",
                    f"{path}.template_ref",
                    str(observed),
                )
    elif template_ref is not None:
        _issue(
            issues,
            "reuse_template_ref_unexpected",
            f"{path}.template_ref",
            "only remote-template mode uses template_ref",
        )
    return (
        mode if isinstance(mode, str) else None,
        template_ref if isinstance(template_ref, str) else None,
    )


def _validate_entry(
    entry: Any,
    index: int,
    bundle: DiscoveryBundle,
    locked_sources: dict[str, str],
    facts_by_source: dict[tuple[str, str, str], dict[str, Any]],
    issues: list[ValidationIssue],
) -> tuple[str | None, list[tuple[str, str, str]], set[str]]:
    path = f"catalog.entries[{index}]"
    if not isinstance(entry, dict):
        _issue(issues, "field_type_invalid", path, "expected object")
        return None, [], set()
    _require_fields(entry, ENTRY_FIELDS, path, issues)
    catalog_id = entry.get("id")
    if not isinstance(catalog_id, str) or not ID_RE.fullmatch(catalog_id):
        _issue(
            issues,
            "catalog_id_invalid",
            f"{path}.id",
            str(catalog_id),
        )
    _require_text(entry.get("display_name"), f"{path}.display_name", issues)
    _require_text(entry.get("summary"), f"{path}.summary", issues, minimum=10)
    lifecycle_status = _validate_lifecycle(
        entry.get("lifecycle"),
        f"{path}.lifecycle",
        issues,
    )
    owner_team, owner_contacts = _validate_ownership(
        entry.get("ownership"),
        f"{path}.ownership",
        issues,
    )
    kind, tags = _validate_classification(
        entry.get("classification"),
        f"{path}.classification",
        issues,
    )
    implementations = entry.get("implementations")
    if not isinstance(implementations, list) or not implementations:
        _issue(
            issues,
            "implementations_empty",
            f"{path}.implementations",
            "at least one implementation is required",
        )
        implementations = []
    implementation_ids: list[str] = []
    source_keys: list[tuple[str, str, str]] = []
    implementation_facts: dict[str, dict[str, Any]] = {}
    frozen = tuple(bundle.metadata.get("frozen_source_prefixes", []))
    for implementation_index, implementation in enumerate(implementations):
        impl_path = f"{path}.implementations[{implementation_index}]"
        if not isinstance(implementation, dict):
            _issue(
                issues,
                "field_type_invalid",
                impl_path,
                "expected object",
            )
            continue
        _require_fields(
            implementation,
            IMPLEMENTATION_FIELDS,
            impl_path,
            issues,
        )
        implementation_id = implementation.get("id")
        if not isinstance(implementation_id, str) or not ID_RE.fullmatch(
            implementation_id
        ):
            _issue(
                issues,
                "implementation_id_invalid",
                f"{impl_path}.id",
                str(implementation_id),
            )
        else:
            implementation_ids.append(implementation_id)
        status = implementation.get("status")
        if status not in VALID_STATUSES:
            _issue(
                issues,
                "implementation_status_invalid",
                f"{impl_path}.status",
                str(status),
            )
        language = implementation.get("language")
        _require_text(language, f"{impl_path}.language", issues)
        framework = _validate_framework(
            implementation.get("framework"),
            f"{impl_path}.framework",
            issues,
        )
        source_key = _validate_source(
            implementation.get("source"),
            f"{impl_path}.source",
            locked_sources,
            frozen,
            status,
            issues,
        )
        reuse = _validate_reuse(
            implementation.get("reuse"),
            f"{impl_path}.reuse",
            source_key,
            locked_sources,
            issues,
        )
        if source_key is None:
            continue
        source_keys.append(source_key)
        fact = facts_by_source.get(source_key)
        if fact is None:
            _issue(
                issues,
                "implementation_facts_missing",
                f"{impl_path}.source",
                str(source_key),
            )
            continue
        if isinstance(implementation_id, str):
            implementation_facts[implementation_id] = fact
        expected_pairs = (
            ("catalog_identity_mismatch", catalog_id, fact["catalog_id"], path),
            (
                "lifecycle_status_mismatch",
                lifecycle_status,
                fact["lifecycle_status"],
                f"{path}.lifecycle.status",
            ),
            (
                "owner_team_mismatch",
                owner_team,
                fact["owner_team"],
                f"{path}.ownership.team",
            ),
            (
                "owner_contacts_mismatch",
                owner_contacts,
                fact["owner_contacts"],
                f"{path}.ownership.contacts",
            ),
            (
                "classification_kind_mismatch",
                kind,
                fact["kind"],
                f"{path}.classification.kind",
            ),
            (
                "classification_tags_mismatch",
                tags,
                fact["tags"],
                f"{path}.classification.tags",
            ),
            (
                "implementation_id_mismatch",
                implementation_id,
                fact["implementation_id"],
                f"{impl_path}.id",
            ),
            (
                "implementation_status_mismatch",
                status,
                fact["lifecycle_status"],
                f"{impl_path}.status",
            ),
            (
                "implementation_language_mismatch",
                language,
                fact["language"],
                f"{impl_path}.language",
            ),
            (
                "framework_package_mismatch",
                framework[0],
                fact["framework"]["package"],
                f"{impl_path}.framework.package",
            ),
            (
                "framework_constraint_mismatch",
                framework[1],
                fact["framework"]["version_constraint"],
                f"{impl_path}.framework.version_constraint",
            ),
            (
                "reuse_mode_mismatch",
                reuse[0],
                fact["reuse"]["mode"],
                f"{impl_path}.reuse.mode",
            ),
            (
                "reuse_ref_mismatch",
                reuse[1],
                fact["reuse"]["template_ref"],
                f"{impl_path}.reuse.template_ref",
            ),
        )
        for code, actual, expected, issue_path in expected_pairs:
            if actual != expected:
                _issue(issues, code, issue_path, f"{actual!r} != {expected!r}")
    if len(implementation_ids) != len(set(implementation_ids)):
        _issue(
            issues,
            "implementation_id_duplicate",
            f"{path}.implementations",
            "implementation IDs must be unique",
        )
    assurance = entry.get("assurance")
    assured_ids: set[str] = set()
    if not isinstance(assurance, list) or not assurance:
        _issue(
            issues,
            "assurance_empty",
            f"{path}.assurance",
            "at least one assurance artifact is required",
        )
        assurance = []
    for assurance_index, item in enumerate(assurance):
        item_path = f"{path}.assurance[{assurance_index}]"
        if not isinstance(item, dict):
            _issue(
                issues,
                "field_type_invalid",
                item_path,
                "expected object",
            )
            continue
        _require_fields(item, ASSURANCE_FIELDS, item_path, issues)
        kind_value = item.get("kind")
        if kind_value not in VALID_ASSURANCE_KINDS:
            _issue(
                issues,
                "assurance_kind_invalid",
                f"{item_path}.kind",
                str(kind_value),
            )
        implementation_id = item.get("implementation_id")
        if implementation_id not in implementation_ids:
            _issue(
                issues,
                "assurance_implementation_unknown",
                f"{item_path}.implementation_id",
                str(implementation_id),
            )
        elif isinstance(implementation_id, str):
            assured_ids.add(implementation_id)
        match = _validate_pinned_url(
            item.get("ref"),
            PINNED_BLOB_RE,
            f"{item_path}.ref",
            locked_sources,
            issues,
        )
        digest = item.get("digest")
        if not isinstance(digest, str) or not DIGEST_RE.fullmatch(digest):
            _issue(
                issues,
                "assurance_digest_invalid",
                f"{item_path}.digest",
                str(digest),
            )
        fact = implementation_facts.get(implementation_id)
        if fact is not None:
            expected = fact["assurance"]
            actual_ref = item.get("ref")
            actual_kind = item.get("kind")
            if actual_ref != expected["ref"]:
                _issue(
                    issues,
                    "assurance_ref_mismatch",
                    f"{item_path}.ref",
                    str(actual_ref),
                )
            if digest != expected["digest"]:
                _issue(
                    issues,
                    "assurance_digest_mismatch",
                    f"{item_path}.digest",
                    str(digest),
                )
            if actual_kind != expected["kind"]:
                _issue(
                    issues,
                    "assurance_kind_mismatch",
                    f"{item_path}.kind",
                    str(actual_kind),
                )
        if match is not None and implementation_id in implementation_facts:
            source = implementation_facts[implementation_id]["source"]
            observed = (
                match.group("repository"),
                match.group("revision"),
            )
            expected_source = (source["repository"], source["revision"])
            if observed != expected_source:
                _issue(
                    issues,
                    "assurance_source_mismatch",
                    f"{item_path}.ref",
                    str(observed),
                )
    missing_assurance = set(implementation_ids) - assured_ids
    if missing_assurance:
        _issue(
            issues,
            "implementation_unassured",
            f"{path}.assurance",
            str(sorted(missing_assurance)),
        )
    coverage = catalog_fact_coverage(entry)
    required = set(bundle.metadata.get("required_discovery_facts", []))
    if set(coverage["provided"]) != required:
        _issue(
            issues,
            "discovery_fact_missing",
            path,
            str(sorted(required - set(coverage["provided"]))),
        )
    return (
        catalog_id if isinstance(catalog_id, str) else None,
        source_keys,
        assured_ids,
    )


def validate_discovery_bundle(bundle: DiscoveryBundle) -> ValidationReport:
    """Validate source ownership and the minimal discovery catalog."""

    issues: list[ValidationIssue] = []
    _validate_metadata(bundle, issues)
    catalog = bundle.catalog
    _require_fields(catalog, CATALOG_FIELDS, "catalog", issues)
    if catalog.get("schema_version") != "1.0":
        _issue(
            issues,
            "catalog_schema_version_invalid",
            "catalog.schema_version",
            "expected 1.0",
        )
    locked_sources = _locked_sources(bundle)
    facts = _facts_by_source(bundle.metadata)
    entries = catalog.get("entries")
    if not isinstance(entries, list) or not entries:
        _issue(
            issues,
            "catalog_entries_empty",
            "catalog.entries",
            "at least one catalog entry is required",
        )
        entries = []
    entry_ids: list[str] = []
    source_owners: list[tuple[tuple[str, str, str], str | None]] = []
    for index, entry in enumerate(entries):
        entry_id, source_keys, _ = _validate_entry(
            entry,
            index,
            bundle,
            locked_sources,
            facts,
            issues,
        )
        if entry_id is not None:
            entry_ids.append(entry_id)
        source_owners.extend((source, entry_id) for source in source_keys)
    for entry_id, count in Counter(entry_ids).items():
        if count > 1:
            _issue(
                issues,
                "catalog_id_duplicate",
                "catalog.entries",
                entry_id,
            )
    source_counts = Counter(source for source, _ in source_owners)
    for source, count in source_counts.items():
        owners = {
            owner for candidate, owner in source_owners if candidate == source
        }
        if count > 1 and len(owners) > 1:
            _issue(
                issues,
                "implementation_source_duplicate",
                "catalog.entries",
                str(source),
            )
    source_contracts = bundle.metadata.get("source_contracts", [])
    field_count = sum(
        len(item.get("fields", []))
        for item in source_contracts
        if isinstance(item, dict)
    )
    plane_counts = Counter(
        plane
        for contract in source_contracts
        if isinstance(contract, dict)
        for field in contract.get("fields", [])
        if isinstance(field, dict)
        for plane in field.get("planes", [])
    )
    summary = {
        "source_contract_count": len(source_contracts),
        "consumer_observation_count": len(
            bundle.metadata.get("consumer_observations", [])
        ),
        "source_field_count": field_count,
        "plane_field_counts": dict(sorted(plane_counts.items())),
        "required_discovery_fact_count": len(
            bundle.metadata.get("required_discovery_facts", [])
        ),
        "catalog_entry_count": len(entries),
        "implementation_count": sum(
            len(entry.get("implementations", []))
            for entry in entries
            if isinstance(entry, dict)
        ),
        "assurance_count": sum(
            len(entry.get("assurance", []))
            for entry in entries
            if isinstance(entry, dict)
        ),
    }
    ordered = tuple(sorted(issues, key=lambda item: (item.path, item.code)))
    return ValidationReport(
        passed=not ordered,
        issues=ordered,
        summary=summary,
    )
