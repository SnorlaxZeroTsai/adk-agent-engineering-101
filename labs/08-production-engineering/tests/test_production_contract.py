"""Dependency-free production-envelope and rollback tests."""

from __future__ import annotations

import json
import unittest

from production_lab.fixtures import build_baseline_suite
from production_lab.fixtures import build_broken_suite
from production_lab.fixtures import build_profile
from production_lab.fixtures import build_project
from production_lab.fixtures import build_release_ledger
from production_lab.gate import exit_code
from production_lab.policy import detect_environment_drift
from production_lab.rendering import diff_projects
from production_lab.rendering import render_project


def _scenario(report, scenario_id):
    return next(
        item
        for item in report.scenarios
        if item.scenario_id == scenario_id
    )


class RenderContractTests(unittest.TestCase):
    def test_all_three_baseline_envelopes_pass(self) -> None:
        report = build_baseline_suite()

        self.assertTrue(report.passed)
        for target in ("local", "cloud_run", "agent_runtime"):
            self.assertTrue(_scenario(report, f"{target}-envelope").passed)

    def test_agent_and_behavior_contracts_do_not_change_by_target(self) -> None:
        project = build_project()
        outputs = [
            render_project(project, build_profile(target))
            for target in ("local", "cloud_run", "agent_runtime")
        ]

        for path in ("agent/contract.json", "quality/behavior-gate.json"):
            self.assertEqual(
                outputs[0].file(path).content,
                outputs[1].file(path).content,
            )
            self.assertEqual(
                outputs[1].file(path).content,
                outputs[2].file(path).content,
            )

    def test_target_diff_is_limited_to_owned_lifecycle_artifacts(self) -> None:
        project = build_project()
        local = render_project(project, build_profile("local"))
        cloud = render_project(project, build_profile("cloud_run"))

        changed = {item.path for item in diff_projects(local, cloud)}

        self.assertEqual(
            changed,
            {
                "deployment/spec.json",
                "lifecycle/manifest.json",
                "release/candidate.json",
                "runtime/config.json",
            },
        )

    def test_render_contains_secret_references_not_material(self) -> None:
        project = build_project()
        output = render_project(project, build_profile("cloud_run"))
        rendered = json.dumps(output.as_dict(), sort_keys=True)

        self.assertIn('"secret_id": "payments-api-key"', rendered)
        self.assertNotIn("secret-material-for-payments-api-key", rendered)

    def test_target_profiles_choose_distinct_artifact_and_rollback_owners(
        self,
    ) -> None:
        profiles = {
            target: build_profile(target)
            for target in ("local", "cloud_run", "agent_runtime")
        }

        self.assertEqual(profiles["local"].artifact_kind, "source_tree")
        self.assertEqual(
            profiles["cloud_run"].rollback_strategy,
            "traffic_shift",
        )
        self.assertEqual(
            profiles["agent_runtime"].rollback_strategy,
            "redeploy_immutable_bundle",
        )


class ReleaseContractTests(unittest.TestCase):
    def test_release_history_preserves_staging_promotion_evidence(self) -> None:
        ledger = build_release_ledger()
        report = ledger.validate(scenario_id="test")
        staging = ledger.get("cloud-staging-v4")
        production = ledger.get("cloud-prod-v4")

        self.assertTrue(report.passed)
        self.assertEqual(
            staging.artifact_digest,
            production.artifact_digest,
        )
        self.assertEqual(
            staging.behavior_report_digest,
            production.behavior_report_digest,
        )

    def test_cloud_run_rollback_shifts_traffic_to_previous_revision(
        self,
    ) -> None:
        plan = build_release_ledger().rollback_plan("cloud-prod-v4")

        self.assertEqual(plan.strategy, "traffic_shift")
        self.assertEqual(plan.target_release_id, "cloud-prod-v3")
        self.assertIn(
            "--to-revisions=support-agent-00003=100",
            plan.command,
        )

    def test_agent_runtime_rollback_redeploys_prior_immutable_bundle(
        self,
    ) -> None:
        plan = build_release_ledger().rollback_plan("runtime-prod-v4")

        self.assertEqual(plan.strategy, "redeploy_immutable_bundle")
        self.assertEqual(plan.target_release_id, "runtime-prod-v3")
        self.assertEqual(plan.command[-1], plan.artifact_ref)
        self.assertIn("@sha256:", plan.artifact_ref)

    def test_release_without_previous_record_cannot_rollback(self) -> None:
        ledger = build_release_ledger()

        with self.assertRaisesRegex(ValueError, "no previous"):
            ledger.rollback_plan("cloud-staging-v4")


class FailureInjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = build_broken_suite()

    def test_every_deliberate_breakage_blocks_release(self) -> None:
        self.assertFalse(self.report.passed)
        self.assertEqual(exit_code(self.report), 1)
        self.assertTrue(
            all(not scenario.passed for scenario in self.report.scenarios)
        )

    def test_plaintext_secret_and_unapproved_content_are_distinct(self) -> None:
        secret_codes = {
            item.code
            for item in _scenario(
                self.report,
                "plaintext-secret",
            ).issues
        }
        telemetry_codes = {
            item.code
            for item in _scenario(
                self.report,
                "unapproved-content-telemetry",
            ).issues
        }

        self.assertIn("plaintext_secret", secret_codes)
        self.assertIn("plain_secret_overlap", secret_codes)
        self.assertIn("trace_content_enabled", telemetry_codes)
        self.assertIn("content_capture_unapproved", telemetry_codes)
        self.assertIn("content_lifecycle_missing", telemetry_codes)

    def test_missing_eval_and_mutable_artifact_fail_independently(self) -> None:
        gate_codes = {
            item.code
            for item in _scenario(
                self.report,
                "missing-behavior-gate",
            ).issues
        }
        artifact_codes = {
            item.code
            for item in _scenario(
                self.report,
                "mutable-artifact-tag",
            ).issues
        }

        self.assertEqual(
            gate_codes,
            {"behavior_gate_failed", "behavior_evidence_missing"},
        )
        self.assertEqual(artifact_codes, {"artifact_not_immutable"})

    def test_target_mismatch_is_not_silently_ignored(self) -> None:
        codes = {
            item.code
            for item in _scenario(
                self.report,
                "target-capability-mismatch",
            ).issues
        }

        self.assertEqual(
            codes,
            {"target_artifact_mismatch", "target_rollback_mismatch"},
        )

    def test_merge_style_update_surfaces_unmanaged_and_changed_env(self) -> None:
        scenario = _scenario(
            self.report,
            "silent-live-config-preservation",
        )

        self.assertEqual(scenario.evidence["unmanaged"], ["DEBUG_BYPASS"])
        self.assertEqual(scenario.evidence["changed"], ["LOG_LEVEL"])
        self.assertEqual(
            scenario.evidence["merge_style_result"]["DEBUG_BYPASS"],
            "true",
        )

    def test_current_resource_metadata_is_not_rollback_history(self) -> None:
        scenario = _scenario(
            self.report,
            "mutable-current-resource-metadata",
        )

        self.assertGreaterEqual(len(scenario.issues), 8)
        self.assertTrue(
            all(item.code == "release_evidence_missing" for item in scenario.issues)
        )

    def test_orphaned_history_fails_promotion_and_rollback_checks(self) -> None:
        codes = {
            item.code
            for item in _scenario(
                self.report,
                "orphaned-rollback-history",
            ).issues
        }

        self.assertEqual(
            codes,
            {"previous_release_missing", "promotion_source_missing"},
        )

    def test_clean_live_environment_has_no_drift(self) -> None:
        project = build_project()
        desired = {item.name: item.value for item in project.plain_env}

        result = detect_environment_drift(
            desired,
            dict(desired),
            scenario_id="clean",
        )

        self.assertTrue(result.passed)
        self.assertEqual(result.issues, ())

    def test_baseline_and_broken_exit_codes_are_enforceable(self) -> None:
        self.assertEqual(exit_code(build_baseline_suite()), 0)
        self.assertEqual(exit_code(self.report), 1)


if __name__ == "__main__":
    unittest.main()
