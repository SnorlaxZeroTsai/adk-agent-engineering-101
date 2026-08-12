"""Dependency-free tests for the normalized pattern catalog."""

from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys
import unittest

from pattern_catalog.fixtures import apply_invalid_case
from pattern_catalog.fixtures import load_invalid_cases
from pattern_catalog.gate import build_gate_report
from pattern_catalog.gate import exit_code
from pattern_catalog.loader import find_repository_root
from pattern_catalog.loader import load_catalog_bundle
from pattern_catalog.validation import CATALOG_FIELDS
from pattern_catalog.validation import PATTERN_FIELDS
from pattern_catalog.validation import validate_catalog


LAB_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = find_repository_root(LAB_ROOT)
INVALID_CASES = (
    LAB_ROOT / "fixtures" / "invalid_cases.json"
)


class CatalogContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bundle = load_catalog_bundle(REPOSITORY_ROOT)
        cls.report = validate_catalog(cls.bundle)

    def test_canonical_catalog_passes_without_issues(self) -> None:
        self.assertTrue(self.report.passed)
        self.assertEqual(self.report.issues, ())

    def test_summary_fixes_phase_nine_exit_counts(self) -> None:
        self.assertEqual(
            self.report.summary,
            {
                "pattern_count": 7,
                "status": {"validated": 7},
                "portability": {
                    "portable": 6,
                    "version-specific": 1,
                },
                "observable_contract_count": 28,
                "failure_mode_count": 28,
                "rejected_decision_count": 7,
                "relation_count": 11,
                "decision_boundary_count": 5,
            },
        )

    def test_schema_required_fields_match_stdlib_validator(self) -> None:
        pattern_schema = json.loads(
            (
                REPOSITORY_ROOT
                / "patterns"
                / "schema"
                / "pattern.schema.json"
            ).read_text(encoding="utf-8")
        )
        catalog_schema = json.loads(
            (
                REPOSITORY_ROOT
                / "patterns"
                / "schema"
                / "catalog.schema.json"
            ).read_text(encoding="utf-8")
        )

        self.assertEqual(set(pattern_schema["required"]), PATTERN_FIELDS)
        self.assertEqual(
            set(pattern_schema["properties"]),
            PATTERN_FIELDS,
        )
        self.assertEqual(set(catalog_schema["required"]), CATALOG_FIELDS)
        self.assertEqual(
            set(catalog_schema["properties"]),
            CATALOG_FIELDS,
        )

    def test_every_claim_has_source_and_lab_evidence(self) -> None:
        for pattern_id, pattern in self.bundle.manifests.items():
            with self.subTest(pattern=pattern_id):
                for field in ("observable_contract", "failure_modes"):
                    for claim in pattern[field]:
                        kinds = {
                            item.split(":", 1)[0]
                            for item in claim["evidence"]
                        }
                        self.assertEqual(kinds, {"source", "lab"})

    def test_all_sources_are_commit_pinned(self) -> None:
        lock_text = (
            REPOSITORY_ROOT / "references" / "upstream-lock.yaml"
        ).read_text(encoding="utf-8")
        locked_sources = dict(
            re.findall(
                r'url:\s*"(https://github\.com/[^"]+)"\s*\n'
                r'\s*commit:\s*"([0-9a-f]{40})"',
                lock_text,
            )
        )
        for pattern_id, pattern in self.bundle.manifests.items():
            with self.subTest(pattern=pattern_id):
                for source in pattern["source_evidence"]:
                    match = re.search(
                        r"^(https://github\.com/[^/]+/[^/]+)/blob/"
                        r"([0-9a-f]{40})/",
                        source["ref"],
                    )
                    self.assertIsNotNone(match)
                    self.assertEqual(
                        locked_sources.get(match.group(1)),
                        match.group(2),
                    )

    def test_all_lab_evidence_paths_exist(self) -> None:
        for pattern_id, pattern in self.bundle.manifests.items():
            with self.subTest(pattern=pattern_id):
                for evidence in pattern["lab_evidence"]:
                    self.assertTrue(
                        (REPOSITORY_ROOT / evidence["path"]).is_file()
                    )

    def test_markdown_cards_include_manifest_and_every_contract_id(self) -> None:
        for pattern_id, pattern in self.bundle.manifests.items():
            text = (REPOSITORY_ROOT / pattern["doc"]).read_text(
                encoding="utf-8"
            )
            documented_ids = {
                item["id"]
                for field in (
                    "observable_contract",
                    "failure_modes",
                    "rejected_decisions",
                )
                for item in pattern[field]
            }
            with self.subTest(pattern=pattern_id):
                self.assertIn(
                    f"manifests/{pattern_id}.json",
                    text,
                )
                self.assertTrue(
                    all(
                        f"`{item_id}`" in text
                        for item_id in documented_ids
                    )
                )

    def test_relations_and_decision_boundaries_cover_every_pattern(self) -> None:
        pattern_ids = set(self.bundle.manifests)
        relation_members = {
            value
            for relation in self.bundle.catalog["relations"]
            for value in (relation["source"], relation["target"])
        }
        boundary_members = {
            value
            for boundary in self.bundle.catalog["decision_boundaries"]
            for value in boundary["patterns"]
        }

        self.assertEqual(relation_members, pattern_ids)
        self.assertEqual(boundary_members, pattern_ids)

    def test_portability_is_separate_from_maturity(self) -> None:
        bounded = self.bundle.manifests["bounded-specialist"]

        self.assertEqual(bounded["status"], "validated")
        self.assertEqual(bounded["portability"], "version-specific")
        self.assertTrue(
            any(
                item["support"] == "validated"
                for item in bounded["adk_versions"]
            )
        )


class InvalidCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bundle = load_catalog_bundle(REPOSITORY_ROOT)
        cls.cases = load_invalid_cases(INVALID_CASES)

    def test_every_invalid_fixture_is_detected_by_expected_code(self) -> None:
        for case in self.cases:
            with self.subTest(case=case["id"]):
                report = validate_catalog(
                    apply_invalid_case(self.bundle, case)
                )
                codes = {issue.code for issue in report.issues}
                self.assertFalse(report.passed)
                self.assertIn(case["expected_code"], codes)

    def test_broken_gate_reports_all_invalid_cases(self) -> None:
        report = build_gate_report(
            "broken",
            root=REPOSITORY_ROOT,
        )

        self.assertFalse(report["passed"])
        self.assertTrue(report["all_invalid_cases_detected"])
        self.assertEqual(len(report["cases"]), 12)

    def test_baseline_and_broken_exit_codes_are_enforceable(self) -> None:
        baseline = build_gate_report(
            "baseline",
            root=REPOSITORY_ROOT,
        )
        broken = build_gate_report(
            "broken",
            root=REPOSITORY_ROOT,
        )

        self.assertEqual(exit_code(baseline), 0)
        self.assertEqual(exit_code(broken), 1)

    def test_cli_process_exit_matches_catalog_validity(self) -> None:
        script = LAB_ROOT / "scripts" / "run_pattern_gate.py"
        baseline = subprocess.run(
            [sys.executable, str(script), "--variant", "baseline"],
            check=False,
            capture_output=True,
            text=True,
        )
        broken = subprocess.run(
            [sys.executable, str(script), "--variant", "broken"],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(baseline.returncode, 0)
        self.assertEqual(broken.returncode, 1)
        self.assertTrue(json.loads(baseline.stdout)["passed"])
        self.assertFalse(json.loads(broken.stdout)["passed"])

    def test_trace_bundle_is_byte_deterministic(self) -> None:
        first = json.dumps(
            {
                "baseline": build_gate_report(
                    "baseline",
                    root=REPOSITORY_ROOT,
                ),
                "broken": build_gate_report(
                    "broken",
                    root=REPOSITORY_ROOT,
                ),
            },
            indent=2,
            sort_keys=True,
        )
        second = json.dumps(
            {
                "baseline": build_gate_report(
                    "baseline",
                    root=REPOSITORY_ROOT,
                ),
                "broken": build_gate_report(
                    "broken",
                    root=REPOSITORY_ROOT,
                ),
            },
            indent=2,
            sort_keys=True,
        )

        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
