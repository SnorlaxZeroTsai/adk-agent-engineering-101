"""Discoverability suite aggregation and exit semantics."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .fixtures import apply_invalid_case
from .fixtures import load_invalid_cases
from .loader import load_discovery_bundle
from .projection import assess_source_surfaces
from .projection import catalog_fact_coverage
from .validation import validate_discovery_bundle


def build_gate_report(
    variant: str,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    """Build the baseline report or deliberate misleading-entry report."""

    bundle = load_discovery_bundle(root)
    if variant == "baseline":
        validation = validate_discovery_bundle(bundle)
        entries = bundle.catalog.get("entries", [])
        coverage = (
            catalog_fact_coverage(entries[0])
            if isinstance(entries, list) and entries
            else {"provided": [], "complete": False}
        )
        return {
            "variant": variant,
            "passed": validation.passed and coverage["complete"],
            "validation": validation.as_dict(),
            "source_surfaces": assess_source_surfaces(bundle.metadata),
            "catalog_coverage": coverage,
        }
    if variant != "broken":
        raise ValueError(f"unknown variant: {variant}")
    fixture_path = (
        Path(__file__).resolve().parents[1]
        / "fixtures"
        / "misleading_cases.json"
    )
    cases = []
    for case in load_invalid_cases(fixture_path):
        report = validate_discovery_bundle(
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
        "all_misleading_cases_detected": all(
            item["detected"] for item in cases
        ),
        "cases": cases,
    }


def exit_code(report: dict[str, Any]) -> int:
    return 0 if report["passed"] else 1
