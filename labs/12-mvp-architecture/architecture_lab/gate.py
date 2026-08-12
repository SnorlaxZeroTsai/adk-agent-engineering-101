"""MVP architecture aggregation and enforceable exit semantics."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .fixtures import apply_invalid_case
from .fixtures import load_invalid_cases
from .loader import load_architecture_bundle
from .validation import validate_architecture_bundle
from .walkthrough import build_walkthroughs


LAB_ROOT = Path(__file__).resolve().parents[1]


def build_gate_report(
    variant: str,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    bundle = load_architecture_bundle(root)
    if variant == "baseline":
        validation = validate_architecture_bundle(bundle)
        walkthroughs = build_walkthroughs(bundle)
        return {
            "variant": variant,
            "passed": validation.passed,
            "validation": validation.as_dict(),
            "walkthroughs": walkthroughs,
        }
    if variant != "broken":
        raise ValueError(f"unknown variant: {variant}")
    cases = []
    fixtures = load_invalid_cases(
        LAB_ROOT / "fixtures" / "invalid_cases.json"
    )
    for case in fixtures:
        report = validate_architecture_bundle(
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
