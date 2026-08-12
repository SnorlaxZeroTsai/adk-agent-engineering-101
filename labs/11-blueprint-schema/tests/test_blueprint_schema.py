"""Dependency-free tests for executable Blueprint contracts."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

from blueprint_lab.fixtures import apply_invalid_case
from blueprint_lab.fixtures import load_invalid_cases
from blueprint_lab.gate import build_gate_report
from blueprint_lab.gate import exit_code
from blueprint_lab.loader import find_repository_root
from blueprint_lab.loader import load_blueprint_bundle
from blueprint_lab.migration import migrate_v0_1_to_v1
from blueprint_lab.references import collect_local_refs
from blueprint_lab.schema_validation import validate_schema_instance
from blueprint_lab.validation import validate_blueprint_bundle


LAB_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = find_repository_root(LAB_ROOT)
INVALID_CASES = LAB_ROOT / "fixtures" / "invalid_cases.json"
LEGACY_FIXTURE = LAB_ROOT / "fixtures" / "order-support-v0.1.json"


class BlueprintContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bundle = load_blueprint_bundle(REPOSITORY_ROOT)
        cls.report = validate_blueprint_bundle(cls.bundle)

    def test_baseline_blueprints_pass_without_issues(self) -> None:
        self.assertTrue(self.report.passed)
        self.assertEqual(self.report.issues, ())

    def test_summary_fixes_phase_eleven_exit_counts(self) -> None:
        self.assertEqual(
            self.report.summary,
            {
                "blueprint_count": 3,
                "architecture_counts": {
                    "multi-agent": 1,
                    "single-agent": 1,
                    "workflow": 1,
                },
                "catalog_entry_count": 3,
                "implementation_count": 3,
                "local_ref_count": 38,
                "unique_local_ref_count": 26,
                "model_slot_count": 3,
                "state_contract_count": 3,
                "retrieval_contract_count": 1,
                "approval_action_count": 1,
                "blocking_metric_count": 16,
            },
        )

    def test_three_materially_different_architectures_are_present(self) -> None:
        kinds = {
            item["architecture"]["kind"]
            for item in self.bundle.blueprints.values()
        }
        self.assertEqual(
            kinds,
            {"single-agent", "workflow", "multi-agent"},
        )

    def test_top_level_schema_contains_only_common_domains(self) -> None:
        expected = {
            "schema_version",
            "id",
            "catalog_ref",
            "architecture",
            "runtime",
            "policy",
            "evaluation",
            "lifecycle",
            "extensions",
        }
        self.assertEqual(set(self.bundle.schema["required"]), expected)
        self.assertEqual(set(self.bundle.schema["properties"]), expected)
        self.assertFalse(self.bundle.schema["additionalProperties"])

    def test_architecture_is_a_strict_three_branch_union(self) -> None:
        union = self.bundle.schema["properties"]["architecture"]["oneOf"]
        self.assertEqual(
            [item["$ref"] for item in union],
            [
                "#/$defs/single_agent_architecture",
                "#/$defs/workflow_architecture",
                "#/$defs/multi_agent_architecture",
            ],
        )
        for name in (
            "single_agent_architecture",
            "workflow_architecture",
            "multi_agent_architecture",
        ):
            definition = self.bundle.schema["$defs"][name]
            self.assertFalse(definition["additionalProperties"])

    def test_object_definitions_keep_required_and_property_fields_aligned(
        self,
    ) -> None:
        for name, definition in self.bundle.schema["$defs"].items():
            if definition.get("type") != "object":
                continue
            with self.subTest(definition=name):
                self.assertEqual(
                    set(definition["required"]),
                    set(definition["properties"]),
                )
                self.assertFalse(definition["additionalProperties"])

    def test_catalog_snapshot_resolves_three_immutable_implementations(
        self,
    ) -> None:
        entries = self.bundle.catalog["entries"]
        self.assertEqual(len(entries), 3)
        for entry in entries:
            implementation = entry["implementations"][0]
            source = implementation["source"]
            self.assertEqual(
                source["revision"],
                "9702a79d15f81a9a44a8d40af3ca038196746c46",
            )
            spec = f"{source['revision']}:{source['path']}"
            result = subprocess.run(
                ["git", "cat-file", "-e", spec],
                cwd=REPOSITORY_ROOT,
                check=False,
            )
            self.assertEqual(result.returncode, 0)
        for path in (
            ["entries", 0, "lifecycle", "status"],
            ["entries", 0, "implementations", 0, "status"],
        ):
            case = {
                "scope": "catalog",
                "operation": "set",
                "path": path,
                "value": "deprecated",
            }
            report = validate_blueprint_bundle(
                apply_invalid_case(self.bundle, case)
            )
            self.assertTrue(
                {
                    "catalog_entry_not_active",
                    "implementation_not_active",
                }
                & {issue.code for issue in report.issues}
            )

    def test_all_local_refs_resolve_to_top_level_python_symbols(self) -> None:
        self.assertEqual(
            sum(
                len(collect_local_refs(item))
                for item in self.bundle.blueprints.values()
            ),
            38,
        )
        local_ref_issues = {
            "local_ref_invalid",
            "local_ref_outside_repository",
            "local_ref_file_missing",
            "local_ref_python_invalid",
            "local_ref_symbol_missing",
        }
        self.assertTrue(
            local_ref_issues.isdisjoint(
                {item.code for item in self.report.issues}
            )
        )

    def test_blueprint_does_not_duplicate_catalog_authority(self) -> None:
        forbidden = {
            "display_name",
            "summary",
            "ownership",
            "classification",
            "implementations",
            "assurance",
        }
        for blueprint in self.bundle.blueprints.values():
            self.assertTrue(forbidden.isdisjoint(blueprint))
            self.assertEqual(
                set(blueprint["catalog_ref"]),
                {"entry_id", "implementation_id"},
            )

    def test_workflow_composes_explicit_rag_contract(self) -> None:
        blueprint = self.bundle.blueprints["research-workflow-rag"]
        retrieval = blueprint["runtime"]["retrieval_contracts"][0]
        self.assertEqual(
            set(retrieval["provenance_fields"]),
            {"document_id", "version", "chunk_id", "uri", "acl"},
        )
        self.assertEqual(
            retrieval["authorization_stage"],
            "before-ranking",
        )
        self.assertIn(
            "retrieval_grounding",
            blueprint["evaluation"]["blocking_metrics"],
        )

    def test_multi_agent_composes_durable_approval_contract(self) -> None:
        blueprint = self.bundle.blueprints["case-triage-with-approval"]
        task_agent = blueprint["architecture"]["agents"][1]
        self.assertEqual(task_agent["mode"], "task")
        self.assertIsNotNone(task_agent["input_schema_ref"])
        self.assertIsNotNone(task_agent["output_schema_ref"])
        approval = blueprint["policy"]["approval"]
        self.assertEqual(approval["actions"], ["vendor_payment"])
        self.assertEqual(approval["replay_key"], "action_id")
        self.assertIn(
            "policy_safety",
            blueprint["evaluation"]["blocking_metrics"],
        )

    def test_v0_1_migration_matches_canonical_v1_example(self) -> None:
        legacy = json.loads(LEGACY_FIXTURE.read_text(encoding="utf-8"))
        result = migrate_v0_1_to_v1(legacy)
        self.assertTrue(result.catalog_ref_preserved)
        self.assertEqual(result.source_id, result.target_id)
        self.assertEqual(
            result.blueprint,
            self.bundle.blueprints["order-support-read-only"],
        )

    def test_migration_rejects_unsupported_version_and_architecture(
        self,
    ) -> None:
        legacy = json.loads(LEGACY_FIXTURE.read_text(encoding="utf-8"))
        wrong_version = deepcopy(legacy)
        wrong_version["schema_version"] = "0.0"
        with self.assertRaises(ValueError):
            migrate_v0_1_to_v1(wrong_version)
        wrong_architecture = deepcopy(legacy)
        wrong_architecture["architecture_kind"] = "workflow"
        with self.assertRaises(ValueError):
            migrate_v0_1_to_v1(wrong_architecture)


class InvalidBlueprintTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bundle = load_blueprint_bundle(REPOSITORY_ROOT)
        cls.cases = load_invalid_cases(INVALID_CASES)

    def test_all_fifteen_invalid_cases_are_detected_by_expected_code(
        self,
    ) -> None:
        self.assertEqual(len(self.cases), 15)
        for case in self.cases:
            with self.subTest(case=case["id"]):
                report = validate_blueprint_bundle(
                    apply_invalid_case(self.bundle, case)
                )
                codes = {issue.code for issue in report.issues}
                self.assertFalse(report.passed)
                self.assertIn(case["expected_code"], codes)

    def test_schema_subset_rejects_duplicated_catalog_authority(self) -> None:
        blueprint = deepcopy(
            self.bundle.blueprints["order-support-read-only"]
        )
        blueprint["display_name"] = "Wrong authority"
        issues = validate_schema_instance(
            blueprint,
            self.bundle.schema,
            path="blueprint",
        )
        self.assertIn(
            "schema_additional_property",
            {item.code for item in issues},
        )

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
        script = LAB_ROOT / "scripts" / "run_blueprint_gate.py"
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
        script = LAB_ROOT / "scripts" / "run_blueprint_traces.py"
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
