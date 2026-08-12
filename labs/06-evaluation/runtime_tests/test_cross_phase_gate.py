"""ADK-backed release-gate tests over Labs 01-05."""

from __future__ import annotations

import asyncio
import unittest

from evaluation_lab.cross_lab import collect_trace_set
from evaluation_lab.dataset import build_dataset
from evaluation_lab.engine import grade_trace_set
from evaluation_lab.gate import exit_code
from evaluation_lab.metrics import default_metric_policies
from evaluation_lab.metrics import EFFICIENCY_BUDGET
from evaluation_lab.metrics import POLICY_SAFETY
from evaluation_lab.metrics import RETRIEVAL_GROUNDING
from evaluation_lab.metrics import RUNTIME_SUCCESS
from evaluation_lab.metrics import SCRIPTED_RESPONSE_QUALITY
from evaluation_lab.metrics import STATE_CONTRACT


def _results_by_case(report):
    return {
        case.case_id: {
            metric.metric_name: metric
            for metric in case.metric_results
        }
        for case in report.case_reports
    }


class CrossPhaseGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        dataset = build_dataset()
        policies = default_metric_policies()
        cls.baseline_traces = asyncio.run(collect_trace_set("baseline"))
        cls.broken_traces = asyncio.run(collect_trace_set("broken"))
        cls.baseline = grade_trace_set(
            dataset,
            cls.baseline_traces,
            policies,
        )
        cls.broken = grade_trace_set(
            dataset,
            cls.broken_traces,
            policies,
        )

    def test_baseline_suite_passes_all_five_architectures(self) -> None:
        self.assertTrue(self.baseline.passed)
        self.assertEqual(len(self.baseline.case_reports), 5)
        self.assertTrue(
            all(case.passed for case in self.baseline.case_reports)
        )
        self.assertEqual(exit_code(self.baseline), 0)

    def test_deliberately_broken_suite_blocks_release(self) -> None:
        self.assertFalse(self.broken.passed)
        self.assertEqual(len(self.broken.blocking_failures), 24)
        self.assertEqual(exit_code(self.broken), 1)
        self.assertTrue(
            all(not case.passed for case in self.broken.case_reports)
        )

    def test_failure_reasons_identify_each_architecture_dimension(self) -> None:
        results = _results_by_case(self.broken)

        self.assertEqual(
            results["agent-tool-round-trip"][RUNTIME_SUCCESS].status,
            "failed",
        )
        self.assertEqual(
            results["workflow-explicit-exhaustion"][
                STATE_CONTRACT
            ].status,
            "failed",
        )
        self.assertEqual(
            results["bounded-task-specialist"][
                EFFICIENCY_BUDGET
            ].status,
            "failed",
        )
        self.assertEqual(
            results["memory-user-isolation"][POLICY_SAFETY].status,
            "failed",
        )
        self.assertEqual(
            results["rag-source-grounding"][
                RETRIEVAL_GROUNDING
            ].status,
            "failed",
        )

    def test_fluent_broken_outputs_do_not_override_contract_failures(
        self,
    ) -> None:
        results = _results_by_case(self.broken)

        for case_id in (
            "workflow-explicit-exhaustion",
            "bounded-task-specialist",
            "memory-user-isolation",
            "rag-source-grounding",
        ):
            with self.subTest(case_id=case_id):
                self.assertEqual(
                    results[case_id][
                        SCRIPTED_RESPONSE_QUALITY
                    ].status,
                    "passed",
                )
        judge_aggregate = next(
            item
            for item in self.broken.aggregate_metrics
            if item.metric_name == SCRIPTED_RESPONSE_QUALITY
        )
        self.assertEqual(judge_aggregate.score, 4.2)
        self.assertEqual(judge_aggregate.status, "passed")
        self.assertFalse(self.broken.passed)

    def test_dataset_trace_and_grade_stages_remain_separate(self) -> None:
        observation = self.baseline_traces.observations[0]

        self.assertFalse(hasattr(observation, "passed"))
        self.assertFalse(hasattr(observation, "metric_results"))
        self.assertTrue(hasattr(self.baseline.case_reports[0], "passed"))

    def test_baseline_and_broken_traces_cover_same_case_ids(self) -> None:
        baseline_ids = {
            item.case_id for item in self.baseline_traces.observations
        }
        broken_ids = {
            item.case_id for item in self.broken_traces.observations
        }

        self.assertEqual(baseline_ids, broken_ids)
        self.assertEqual(
            baseline_ids,
            {case.case_id for case in build_dataset().cases},
        )


if __name__ == "__main__":
    unittest.main()
