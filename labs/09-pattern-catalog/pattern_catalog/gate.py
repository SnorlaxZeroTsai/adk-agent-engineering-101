"""Catalog gate aggregation and process exit semantics."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .fixtures import apply_invalid_case
from .fixtures import load_invalid_cases
from .loader import load_catalog_bundle
from .validation import validate_catalog


def build_gate_report(
    variant: str,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    """Build the valid catalog report or the deliberate invalid-case bundle."""

    bundle = load_catalog_bundle(root)
    if variant == "baseline":
        report = validate_catalog(bundle)
        return {
            "variant": variant,
            "passed": report.passed,
            "validation": report.as_dict(),
        }
    if variant != "broken":
        raise ValueError(f"unknown variant: {variant}")
    fixture_path = (
        Path(__file__).resolve().parents[1]
        / "fixtures"
        / "invalid_cases.json"
    )
    cases = []
    for case in load_invalid_cases(fixture_path):
        report = validate_catalog(apply_invalid_case(bundle, case))
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
