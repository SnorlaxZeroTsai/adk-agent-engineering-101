"""Blueprint suite aggregation, migration evidence, and exit semantics."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .fixtures import apply_invalid_case
from .fixtures import load_invalid_cases
from .loader import load_blueprint_bundle
from .migration import migrate_v0_1_to_v1
from .validation import validate_blueprint_bundle


LAB_ROOT = Path(__file__).resolve().parents[1]


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def build_gate_report(
    variant: str,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    """Build the valid suite or deliberate cross-domain breakage report."""

    bundle = load_blueprint_bundle(root)
    if variant == "baseline":
        validation = validate_blueprint_bundle(bundle)
        legacy = _load_json(
            LAB_ROOT / "fixtures" / "order-support-v0.1.json"
        )
        migration = migrate_v0_1_to_v1(legacy)
        migration_matches = (
            migration.blueprint
            == bundle.blueprints["order-support-read-only"]
        )
        return {
            "variant": variant,
            "passed": (
                validation.passed
                and migration.catalog_ref_preserved
                and migration_matches
            ),
            "validation": validation.as_dict(),
            "migration": {
                "source_version": migration.source_version,
                "target_version": migration.target_version,
                "source_id": migration.source_id,
                "target_id": migration.target_id,
                "catalog_ref_preserved": migration.catalog_ref_preserved,
                "matches_canonical_example": migration_matches,
            },
        }
    if variant != "broken":
        raise ValueError(f"unknown variant: {variant}")
    cases = []
    for case in load_invalid_cases(
        LAB_ROOT / "fixtures" / "invalid_cases.json"
    ):
        report = validate_blueprint_bundle(
            apply_invalid_case(bundle, case)
        )
        codes = sorted({issue.code for issue in report.issues})
        expected = case["expected_code"]
        cases.append(
            {
                "case_id": case["id"],
                "detected": not report.passed and expected in codes,
                "expected_code": expected,
                "observed_codes": codes,
            }
        )
    return {
        "variant": variant,
        "passed": False,
        "all_invalid_cases_detected": all(
            item["detected"] for item in cases
        ),
        "cases": cases,
    }


def exit_code(report: dict[str, Any]) -> int:
    return 0 if report["passed"] else 1
