"""Dependency-free end-to-end tests for the Mini Agent Garden."""

from __future__ import annotations

from contextlib import redirect_stderr
from contextlib import redirect_stdout
from copy import deepcopy
from dataclasses import replace
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


LAB_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = LAB_ROOT.parents[1]
PACKAGE_ROOT = REPOSITORY_ROOT / "mini-agent-garden"
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))
if str(LAB_ROOT) not in sys.path:
    sys.path.insert(0, str(LAB_ROOT))

from garden_lab.gate import BLUEPRINT_IDS
from garden_lab.gate import EXPECTED_TEST_COUNTS
from garden_lab.gate import ExperimentalHandler
from garden_lab.gate import ExperimentalValidator
from garden_lab.gate import FIXTURE_ROOT
from garden_lab.gate import build_gate_report
from garden_lab.gate import exit_code
from mini_agent_garden.architecture import ArchitectureRegistry
from mini_agent_garden.canonical import digest_json
from mini_agent_garden.cli import main as cli_main
from mini_agent_garden.contracts import Candidate
from mini_agent_garden.errors import GardenError
from mini_agent_garden.errors import ProjectIntegrityError
from mini_agent_garden.errors import UpgradeReviewRequired
from mini_agent_garden.service import MiniAgentGarden


class MiniGardenContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.garden = MiniAgentGarden(REPOSITORY_ROOT)

    def test_catalog_lists_exactly_three_blueprints(self) -> None:
        report = self.garden.list()
        self.assertEqual(report["count"], 3)
        self.assertEqual(
            {item["blueprint_id"] for item in report["entries"]},
            set(BLUEPRINT_IDS),
        )

    def test_catalog_filters_by_architecture_and_tag(self) -> None:
        workflows = self.garden.list(architecture="workflow")
        self.assertEqual(
            [item["blueprint_id"] for item in workflows["entries"]],
            ["research-workflow-rag"],
        )
        approvals = self.garden.list(tag="approval")
        self.assertEqual(
            [item["blueprint_id"] for item in approvals["entries"]],
            ["case-triage-with-approval"],
        )

    def test_inspect_resolves_full_commit_selection(self) -> None:
        report = self.garden.inspect("order-support-read-only")
        selection = report["selection"]
        self.assertRegex(selection["revision"], r"^[0-9a-f]{40}$")
        self.assertEqual(
            selection["source_path"],
            "labs/01-agent-basics",
        )
        self.assertEqual(
            report["entry"]["id"],
            report["blueprint"]["catalog_ref"]["entry_id"],
        )

    def test_all_three_blueprints_pass_existing_validator(self) -> None:
        for blueprint_id in BLUEPRINT_IDS:
            with self.subTest(blueprint_id=blueprint_id):
                report = self.garden.validate(blueprint_id)
                self.assertTrue(report["passed"])
                self.assertEqual(report["issues"], ())

    def test_project_render_is_byte_deterministic_across_paths(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = self.garden.create(
                "order-support-read-only",
                root / "first",
            )
            second = self.garden.create(
                "order-support-read-only",
                root / "second",
            )
            self.assertEqual(first["manifest"], second["manifest"])
            self.assertEqual(
                (root / "first" / "garden-project.json").read_bytes(),
                (root / "second" / "garden-project.json").read_bytes(),
            )

    def test_project_source_matches_pinned_git_blob(self) -> None:
        with TemporaryDirectory() as temporary:
            project = Path(temporary) / "project"
            self.garden.create("order-support-read-only", project)
            rendered = (
                project
                / "implementation"
                / "agent_basics"
                / "tools.py"
            ).read_bytes()
            expected = subprocess.run(
                [
                    "git",
                    "-C",
                    str(REPOSITORY_ROOT),
                    "show",
                    (
                        "9702a79d15f81a9a44a8d40af3ca038196746c46:"
                        "labs/01-agent-basics/agent_basics/tools.py"
                    ),
                ],
                capture_output=True,
                check=True,
            ).stdout
            self.assertEqual(rendered, expected)

    def test_all_three_projects_scaffold_and_pass_contract_tests(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            for blueprint_id in BLUEPRINT_IDS:
                with self.subTest(blueprint_id=blueprint_id):
                    project = root / blueprint_id
                    created = self.garden.create(blueprint_id, project)
                    report = self.garden.test(project)
                    self.assertTrue(report["passed"])
                    self.assertEqual(
                        report["test_count"],
                        EXPECTED_TEST_COUNTS[blueprint_id],
                    )
                    self.assertEqual(
                        report["blueprint_digest"],
                        created["manifest"]["blueprint_digest"],
                    )

    def test_behavior_report_is_content_addressed_to_candidate(self) -> None:
        with TemporaryDirectory() as temporary:
            project = Path(temporary) / "project"
            self.garden.create("order-support-read-only", project)
            report = self.garden.test(project)
            stored = (
                project
                / ".garden"
                / "behavior-reports"
                / "sha256"
                / f"{report['report_digest']}.json"
            )
            self.assertTrue(stored.is_file())
            core = json.loads(stored.read_text(encoding="utf-8"))
            self.assertEqual(digest_json(core), report["report_digest"])
            self.assertRegex(
                report["candidate_digest"],
                r"^[0-9a-f]{64}$",
            )

    def test_candidate_tamper_fails_before_behavior_execution(self) -> None:
        with TemporaryDirectory() as temporary:
            project = Path(temporary) / "project"
            self.garden.create("order-support-read-only", project)
            path = (
                project
                / "implementation"
                / "agent_basics"
                / "tools.py"
            )
            path.write_text(
                path.read_text(encoding="utf-8") + "\nTAMPERED = True\n",
                encoding="utf-8",
            )
            with self.assertRaises(ProjectIntegrityError):
                self.garden.test(project)

    def test_forged_candidate_digest_fails_before_test_execution(self) -> None:
        with TemporaryDirectory() as temporary:
            project = Path(temporary) / "project"
            self.garden.create("order-support-read-only", project)
            candidate = self.garden.deployment.stage(project)
            forged = Candidate(
                project_root=candidate.project_root,
                candidate_digest="0" * 64,
                payload=candidate.payload,
            )
            with self.assertRaises(ProjectIntegrityError):
                self.garden.behavior.evaluate(forged)

    def test_legacy_upgrade_is_identity_preserving_schema_migration(
        self,
    ) -> None:
        with TemporaryDirectory() as temporary:
            project = Path(temporary) / "project"
            self.garden.create("order-support-read-only", project)
            result = self.garden.upgrade(
                project,
                (
                    REPOSITORY_ROOT
                    / "labs"
                    / "11-blueprint-schema"
                    / "fixtures"
                    / "order-support-v0.1.json"
                ),
            )
            plan = result["plan"]
            self.assertEqual(
                plan["categories"],
                ["blueprint-schema-migration"],
            )
            self.assertFalse(plan["requires_review"])
            self.assertEqual(
                plan["from"]["blueprint_digest"],
                plan["to"]["blueprint_digest"],
            )

    def test_compatible_upgrade_preserves_user_owned_file(self) -> None:
        with TemporaryDirectory() as temporary:
            project = Path(temporary) / "project"
            self.garden.create("order-support-read-only", project)
            user_file = project / "user" / "notes.txt"
            user_file.parent.mkdir()
            user_file.write_text("keep me\n", encoding="utf-8")
            updated = deepcopy(
                self.garden.catalog.blueprints[
                    "order-support-read-only"
                ]
            )
            updated["extensions"]["com.phase13"] = {"revision": "1.1"}
            planned = self.garden.upgrade(project, updated)
            self.assertEqual(
                planned["plan"]["categories"],
                ["blueprint-composition-change"],
            )
            self.assertFalse(planned["plan"]["requires_review"])
            applied = self.garden.upgrade(
                project,
                updated,
                apply=True,
            )
            self.assertTrue(applied["applied"])
            self.assertEqual(
                user_file.read_text(encoding="utf-8"),
                "keep me\n",
            )

    def test_implementation_change_requires_explicit_review(self) -> None:
        with TemporaryDirectory() as temporary:
            project = Path(temporary) / "project"
            self.garden.create("order-support-read-only", project)
            blueprint = self.garden.catalog.blueprints[
                "order-support-read-only"
            ]
            selection = replace(
                self.garden.catalog.resolve(blueprint),
                implementation_id="python-adk-2x-next",
            )
            validation = self.garden.validator.require_valid(blueprint)
            target = self.garden.renderer.build_plan(
                blueprint,
                selection,
                validation,
            )
            plan = self.garden.upgrades.plan(project, target)
            self.assertTrue(plan.requires_review)
            with self.assertRaises(UpgradeReviewRequired):
                self.garden.upgrades.apply(plan)

    def test_release_ledger_is_append_only_and_secret_free(self) -> None:
        with TemporaryDirectory() as temporary:
            ledger = self.garden.release_ledger(
                Path(temporary) / "releases.jsonl"
            )
            record = {
                "release_id": "release-1",
                "status": "validated-local",
            }
            ledger.append(record)
            self.assertEqual(ledger.records(), (record,))
            with self.assertRaises(GardenError):
                ledger.append(record)
            with self.assertRaises(GardenError):
                ledger.append(
                    {
                        "release_id": "release-2",
                        "api_token": "not-allowed",
                    }
                )

    def test_typed_handler_extension_does_not_change_cli_dispatch(
        self,
    ) -> None:
        architectures = ArchitectureRegistry()
        architectures.register(ExperimentalHandler())
        garden = MiniAgentGarden(
            REPOSITORY_ROOT,
            architectures=architectures,
            contract_validator=ExperimentalValidator(),
        )
        with TemporaryDirectory() as temporary:
            project = Path(temporary) / "experimental"
            stdout = io.StringIO()
            stderr = io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                code = cli_main(
                    [
                        "--repository",
                        str(REPOSITORY_ROOT),
                        "create",
                        str(
                            (
                                FIXTURE_ROOT
                                / "experimental-typed.blueprint.json"
                            ).relative_to(REPOSITORY_ROOT)
                        ),
                        str(project),
                    ],
                    garden_factory=lambda _: garden,
                )
            self.assertEqual(code, 0)
            self.assertEqual(stderr.getvalue(), "")
            self.assertEqual(
                garden.renderer.load_manifest(project)[
                    "architecture_kind"
                ],
                "experimental-typed",
            )
            self.assertTrue(garden.test(project)["passed"])

    def test_default_validator_rejects_untyped_architecture(self) -> None:
        report = self.garden.validate(
            FIXTURE_ROOT / "experimental-typed.blueprint.json"
        )
        codes = {item["code"] for item in report["issues"]}
        self.assertFalse(report["passed"])
        self.assertIn("schema_one_of", codes)
        self.assertIn("architecture_kind_unknown", codes)

    def test_cli_list_validate_create_and_test_exit_status(self) -> None:
        with TemporaryDirectory() as temporary:
            project = Path(temporary) / "project"
            commands = (
                ["--repository", str(REPOSITORY_ROOT), "list"],
                [
                    "--repository",
                    str(REPOSITORY_ROOT),
                    "validate",
                    "order-support-read-only",
                ],
                [
                    "--repository",
                    str(REPOSITORY_ROOT),
                    "create",
                    "order-support-read-only",
                    str(project),
                ],
                [
                    "--repository",
                    str(REPOSITORY_ROOT),
                    "test",
                    str(project),
                ],
            )
            for command in commands:
                stdout = io.StringIO()
                with redirect_stdout(stdout):
                    code = cli_main(command)
                self.assertEqual(code, 0)
                self.assertIsInstance(json.loads(stdout.getvalue()), dict)


class MiniGardenGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.baseline = build_gate_report("baseline")
        cls.broken = build_gate_report("broken")

    def test_baseline_fixes_phase_thirteen_exit_counts(self) -> None:
        self.assertTrue(self.baseline["passed"])
        self.assertEqual(self.baseline["catalog_count"], 3)
        self.assertEqual(len(self.baseline["projects"]), 3)
        self.assertEqual(
            sum(
                item["test_count"]
                for item in self.baseline["projects"].values()
            ),
            27,
        )
        self.assertEqual(self.baseline["release_ledger_records"], 1)

    def test_all_eleven_invalid_flows_are_detected(self) -> None:
        self.assertEqual(len(self.broken["cases"]), 11)
        self.assertTrue(self.broken["all_invalid_cases_detected"])
        self.assertTrue(all(item["detected"] for item in self.broken["cases"]))

    def test_gate_exit_codes_are_enforceable(self) -> None:
        self.assertEqual(exit_code(self.baseline), 0)
        self.assertEqual(exit_code(self.broken), 1)

    def test_gate_scripts_have_real_process_exit_status(self) -> None:
        baseline = subprocess.run(
            [
                sys.executable,
                "scripts/run_garden_gate.py",
                "--variant",
                "baseline",
            ],
            cwd=LAB_ROOT,
            capture_output=True,
            check=False,
        )
        broken = subprocess.run(
            [
                sys.executable,
                "scripts/run_garden_gate.py",
                "--variant",
                "broken",
            ],
            cwd=LAB_ROOT,
            capture_output=True,
            check=False,
        )
        self.assertEqual(baseline.returncode, 0)
        self.assertEqual(broken.returncode, 1)

    def test_evidence_renderer_is_byte_deterministic(self) -> None:
        command = [
            sys.executable,
            "scripts/run_garden_traces.py",
        ]
        first = subprocess.check_output(command, cwd=LAB_ROOT)
        second = subprocess.check_output(command, cwd=LAB_ROOT)
        self.assertEqual(first, second)
        self.assertRegex(hashlib.sha256(first).hexdigest(), r"^[0-9a-f]{64}$")


if __name__ == "__main__":
    unittest.main()
