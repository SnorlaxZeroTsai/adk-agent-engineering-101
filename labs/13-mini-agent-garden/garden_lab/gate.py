"""End-to-end baseline and deliberate Mini Agent Garden failures."""

from __future__ import annotations

from contextlib import redirect_stderr
from contextlib import redirect_stdout
from copy import deepcopy
from dataclasses import replace
import io
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
PACKAGE_ROOT = REPOSITORY_ROOT / "mini-agent-garden"
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from mini_agent_garden.architecture import ArchitectureRegistry  # noqa: E402
from mini_agent_garden.catalog import CatalogRegistry  # noqa: E402
from mini_agent_garden.cli import main as cli_main  # noqa: E402
from mini_agent_garden.contracts import ContractReport  # noqa: E402
from mini_agent_garden.contracts import TestSpec  # noqa: E402
from mini_agent_garden.errors import ContractValidationError  # noqa: E402
from mini_agent_garden.errors import GardenError  # noqa: E402
from mini_agent_garden.errors import ProjectIntegrityError  # noqa: E402
from mini_agent_garden.errors import UnknownBlueprintError  # noqa: E402
from mini_agent_garden.errors import UpgradeReviewRequired  # noqa: E402
from mini_agent_garden.service import MiniAgentGarden  # noqa: E402


BLUEPRINT_IDS = (
    "order-support-read-only",
    "research-workflow-rag",
    "case-triage-with-approval",
)
EXPECTED_TEST_COUNTS = {
    "order-support-read-only": 13,
    "research-workflow-rag": 7,
    "case-triage-with-approval": 7,
}
FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures"


class ExperimentalHandler:
    kind = "experimental-typed"

    def render_descriptor(
        self,
        blueprint: dict[str, Any],
    ) -> dict[str, Any]:
        architecture = blueprint["architecture"]
        return {
            "kind": self.kind,
            "pipeline_id": architecture["pipeline_id"],
            "steps": architecture["steps"],
        }

    def test_spec(self, implementation_root: Path) -> TestSpec:
        return TestSpec(
            command=(
                "python",
                "-m",
                "unittest",
                "discover",
                "-s",
                "tests",
                "-q",
            ),
            working_directory="implementation",
        )


class ExperimentalValidator:
    """Stand in for the typed schema/validator change required by Phase 12."""

    def validate(self, blueprint: dict[str, Any]) -> ContractReport:
        return ContractReport(
            blueprint_id=blueprint["id"],
            passed=True,
            issues=(),
            suite_summary={
                "architecture_counts": {
                    "experimental-typed": 1,
                }
            },
        )

    def require_valid(
        self,
        blueprint: dict[str, Any],
    ) -> ContractReport:
        return self.validate(blueprint)

    def migrate_legacy(
        self,
        blueprint: dict[str, Any],
    ) -> tuple[dict[str, Any], None]:
        return blueprint, None


def _load_invalid_cases() -> tuple[dict[str, str], ...]:
    value = json.loads(
        (FIXTURE_ROOT / "invalid_cases.json").read_text(
            encoding="utf-8"
        )
    )
    return tuple(value["cases"])


def _failing_runner(
    command: tuple[str, ...],
    cwd: Path,
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        args=command,
        returncode=1,
        stdout="",
        stderr="Ran 1 test\nFAILED (failures=1)\n",
    )


def _custom_architecture_evidence(
    repository: Path,
    workspace: Path,
) -> dict[str, Any]:
    architectures = ArchitectureRegistry()
    architectures.register(ExperimentalHandler())
    garden = MiniAgentGarden(
        repository,
        architectures=architectures,
        contract_validator=ExperimentalValidator(),
    )
    fixture = FIXTURE_ROOT / "experimental-typed.blueprint.json"
    output = workspace / "experimental"
    stdout = io.StringIO()
    stderr = io.StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        cli_exit = cli_main(
            [
                "--repository",
                str(repository),
                "create",
                str(fixture.relative_to(repository)),
                str(output),
            ],
            garden_factory=lambda _: garden,
        )
    report = garden.test(output)
    return {
        "cli_exit": cli_exit,
        "stderr_empty": not stderr.getvalue(),
        "architecture_kind": garden.renderer.load_manifest(output)[
            "architecture_kind"
        ],
        "test_count": report["test_count"],
        "passed": report["passed"],
    }


def _baseline(repository: Path) -> dict[str, Any]:
    garden = MiniAgentGarden(repository)
    with TemporaryDirectory() as temporary:
        workspace = Path(temporary)
        projects: dict[str, Any] = {}
        project_paths: dict[str, Path] = {}
        reports: dict[str, dict[str, Any]] = {}
        for blueprint_id in BLUEPRINT_IDS:
            output = workspace / blueprint_id
            created = garden.create(blueprint_id, output)
            report = garden.test(output)
            project_paths[blueprint_id] = output
            reports[blueprint_id] = report
            projects[blueprint_id] = {
                "architecture": created["manifest"][
                    "architecture_kind"
                ],
                "managed_file_count": len(
                    created["manifest"]["managed_files"]
                ),
                "project_digest": created["manifest"][
                    "project_digest"
                ],
                "test_count": report["test_count"],
                "behavior_report_digest": report["report_digest"],
                "passed": report["passed"],
            }

        order_project = project_paths["order-support-read-only"]
        legacy_plan = garden.upgrade(
            order_project,
            (
                repository
                / "labs"
                / "11-blueprint-schema"
                / "fixtures"
                / "order-support-v0.1.json"
            ),
        )
        user_file = order_project / "user" / "notes.txt"
        user_file.parent.mkdir(parents=True)
        user_file.write_text("owned by the project team\n", encoding="utf-8")
        updated = deepcopy(
            garden.catalog.blueprints["order-support-read-only"]
        )
        updated["extensions"]["com.phase13"] = {
            "compatible_render_revision": "1.1"
        }
        upgrade_plan = garden.upgrade(order_project, updated)
        upgrade_result = garden.upgrade(
            order_project,
            updated,
            apply=True,
        )
        upgraded_report = garden.test(order_project)

        ledger = garden.release_ledger(workspace / "releases.jsonl")
        ledger.append(
            {
                "release_id": "local-order-support-1",
                "candidate_digest": upgraded_report["candidate_digest"],
                "behavior_report_digest": upgraded_report[
                    "report_digest"
                ],
                "status": "validated-local",
            }
        )

        custom = _custom_architecture_evidence(
            repository,
            workspace,
        )
        passed = (
            all(item["passed"] for item in projects.values())
            and all(
                projects[key]["test_count"] == EXPECTED_TEST_COUNTS[key]
                for key in BLUEPRINT_IDS
            )
            and legacy_plan["plan"]["categories"]
            == ["blueprint-schema-migration"]
            and not upgrade_plan["plan"]["requires_review"]
            and upgrade_result["applied"]
            and user_file.read_text(encoding="utf-8")
            == "owned by the project team\n"
            and upgraded_report["passed"]
            and len(ledger.records()) == 1
            and custom["cli_exit"] == 0
            and custom["passed"]
        )
        return {
            "variant": "baseline",
            "passed": passed,
            "catalog_count": garden.list()["count"],
            "architecture_handlers": list(garden.architectures.kinds),
            "projects": projects,
            "legacy_migration": legacy_plan["plan"],
            "compatible_upgrade": {
                "categories": upgrade_plan["plan"]["categories"],
                "requires_review": upgrade_plan["plan"][
                    "requires_review"
                ],
                "applied": upgrade_result["applied"],
                "user_file_preserved": user_file.is_file(),
                "post_upgrade_report": upgraded_report["report_digest"],
            },
            "release_ledger_records": len(ledger.records()),
            "typed_extension": custom,
        }


def _detect_case(
    case_id: str,
    garden: MiniAgentGarden,
    workspace: Path,
    repository: Path,
) -> str | None:
    if case_id == "unknown-blueprint":
        try:
            garden.create("does-not-exist", workspace / "missing")
        except UnknownBlueprintError:
            return "unknown_blueprint"
    elif case_id == "missing-blocking-metric":
        blueprint = deepcopy(
            garden.catalog.blueprints["order-support-read-only"]
        )
        blueprint["evaluation"]["blocking_metrics"].remove(
            "output_contract"
        )
        try:
            garden.create(blueprint, workspace / "invalid")
        except ContractValidationError:
            return "contract_validation"
    elif case_id == "tampered-managed-file":
        project = workspace / "tampered"
        garden.create("order-support-read-only", project)
        tool_file = (
            project
            / "implementation"
            / "agent_basics"
            / "tools.py"
        )
        tool_file.write_text(
            tool_file.read_text(encoding="utf-8") + "\nTAMPERED = True\n",
            encoding="utf-8",
        )
        try:
            garden.test(project)
        except ProjectIntegrityError:
            return "project_integrity"
    elif case_id == "forged-candidate-digest":
        project = workspace / "forged-candidate"
        garden.create("order-support-read-only", project)
        candidate = garden.deployment.stage(project)
        forged = replace(candidate, candidate_digest="0" * 64)
        try:
            garden.behavior.evaluate(forged)
        except ProjectIntegrityError:
            return "project_integrity"
    elif case_id == "failing-behavior-command":
        failing = MiniAgentGarden(
            repository,
            behavior_runner=_failing_runner,
        )
        project = workspace / "failing"
        failing.create("order-support-read-only", project)
        if not failing.test(project)["passed"]:
            return "behavior_gate_failed"
    elif case_id == "implementation-change-without-review":
        project = workspace / "implementation-change"
        garden.create("order-support-read-only", project)
        blueprint = garden.catalog.blueprints[
            "order-support-read-only"
        ]
        selection = replace(
            garden.catalog.resolve(blueprint),
            implementation_id="python-adk-2x-next",
        )
        validation = garden.validator.require_valid(blueprint)
        target = garden.renderer.build_plan(
            blueprint,
            selection,
            validation,
        )
        plan = garden.upgrades.plan(project, target)
        try:
            garden.upgrades.apply(plan)
        except UpgradeReviewRequired:
            return "upgrade_review_required"
    elif case_id == "duplicate-release-record":
        ledger = garden.release_ledger(workspace / "duplicate.jsonl")
        record = {"release_id": "release-1", "status": "validated-local"}
        ledger.append(record)
        try:
            ledger.append(record)
        except GardenError:
            return "duplicate_release"
    elif case_id == "secret-bearing-release-record":
        ledger = garden.release_ledger(workspace / "secret.jsonl")
        try:
            ledger.append(
                {
                    "release_id": "release-secret",
                    "api_token": "not-allowed",
                }
            )
        except GardenError:
            return "secret_release"
    elif case_id == "unknown-architecture-handler":
        try:
            garden.architectures.get("unknown-kind")
        except GardenError:
            return "unknown_handler"
    elif case_id == "create-over-existing-output":
        output = workspace / "existing"
        garden.create("order-support-read-only", output)
        try:
            garden.create("order-support-read-only", output)
        except GardenError:
            return "existing_output"
    elif case_id == "untyped-architecture-extension":
        report = garden.validate(
            FIXTURE_ROOT / "experimental-typed.blueprint.json"
        )
        codes = {item["code"] for item in report["issues"]}
        if (
            not report["passed"]
            and "architecture_kind_unknown" in codes
            and "schema_one_of" in codes
        ):
            return "architecture_extension_rejected"
    return None


def _broken(repository: Path) -> dict[str, Any]:
    garden = MiniAgentGarden(repository)
    cases = []
    with TemporaryDirectory() as temporary:
        workspace = Path(temporary)
        for case in _load_invalid_cases():
            observed = _detect_case(
                case["id"],
                garden,
                workspace,
                repository,
            )
            cases.append(
                {
                    "case_id": case["id"],
                    "expected_code": case["expected_code"],
                    "observed_code": observed,
                    "detected": observed == case["expected_code"],
                }
            )
    return {
        "variant": "broken",
        "passed": False,
        "all_invalid_cases_detected": all(
            item["detected"] for item in cases
        ),
        "cases": cases,
    }


def build_gate_report(
    variant: str,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    repository = (root or REPOSITORY_ROOT).resolve()
    if variant == "baseline":
        return _baseline(repository)
    if variant == "broken":
        return _broken(repository)
    raise ValueError(f"unknown variant: {variant}")


def exit_code(report: dict[str, Any]) -> int:
    return 0 if report["passed"] else 1
