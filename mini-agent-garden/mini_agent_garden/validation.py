"""Contract Validator adapter delegating to the Phase 11 authority."""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

from .contracts import ContractReport
from .errors import ContractValidationError


def _blueprint_api(root: Path) -> tuple[Any, Any, Any, Any]:
    lab_root = root / "labs" / "11-blueprint-schema"
    path = str(lab_root)
    if path not in sys.path:
        sys.path.insert(0, path)
    from blueprint_lab.contracts import BlueprintBundle
    from blueprint_lab.loader import load_blueprint_bundle
    from blueprint_lab.migration import migrate_v0_1_to_v1
    from blueprint_lab.validation import validate_blueprint_bundle

    return (
        BlueprintBundle,
        load_blueprint_bundle,
        migrate_v0_1_to_v1,
        validate_blueprint_bundle,
    )


class ContractValidator:
    """Reuse schema/Git/AST/graph rules without copying them into the CLI."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def validate(self, blueprint: dict[str, Any]) -> ContractReport:
        (
            bundle_type,
            load_bundle,
            _,
            validate_bundle,
        ) = _blueprint_api(self.root)
        canonical = load_bundle(self.root)
        blueprints = dict(canonical.blueprints)
        blueprint_paths = dict(canonical.blueprint_paths)
        blueprint_id = blueprint.get("id")
        if not isinstance(blueprint_id, str):
            raise ContractValidationError("Blueprint id must be a string")
        blueprints[blueprint_id] = blueprint
        blueprint_paths[blueprint_id] = Path("<provided-blueprint>")
        bundle = bundle_type(
            root=canonical.root,
            schema=canonical.schema,
            catalog_schema=canonical.catalog_schema,
            catalog=canonical.catalog,
            blueprints=blueprints,
            blueprint_paths=blueprint_paths,
        )
        report = validate_bundle(bundle)
        result = ContractReport(
            blueprint_id=blueprint_id,
            passed=report.passed,
            issues=tuple(item.as_dict() for item in report.issues),
            suite_summary=report.summary,
        )
        return result

    def require_valid(
        self,
        blueprint: dict[str, Any],
    ) -> ContractReport:
        report = self.validate(blueprint)
        if not report.passed:
            codes = sorted({item["code"] for item in report.issues})
            raise ContractValidationError(
                "Blueprint validation failed: " + ", ".join(codes)
            )
        return report

    def migrate_legacy(
        self,
        blueprint: dict[str, Any],
    ) -> tuple[dict[str, Any], dict[str, Any] | None]:
        if blueprint.get("schema_version") != "0.1":
            return blueprint, None
        _, _, migrate, _ = _blueprint_api(self.root)
        result = migrate(blueprint)
        migration = {
            "source_version": result.source_version,
            "target_version": result.target_version,
            "source_id": result.source_id,
            "target_id": result.target_id,
            "catalog_ref_preserved": result.catalog_ref_preserved,
        }
        return result.blueprint, migration
