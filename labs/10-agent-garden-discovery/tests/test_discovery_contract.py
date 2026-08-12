"""Dependency-free tests for Agent Garden discoverability metadata."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import unittest

from garden_discovery.fixtures import apply_invalid_case
from garden_discovery.fixtures import load_invalid_cases
from garden_discovery.gate import build_gate_report
from garden_discovery.gate import exit_code
from garden_discovery.loader import find_repository_root
from garden_discovery.loader import load_discovery_bundle
from garden_discovery.projection import assess_source_surfaces
from garden_discovery.projection import catalog_fact_coverage
from garden_discovery.validation import ASSURANCE_FIELDS
from garden_discovery.validation import CATALOG_FIELDS
from garden_discovery.validation import CLASSIFICATION_FIELDS
from garden_discovery.validation import ENTRY_FIELDS
from garden_discovery.validation import FRAMEWORK_FIELDS
from garden_discovery.validation import IMPLEMENTATION_FIELDS
from garden_discovery.validation import LIFECYCLE_FIELDS
from garden_discovery.validation import OWNERSHIP_FIELDS
from garden_discovery.validation import REUSE_FIELDS
from garden_discovery.validation import SOURCE_FIELDS
from garden_discovery.validation import validate_discovery_bundle


LAB_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = find_repository_root(LAB_ROOT)
INVALID_CASES = LAB_ROOT / "fixtures" / "misleading_cases.json"


class DiscoveryContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bundle = load_discovery_bundle(REPOSITORY_ROOT)
        cls.report = validate_discovery_bundle(cls.bundle)

    def test_baseline_catalog_passes_without_issues(self) -> None:
        self.assertTrue(self.report.passed)
        self.assertEqual(self.report.issues, ())

    def test_summary_fixes_phase_ten_exit_counts(self) -> None:
        self.assertEqual(
            self.report.summary,
            {
                "source_contract_count": 3,
                "consumer_observation_count": 4,
                "source_field_count": 33,
                "plane_field_counts": {
                    "catalog": 16,
                    "governance": 7,
                    "runtime": 6,
                    "scaffold": 19,
                },
                "required_discovery_fact_count": 9,
                "catalog_entry_count": 1,
                "implementation_count": 1,
                "assurance_count": 1,
            },
        )

    def test_published_schema_matches_stdlib_validator_fields(self) -> None:
        schema = self.bundle.schema
        definitions = schema["$defs"]
        self.assertEqual(set(schema["required"]), CATALOG_FIELDS)
        self.assertEqual(set(schema["properties"]), CATALOG_FIELDS)
        expected = {
            "entry": ENTRY_FIELDS,
            "lifecycle": LIFECYCLE_FIELDS,
            "ownership": OWNERSHIP_FIELDS,
            "classification": CLASSIFICATION_FIELDS,
            "implementation": IMPLEMENTATION_FIELDS,
            "framework": FRAMEWORK_FIELDS,
            "source": SOURCE_FIELDS,
            "reuse": REUSE_FIELDS,
            "assurance": ASSURANCE_FIELDS,
        }
        for definition, fields in expected.items():
            with self.subTest(definition=definition):
                self.assertEqual(
                    set(definitions[definition]["required"]),
                    fields,
                )
                self.assertEqual(
                    set(definitions[definition]["properties"]),
                    fields,
                )

    def test_all_source_contracts_are_exactly_commit_pinned(self) -> None:
        lock_text = (
            REPOSITORY_ROOT / "references" / "upstream-lock.yaml"
        ).read_text(encoding="utf-8")
        locked = dict(
            re.findall(
                r'url:\s*"(https://github\.com/[^"]+)"\s*\n'
                r'\s*commit:\s*"([0-9a-f]{40})"',
                lock_text,
            )
        )
        sources = [
            item["source"]
            for item in self.bundle.metadata["source_contracts"]
        ]
        sources.extend(
            item["source"]
            for item in self.bundle.metadata["consumer_observations"]
        )
        for source in sources:
            match = re.fullmatch(
                r"(https://github\.com/[^/]+/[^/]+)/blob/"
                r"([0-9a-f]{40})/.+",
                source,
            )
            self.assertIsNotNone(match)
            self.assertEqual(locked.get(match.group(1)), match.group(2))

    def test_every_source_field_has_an_owner_plane(self) -> None:
        plane_ids = {
            plane["id"] for plane in self.bundle.metadata["planes"]
        }
        observed = set()
        for contract in self.bundle.metadata["source_contracts"]:
            for field in contract["fields"]:
                self.assertTrue(field["planes"])
                self.assertLessEqual(set(field["planes"]), plane_ids)
                observed.update(field["planes"])
        self.assertEqual(observed, plane_ids)

    def test_no_upstream_surface_is_a_complete_catalog_contract(self) -> None:
        assessments = assess_source_surfaces(self.bundle.metadata)
        self.assertEqual(len(assessments), 3)
        self.assertTrue(all(not item["complete"] for item in assessments))
        self.assertTrue(
            all("stable_identity" in item["missing"] for item in assessments)
        )

    def test_registry_entry_covers_all_nine_discovery_facts(self) -> None:
        entry = self.bundle.catalog["entries"][0]
        coverage = catalog_fact_coverage(entry)
        self.assertTrue(coverage["complete"])
        self.assertEqual(
            set(coverage["provided"]),
            set(self.bundle.metadata["required_discovery_facts"]),
        )

    def test_catalog_contract_excludes_executable_blueprint_fields(self) -> None:
        forbidden = {
            "models",
            "tools",
            "workflow",
            "deployment_targets",
            "runtime_config",
            "policy",
            "evaluation",
            "secrets",
        }
        entry = self.bundle.catalog["entries"][0]
        self.assertTrue(forbidden.isdisjoint(entry))
        self.assertTrue(forbidden.isdisjoint(ENTRY_FIELDS))

    def test_project_instance_name_is_not_catalog_identity(self) -> None:
        project = next(
            item
            for item in self.bundle.metadata["source_contracts"]
            if item["id"] == "agents-cli-project-manifest"
        )
        self.assertNotIn("stable_identity", project["provides"])
        name_field = next(
            item for item in project["fields"] if item["field"] == "name"
        )
        self.assertEqual(name_field["planes"], ["scaffold"])

    def test_catalog_source_and_template_ref_are_the_same_revision(self) -> None:
        implementation = self.bundle.catalog["entries"][0][
            "implementations"
        ][0]
        source = implementation["source"]
        template_ref = implementation["reuse"]["template_ref"]
        self.assertIn(source["repository"], template_ref)
        self.assertIn(source["revision"], template_ref)
        self.assertTrue(template_ref.endswith(source["path"]))

    def test_assurance_is_bound_to_one_implementation(self) -> None:
        entry = self.bundle.catalog["entries"][0]
        implementation_ids = {
            item["id"] for item in entry["implementations"]
        }
        assured_ids = {
            item["implementation_id"] for item in entry["assurance"]
        }
        self.assertEqual(assured_ids, implementation_ids)
        self.assertRegex(
            entry["assurance"][0]["digest"],
            r"^sha256:[0-9a-f]{64}$",
        )


class MisleadingCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bundle = load_discovery_bundle(REPOSITORY_ROOT)
        cls.cases = load_invalid_cases(INVALID_CASES)

    def test_all_misleading_cases_are_detected_by_expected_code(self) -> None:
        for case in self.cases:
            with self.subTest(case=case["id"]):
                report = validate_discovery_bundle(
                    apply_invalid_case(self.bundle, case)
                )
                codes = {issue.code for issue in report.issues}
                self.assertFalse(report.passed)
                self.assertIn(case["expected_code"], codes)

    def test_broken_gate_reports_all_thirteen_cases(self) -> None:
        report = build_gate_report("broken", root=REPOSITORY_ROOT)
        self.assertFalse(report["passed"])
        self.assertTrue(report["all_misleading_cases_detected"])
        self.assertEqual(len(report["cases"]), 13)

    def test_baseline_and_broken_exit_codes_are_enforceable(self) -> None:
        baseline = build_gate_report("baseline", root=REPOSITORY_ROOT)
        broken = build_gate_report("broken", root=REPOSITORY_ROOT)
        self.assertEqual(exit_code(baseline), 0)
        self.assertEqual(exit_code(broken), 1)

    def test_cli_process_exit_status_matches_gate(self) -> None:
        script = LAB_ROOT / "scripts" / "run_discovery_gate.py"
        baseline = subprocess.run(
            [sys.executable, str(script), "--variant", "baseline"],
            cwd=LAB_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        broken = subprocess.run(
            [sys.executable, str(script), "--variant", "broken"],
            cwd=LAB_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(baseline.returncode, 0)
        self.assertEqual(broken.returncode, 1)

    def test_evidence_renderer_is_byte_deterministic(self) -> None:
        script = LAB_ROOT / "scripts" / "run_discovery_traces.py"
        first = subprocess.check_output(
            [sys.executable, str(script)],
            cwd=LAB_ROOT,
        )
        second = subprocess.check_output(
            [sys.executable, str(script)],
            cwd=LAB_ROOT,
        )
        self.assertEqual(first, second)
        parsed = json.loads(first)
        self.assertTrue(parsed["baseline"]["passed"])
        self.assertTrue(
            parsed["broken"]["all_misleading_cases_detected"]
        )
        self.assertEqual(
            hashlib.sha256(first).hexdigest(),
            hashlib.sha256(second).hexdigest(),
        )


if __name__ == "__main__":
    unittest.main()
