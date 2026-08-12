"""Behavioral comparison of legacy composites and graph Workflow."""

from __future__ import annotations

import logging
import unittest
import warnings

from google.adk.workflow import START
from google.adk.workflow import Workflow

from workflow_lab.graph_pipeline import build_graph_pipeline
from workflow_lab.graph_pipeline import TransientResearchError
from workflow_lab.runtime import run_baseline_comparison
from workflow_lab.runtime import run_duplicate_output_comparison
from workflow_lab.runtime import run_graph_resume_trace
from workflow_lab.runtime import run_legacy_resume_trace
from workflow_lab.runtime import run_loop_limit_comparison
from workflow_lab.runtime import run_missing_state_trace
from workflow_lab.runtime import run_retry_comparison


logging.getLogger("google_adk").setLevel(logging.CRITICAL)
warnings.filterwarnings(
    "ignore",
    message=r"\[EXPERIMENTAL\] feature AGENT_STATE.*",
)


def _node_outputs(result, node_name: str) -> list[object]:
    marker = f"/{node_name}@"
    return [
        event.output
        for event in result.events
        if event.output is not None and marker in event.node_info.path
    ]


class WorkflowComparisonTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self._asyncioTestLoop.slow_callback_duration = 10
        warnings.filterwarnings(
            "ignore",
            message=r"\[EXPERIMENTAL\] feature AGENT_STATE.*",
        )

    async def test_equivalent_happy_paths_reach_same_final_state(self) -> None:
        results = await run_baseline_comparison()

        self.assertIsNone(results["legacy"].error)
        self.assertIsNone(results["graph"].error)
        self.assertEqual(
            results["legacy"].session.state["final"],
            results["graph"].session.state["final"],
        )
        self.assertEqual(results["legacy"].session.state["review_count"], 2)
        self.assertEqual(results["graph"].session.state["review_count"], 2)

    async def test_graph_exposes_fanout_join_loop_and_terminal_output(self) -> None:
        graph = (await run_baseline_comparison())["graph"]

        branches = {
            event.branch
            for event in graph.events
            if event.node_info.path.endswith(("facts@1", "risks@1"))
        }
        self.assertEqual(branches, {"facts@1", "risks@1"})
        self.assertEqual(len(_node_outputs(graph, "analysis_join")), 1)
        self.assertEqual(len(_node_outputs(graph, "review")), 2)
        self.assertEqual(len(_node_outputs(graph, "finalize")), 1)
        workflow_outputs = [
            event
            for event in graph.events
            if event.output is not None
            and event.node_info.path == "graph_research_pipeline@1"
        ]
        self.assertEqual(workflow_outputs, [])

    async def test_legacy_trace_contains_composite_checkpoints(self) -> None:
        legacy = (await run_baseline_comparison())["legacy"]

        checkpoint_authors = {
            event.author
            for event in legacy.events
            if event.actions.agent_state is not None
        }
        self.assertIn("legacy_research_pipeline", checkpoint_authors)
        self.assertIn("quality_loop", checkpoint_authors)
        self.assertIn("parallel_analysis", checkpoint_authors)

        stage_text = [
            part.text
            for event in legacy.events
            if event.content
            for part in event.content.parts or []
            if part.text
        ]
        self.assertEqual(stage_text.count("review"), 2)
        self.assertEqual(stage_text.count("revise"), 1)

    async def test_loop_limit_is_explicit_only_in_graph_variant(self) -> None:
        results = await run_loop_limit_comparison()
        legacy_state = results["legacy"].session.state
        graph_state = results["graph"].session.state

        self.assertEqual(legacy_state["final"]["status"], "unsafe_unapproved")
        self.assertFalse(legacy_state["approved"])
        self.assertNotIn("final", graph_state)
        self.assertEqual(graph_state["rejection"]["status"], "rejected")
        self.assertEqual(
            graph_state["rejection"]["reason"],
            "review_limit_exhausted",
        )

    async def test_graph_retry_is_local_and_observable(self) -> None:
        graph = (await run_retry_comparison())["graph"]

        self.assertIsNone(graph.error)
        self.assertEqual(graph.metrics["attempts"], 2)
        error_events = [
            event
            for event in graph.events
            if event.error_code == "TransientResearchError"
        ]
        self.assertEqual(len(error_events), 1)
        self.assertEqual(_node_outputs(graph, "flaky_fetch"), [
            {"status": "recovered"}
        ])

    async def test_legacy_child_failure_has_no_composite_retry(self) -> None:
        legacy = (await run_retry_comparison())["legacy"]

        self.assertIsInstance(legacy.error, TransientResearchError)
        self.assertEqual(legacy.metrics["attempts"], 1)
        self.assertEqual(
            [
                event
                for event in legacy.events
                if event.error_code == "TransientResearchError"
            ],
            [],
        )

    async def test_missing_state_names_the_function_parameter(self) -> None:
        result = await run_missing_state_trace()

        self.assertIsInstance(result.error, ValueError)
        self.assertIn('Missing value for parameter "draft"', str(result.error))
        error_events = [event for event in result.events if event.error_code]
        self.assertEqual(len(error_events), 1)
        self.assertTrue(error_events[0].node_info.path.endswith(
            "consume_draft@1"
        ))

    async def test_output_delegation_removes_duplicate_event(self) -> None:
        results = await run_duplicate_output_comparison()
        duplicate_outputs = [
            event
            for event in results["duplicate"].events
            if event.output == "shared-output"
        ]
        delegated_outputs = [
            event
            for event in results["delegated"].events
            if event.output == "shared-output"
        ]

        self.assertEqual(len(duplicate_outputs), 2)
        self.assertEqual(len(delegated_outputs), 1)
        self.assertIn("/child_output@", delegated_outputs[0].node_info.path)
        self.assertEqual(
            len(delegated_outputs[0].node_info.output_for),
            3,
        )

    async def test_graph_resume_replays_without_repeating_side_effect(self) -> None:
        result = await run_graph_resume_trace()

        self.assertEqual(result.ledger, ["prepared"])
        self.assertIsNone(result.first.error)
        self.assertIsNone(result.second.error)
        self.assertTrue(any(
            event.long_running_tool_ids for event in result.first.events
        ))
        self.assertEqual(
            result.second.session.state["final"],
            {"finalized": True},
        )
        self.assertEqual(
            _node_outputs(result.second, "prepare"),
            [{"prepared": True}],
        )

    async def test_legacy_resume_stops_at_interrupted_leaf(self) -> None:
        result = await run_legacy_resume_trace()

        self.assertEqual(result.ledger, ["prepared"])
        self.assertIsNone(result.first.error)
        self.assertIsNone(result.second.error)
        self.assertTrue(result.second.session.state["approved"])
        self.assertNotIn("final", result.second.session.state)
        self.assertFalse(any(
            event.author == "finalize" for event in result.second.events
        ))


class GraphValidationTests(unittest.TestCase):
    def test_unconditional_cycle_is_rejected_at_construction(self) -> None:
        def first() -> str:
            return "first"

        def second() -> str:
            return "second"

        with self.assertRaisesRegex(ValueError, "Unconditional cycle"):
            Workflow(
                name="invalid_cycle",
                edges=[
                    (START, first, second),
                    (second, first),
                ],
            )

    def test_duplicate_edge_is_rejected_at_construction(self) -> None:
        graph = build_graph_pipeline()
        intake = next(node for node in graph.graph.nodes if node.name == "intake")
        facts = next(node for node in graph.graph.nodes if node.name == "facts")

        with self.assertRaisesRegex(ValueError, "Duplicate edge"):
            Workflow(
                name="invalid_duplicate",
                edges=[
                    (START, intake),
                    (intake, facts),
                    (intake, facts),
                ],
            )


if __name__ == "__main__":
    unittest.main()
