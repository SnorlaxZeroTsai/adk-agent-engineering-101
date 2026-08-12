"""Dependency-free tests for evaluation contracts and gate semantics."""

from __future__ import annotations

import json
import unittest

from evaluation_lab.contracts import EvalCaseSpec
from evaluation_lab.contracts import EvalDataset
from evaluation_lab.contracts import MetricPolicy
from evaluation_lab.contracts import ObservedRun
from evaluation_lab.contracts import RetrievalEvidence
from evaluation_lab.contracts import ToolCall
from evaluation_lab.contracts import TraceSet
from evaluation_lab.dataset import build_dataset
from evaluation_lab.engine import grade_trace_set
from evaluation_lab.metrics import OUTPUT_CONTRACT
from evaluation_lab.metrics import POLICY_SAFETY
from evaluation_lab.metrics import RETRIEVAL_GROUNDING
from evaluation_lab.metrics import SCRIPTED_RESPONSE_QUALITY
from evaluation_lab.metrics import STATE_CONTRACT
from evaluation_lab.metrics import TOOL_CONTRACT
from evaluation_lab.metrics import default_metric_policies


def _policy(name: str, *, blocking: bool = True) -> MetricPolicy:
    return MetricPolicy(
        name=name,
        kind=(
            "judge"
            if name == SCRIPTED_RESPONSE_QUALITY
            else "deterministic"
        ),
        threshold=4.0 if name == SCRIPTED_RESPONSE_QUALITY else 1.0,
        blocking=blocking,
        aggregation=(
            "mean"
            if name == SCRIPTED_RESPONSE_QUALITY
            else "all_cases"
        ),
    )


def _grade(
    case: EvalCaseSpec,
    observed: ObservedRun,
    *policies: MetricPolicy,
):
    dataset = EvalDataset(dataset_id="test", cases=(case,))
    traces = TraceSet(
        trace_set_id="trace",
        dataset_id="test",
        variant="test",
        observations=(observed,),
    )
    return grade_trace_set(dataset, traces, tuple(policies))


class ContractTests(unittest.TestCase):
    def test_cross_phase_dataset_has_one_unique_case_per_phase(self) -> None:
        dataset = build_dataset()

        self.assertEqual(len(dataset.cases), 5)
        self.assertEqual(
            len({case.case_id for case in dataset.cases}),
            5,
        )
        self.assertEqual(
            {case.phase for case in dataset.cases},
            {
                "foundations",
                "workflow",
                "multi-agent",
                "context-memory",
                "rag",
            },
        )

    def test_duplicate_dataset_case_ids_are_rejected(self) -> None:
        case = EvalCaseSpec(
            case_id="duplicate",
            phase="test",
            metrics=(OUTPUT_CONTRACT,),
        )

        with self.assertRaisesRegex(ValueError, "unique"):
            EvalDataset(dataset_id="test", cases=(case, case))

    def test_trace_case_set_must_match_dataset(self) -> None:
        case = EvalCaseSpec(
            case_id="expected",
            phase="test",
            metrics=(OUTPUT_CONTRACT,),
        )
        dataset = EvalDataset(dataset_id="test", cases=(case,))
        traces = TraceSet(
            trace_set_id="trace",
            dataset_id="test",
            variant="test",
            observations=(
                ObservedRun(case_id="extra", phase="test"),
            ),
        )

        with self.assertRaisesRegex(ValueError, "missing=.*expected"):
            grade_trace_set(
                dataset,
                traces,
                (_policy(OUTPUT_CONTRACT),),
            )

    def test_reports_serialize_without_runtime_objects(self) -> None:
        case = EvalCaseSpec(
            case_id="serializable",
            phase="test",
            metrics=(OUTPUT_CONTRACT,),
            required_output_fragments=("ok",),
        )
        report = _grade(
            case,
            ObservedRun(
                case_id=case.case_id,
                phase=case.phase,
                output_text="ok",
            ),
            _policy(OUTPUT_CONTRACT),
        )

        rendered = json.dumps(report.as_dict(), sort_keys=True)
        self.assertIn('"passed": true', rendered)


class DeterministicMetricTests(unittest.TestCase):
    def test_tool_metric_requires_exact_name_order_and_arguments(self) -> None:
        case = EvalCaseSpec(
            case_id="tool",
            phase="test",
            metrics=(TOOL_CONTRACT,),
            expected_tool_calls=(
                ToolCall(name="lookup", arguments={"id": "A100"}),
            ),
        )
        report = _grade(
            case,
            ObservedRun(
                case_id=case.case_id,
                phase=case.phase,
                tool_calls=(
                    ToolCall(name="lookup", arguments={"id": "A101"}),
                ),
            ),
            _policy(TOOL_CONTRACT),
        )

        self.assertFalse(report.passed)
        self.assertIn(
            "arguments differ",
            report.case_reports[0].metric_results[0].reasons[0],
        )

    def test_state_metric_checks_nested_and_forbidden_paths(self) -> None:
        case = EvalCaseSpec(
            case_id="state",
            phase="test",
            metrics=(STATE_CONTRACT,),
            required_state={"decision.status": "approved"},
            forbidden_state_paths=("secret",),
        )
        report = _grade(
            case,
            ObservedRun(
                case_id=case.case_id,
                phase=case.phase,
                state={
                    "decision": {"status": "rejected"},
                    "secret": "visible",
                },
            ),
            _policy(STATE_CONTRACT),
        )
        metric = report.case_reports[0].metric_results[0]

        self.assertFalse(report.passed)
        self.assertEqual(len(metric.reasons), 2)

    def test_policy_metric_blocks_forbidden_model_input(self) -> None:
        case = EvalCaseSpec(
            case_id="policy",
            phase="test",
            metrics=(POLICY_SAFETY,),
            forbidden_model_input_fragments=("SECRET",),
        )
        report = _grade(
            case,
            ObservedRun(
                case_id=case.case_id,
                phase=case.phase,
                model_input_text="another user's SECRET",
            ),
            _policy(POLICY_SAFETY),
        )

        self.assertFalse(report.passed)
        self.assertIn(
            "forbidden model-input",
            report.case_reports[0].metric_results[0].reasons[0],
        )

    def test_retrieval_metric_fails_correct_answer_without_citations(
        self,
    ) -> None:
        case = EvalCaseSpec(
            case_id="rag",
            phase="test",
            metrics=(RETRIEVAL_GROUNDING,),
            require_retrieval_grounding=True,
        )
        report = _grade(
            case,
            ObservedRun(
                case_id=case.case_id,
                phase=case.phase,
                output_text="The payload is 80 kg.",
                retrieval=RetrievalEvidence(
                    retrieval_recall=1.0,
                    retrieval_precision=1.0,
                    citation_recall=0.0,
                    citation_precision=0.0,
                    access_violations=0,
                    stale_hits=0,
                    deleted_hits=0,
                    grounded=False,
                ),
            ),
            _policy(RETRIEVAL_GROUNDING),
        )

        self.assertFalse(report.passed)
        reasons = report.case_reports[0].metric_results[0].reasons
        self.assertTrue(any("citation recall" in item for item in reasons))

    def test_mean_aggregate_cannot_hide_a_blocking_case_failure(self) -> None:
        cases = (
            EvalCaseSpec(
                case_id="pass",
                phase="test",
                metrics=(OUTPUT_CONTRACT,),
                required_output_fragments=("ok",),
            ),
            EvalCaseSpec(
                case_id="fail",
                phase="test",
                metrics=(OUTPUT_CONTRACT,),
                required_output_fragments=("ok",),
            ),
        )
        dataset = EvalDataset(dataset_id="mean", cases=cases)
        traces = TraceSet(
            trace_set_id="mean-trace",
            dataset_id="mean",
            variant="test",
            observations=(
                ObservedRun(
                    case_id="pass",
                    phase="test",
                    output_text="ok",
                ),
                ObservedRun(
                    case_id="fail",
                    phase="test",
                    output_text="wrong",
                ),
            ),
        )
        average_policy = MetricPolicy(
            name=OUTPUT_CONTRACT,
            kind="deterministic",
            threshold=0.5,
            blocking=True,
            aggregation="mean",
        )
        report = grade_trace_set(dataset, traces, (average_policy,))

        self.assertEqual(report.aggregate_metrics[0].score, 0.5)
        self.assertEqual(report.aggregate_metrics[0].status, "passed")
        self.assertFalse(report.passed)
        self.assertFalse(report.case_reports[1].passed)

    def test_advisory_judge_cannot_override_deterministic_failure(self) -> None:
        case = EvalCaseSpec(
            case_id="judge",
            phase="test",
            metrics=(
                OUTPUT_CONTRACT,
                SCRIPTED_RESPONSE_QUALITY,
            ),
            required_output_fragments=("authorized source",),
        )
        report = _grade(
            case,
            ObservedRun(
                case_id=case.case_id,
                phase=case.phase,
                output_text="Fluent but unsupported answer.",
                judge_scores={SCRIPTED_RESPONSE_QUALITY: 5.0},
            ),
            _policy(OUTPUT_CONTRACT),
            _policy(SCRIPTED_RESPONSE_QUALITY, blocking=False),
        )
        results = {
            item.metric_name: item
            for item in report.case_reports[0].metric_results
        }

        self.assertEqual(
            results[SCRIPTED_RESPONSE_QUALITY].status,
            "passed",
        )
        self.assertEqual(results[OUTPUT_CONTRACT].status, "failed")
        self.assertFalse(report.passed)

    def test_default_blocking_metrics_use_all_cases_aggregation(self) -> None:
        policies = default_metric_policies()
        deterministic = [
            policy for policy in policies if policy.kind == "deterministic"
        ]
        judge = [
            policy for policy in policies if policy.kind == "judge"
        ]

        self.assertTrue(all(item.blocking for item in deterministic))
        self.assertTrue(
            all(item.aggregation == "all_cases" for item in deterministic)
        )
        self.assertEqual(len(judge), 1)
        self.assertFalse(judge[0].blocking)
        self.assertEqual(judge[0].aggregation, "mean")


if __name__ == "__main__":
    unittest.main()
