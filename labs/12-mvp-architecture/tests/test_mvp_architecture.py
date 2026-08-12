"""Dependency-free tests for the Mini Agent Garden component model."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

from architecture_lab.fixtures import apply_invalid_case
from architecture_lab.fixtures import load_invalid_cases
from architecture_lab.gate import build_gate_report
from architecture_lab.gate import exit_code
from architecture_lab.loader import find_repository_root
from architecture_lab.loader import load_architecture_bundle
from architecture_lab.validation import EXPECTED_COMPONENTS
from architecture_lab.validation import EXPECTED_CREDENTIAL_SCOPES
from architecture_lab.validation import EXPECTED_RELEASE_STAGES
from architecture_lab.validation import EXPECTED_ROLLBACK_STAGES
from architecture_lab.validation import validate_architecture_bundle
from architecture_lab.walkthrough import build_walkthroughs


LAB_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = find_repository_root(LAB_ROOT)
INVALID_CASES = LAB_ROOT / "fixtures" / "invalid_cases.json"


class ArchitectureContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bundle = load_architecture_bundle(REPOSITORY_ROOT)
        cls.report = validate_architecture_bundle(cls.bundle)
        cls.architecture = cls.bundle.architecture

    def test_baseline_architecture_passes_without_issues(self) -> None:
        self.assertTrue(self.report.passed)
        self.assertEqual(self.report.issues, ())

    def test_summary_fixes_phase_twelve_exit_counts(self) -> None:
        self.assertEqual(
            self.report.summary,
            {
                "component_count": 6,
                "artifact_count": 12,
                "storage_class_count": 6,
                "trust_boundary_count": 9,
                "extension_point_count": 7,
                "release_stage_count": 7,
                "rollback_stage_count": 2,
                "walkthrough_count": 3,
                "adr_count": 6,
            },
        )

    def test_component_set_and_credentials_are_minimal(self) -> None:
        components = {
            item["id"]: item for item in self.architecture["components"]
        }
        self.assertEqual(set(components), EXPECTED_COMPONENTS)
        self.assertEqual(
            {
                component_id: item["credential_scope"]
                for component_id, item in components.items()
            },
            EXPECTED_CREDENTIAL_SCOPES,
        )
        self.assertNotIn("cli", components)
        self.assertNotIn("event-bus", components)
        self.assertNotIn("database", components)

    def test_every_internal_artifact_has_one_component_owner(self) -> None:
        components = {
            item["id"]: item for item in self.architecture["components"]
        }
        for artifact in self.architecture["artifacts"]:
            owner = artifact["owner"]
            if owner.startswith("external:"):
                continue
            self.assertIn(owner, components)
            self.assertIn(artifact["id"], components[owner]["owns"])

    def test_storage_classes_separate_authority_and_mutability(self) -> None:
        artifacts = {
            item["id"]: item for item in self.architecture["artifacts"]
        }
        self.assertEqual(
            artifacts["release-record"]["mutability"],
            "append-only",
        )
        self.assertEqual(
            artifacts["deployment-status"]["authority"],
            "cache",
        )
        self.assertEqual(
            artifacts["project-instance"]["mutability"],
            "regenerable",
        )
        self.assertTrue(
            all(
                not item["secret_material_allowed"]
                for item in artifacts.values()
            )
        )

    def test_deployment_and_release_history_are_separate(self) -> None:
        components = {
            item["id"]: item for item in self.architecture["components"]
        }
        deployment = components["deployment-controller"]
        ledger = components["release-ledger"]
        self.assertEqual(deployment["credential_scope"], "target-scoped")
        self.assertEqual(ledger["credential_scope"], "ledger-write")
        self.assertNotIn("release-record", deployment["owns"])
        self.assertNotIn("deployment-status", ledger["owns"])

    def test_trust_boundaries_cover_candidate_promotion_and_rollback(
        self,
    ) -> None:
        boundaries = {
            item["id"]: item
            for item in self.architecture["trust_boundaries"]
        }
        self.assertIn("candidate-to-evaluation", boundaries)
        self.assertIn("evaluation-to-promotion", boundaries)
        self.assertIn("deployment-to-ledger", boundaries)
        self.assertIn("ledger-to-rollback", boundaries)
        self.assertIn(
            "behavior-report",
            boundaries["evaluation-to-promotion"]["artifacts"],
        )

    def test_extensions_keep_architecture_in_typed_core(self) -> None:
        extensions = {
            item["id"]: item
            for item in self.architecture["extension_points"]
        }
        self.assertEqual(
            extensions["architecture-kind"]["kind"],
            "typed-union",
        )
        self.assertTrue(
            extensions["architecture-kind"]["core_change_required"]
        )
        adapters = [
            item
            for item in extensions.values()
            if item["id"] != "architecture-kind"
        ]
        self.assertTrue(
            all(item["kind"] == "external-adapter" for item in adapters)
        )
        self.assertTrue(
            all(not item["core_change_required"] for item in adapters)
        )

    def test_release_and_rollback_paths_have_explicit_order(self) -> None:
        lifecycle = self.architecture["lifecycle"]
        self.assertEqual(
            [item["id"] for item in lifecycle["release_path"]],
            EXPECTED_RELEASE_STAGES,
        )
        self.assertEqual(
            [item["id"] for item in lifecycle["rollback_path"]],
            EXPECTED_ROLLBACK_STAGES,
        )
        promote = lifecycle["release_path"][5]
        self.assertIn("behavior-report", promote["consumes"])
        record = lifecycle["release_path"][6]
        self.assertEqual(record["component"], "release-ledger")

    def test_walkthroughs_match_blueprint_architecture_and_metrics(
        self,
    ) -> None:
        walkthroughs = {
            item["blueprint_id"]: item
            for item in self.architecture["blueprint_walkthroughs"]
        }
        self.assertEqual(set(walkthroughs), set(self.bundle.blueprints))
        for blueprint_id, blueprint in self.bundle.blueprints.items():
            walkthrough = walkthroughs[blueprint_id]
            self.assertEqual(
                walkthrough["architecture"],
                blueprint["architecture"]["kind"],
            )
            self.assertEqual(
                walkthrough["required_metrics"],
                blueprint["evaluation"]["blocking_metrics"],
            )
            self.assertTrue(walkthrough["rollback_supported"])

    def test_digest_chained_walkthroughs_use_all_release_stages(self) -> None:
        evidence = build_walkthroughs(self.bundle)
        self.assertEqual(len(evidence), 3)
        for item in evidence:
            self.assertEqual(
                [stage["stage"] for stage in item["stage_receipts"]],
                EXPECTED_RELEASE_STAGES,
            )
            self.assertRegex(item["candidate_digest"], r"^[0-9a-f]{64}$")
            self.assertRegex(
                item["behavior_report_digest"],
                r"^[0-9a-f]{64}$",
            )
            self.assertRegex(
                item["release_record_digest"],
                r"^[0-9a-f]{64}$",
            )
            self.assertFalse(item["secret_material_present"])

    def test_all_six_adrs_have_required_sections(self) -> None:
        self.assertEqual(len(self.architecture["adrs"]), 6)
        for adr in self.architecture["adrs"]:
            text = (REPOSITORY_ROOT / adr["path"]).read_text(
                encoding="utf-8"
            )
            for section in (
                "Status: Accepted",
                "## Context",
                "## Decision",
                "## Consequences",
                "## Evidence",
            ):
                self.assertIn(section, text)

    def test_published_schema_fields_match_stdlib_validator(self) -> None:
        schema = self.bundle.schema
        self.assertEqual(
            set(schema["required"]),
            set(schema["properties"]),
        )
        for name in (
            "component",
            "artifact",
            "storage_class",
            "trust_boundary",
            "extension_point",
            "lifecycle",
            "stage",
            "walkthrough",
            "adr",
        ):
            definition = schema["$defs"][name]
            self.assertEqual(
                set(definition["required"]),
                set(definition["properties"]),
            )
            self.assertFalse(definition["additionalProperties"])


class InvalidArchitectureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bundle = load_architecture_bundle(REPOSITORY_ROOT)
        cls.cases = load_invalid_cases(INVALID_CASES)

    def test_all_fifteen_invalid_boundaries_are_detected(self) -> None:
        self.assertEqual(len(self.cases), 15)
        for case in self.cases:
            with self.subTest(case=case["id"]):
                report = validate_architecture_bundle(
                    apply_invalid_case(self.bundle, case)
                )
                codes = {issue.code for issue in report.issues}
                self.assertFalse(report.passed)
                self.assertIn(case["expected_code"], codes)

    def test_broken_gate_reports_all_fifteen_cases(self) -> None:
        report = build_gate_report("broken", root=REPOSITORY_ROOT)
        self.assertFalse(report["passed"])
        self.assertTrue(report["all_invalid_cases_detected"])
        self.assertEqual(len(report["cases"]), 15)

    def test_baseline_and_broken_exit_codes_are_enforceable(self) -> None:
        baseline = build_gate_report("baseline", root=REPOSITORY_ROOT)
        broken = build_gate_report("broken", root=REPOSITORY_ROOT)
        self.assertEqual(exit_code(baseline), 0)
        self.assertEqual(exit_code(broken), 1)

    def test_cli_process_exit_status_matches_gate(self) -> None:
        script = LAB_ROOT / "scripts" / "run_architecture_gate.py"
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
        script = LAB_ROOT / "scripts" / "run_architecture_traces.py"
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
        self.assertTrue(parsed["broken"]["all_invalid_cases_detected"])
        self.assertEqual(
            hashlib.sha256(first).hexdigest(),
            hashlib.sha256(second).hexdigest(),
        )


if __name__ == "__main__":
    unittest.main()
