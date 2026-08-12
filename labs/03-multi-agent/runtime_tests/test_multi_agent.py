"""Behavioral comparison of ADK specialist execution lifecycles."""

from __future__ import annotations

import json
import logging
import unittest
import warnings

from multi_agent_lab.domain import decision_payload
from multi_agent_lab.runtime import run_baseline_comparison
from multi_agent_lab.runtime import run_overlap_trace
from multi_agent_lab.runtime import run_shared_state_conflict
from multi_agent_lab.runtime import run_task_hard_failure
from multi_agent_lab.runtime import run_task_validation_recovery
from multi_agent_lab.runtime import run_transfer_continuation
from multi_agent_lab.runtime import summarize_event


logging.getLogger("google_adk").setLevel(logging.CRITICAL)
warnings.filterwarnings(
    "ignore",
    message=r".*JSON_SCHEMA_FOR_FUNC_DECL.*",
)


def _request_texts(request) -> list[str]:
    return [
        part.text
        for content in request.contents or []
        for part in content.parts or []
        if part.text
    ]


def _finish_task_responses(result) -> list[dict]:
    return [
        response.response
        for event in result.events
        for response in event.get_function_responses()
        if response.name == "finish_task"
    ]


class SpecialistModeTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self._asyncioTestLoop.slow_callback_duration = 10

    async def test_all_baselines_materialize_same_typed_decision(
        self,
    ) -> None:
        results = await run_baseline_comparison()
        expected = decision_payload()

        for name, result in results.items():
            with self.subTest(mode=name):
                self.assertIsNone(result.error)
                self.assertEqual(
                    result.session.state["triage_result"],
                    expected,
                )

    async def test_model_call_cost_increases_with_reasoning_boundaries(
        self,
    ) -> None:
        results = await run_baseline_comparison()

        self.assertEqual(
            {
                name: result.model_request_count
                for name, result in results.items()
            },
            {
                "function": 0,
                "single_turn": 1,
                "transfer": 2,
                "task": 3,
            },
        )

    async def test_event_trajectories_distinguish_transfer_and_task(
        self,
    ) -> None:
        results = await run_baseline_comparison()
        transfer = [summarize_event(event) for event in results["transfer"].events]
        task = [summarize_event(event) for event in results["task"].events]

        self.assertEqual(
            [event["kind"] for event in transfer],
            ["function_call", "function_response", "message"],
        )
        self.assertEqual(
            [event["author"] for event in transfer],
            [
                "transfer_coordinator",
                "transfer_coordinator",
                "transfer_triage",
            ],
        )
        self.assertEqual(
            [event["kind"] for event in task],
            [
                "function_call",
                "function_call",
                "function_response",
                "function_response",
                "message",
            ],
        )
        self.assertEqual(task[1]["function_calls"][0]["name"], "finish_task")
        self.assertEqual(task[3]["author"], "user")

    async def test_single_turn_and_task_specialists_receive_isolated_input(
        self,
    ) -> None:
        results = await run_baseline_comparison()
        single_request = results["single_turn"].models[
            "single_turn_triage"
        ].requests[0]
        task_request = results["task"].models["task_triage"].requests[0]

        self.assertTrue(any("CASE-100" in text for text in _request_texts(
            single_request
        )))
        self.assertTrue(any("CASE-100" in text for text in _request_texts(
            task_request
        )))
        self.assertNotIn(
            "CASE-100 was assigned",
            "\n".join(_request_texts(task_request)),
        )
        task_events = [
            event
            for event in results["task"].events
            if event.author == "task_triage"
        ]
        self.assertTrue(task_events)
        self.assertEqual(
            {event.isolation_scope for event in task_events},
            {"delegate-case-1"},
        )

    async def test_transfer_specialist_owns_follow_up_turn_and_history(
        self,
    ) -> None:
        result = await run_transfer_continuation()
        coordinator = result.models["transfer_coordinator"]
        specialist = result.models["transfer_triage"]

        self.assertIsNone(result.error)
        self.assertEqual(len(coordinator.requests), 1)
        self.assertEqual(len(specialist.requests), 2)
        self.assertEqual(result.turn_event_counts, [3, 1])
        self.assertEqual(result.events[-1].author, "transfer_triage")
        second_request_text = "\n".join(_request_texts(
            specialist.requests[1]
        ))
        self.assertIn("Explain the same assignment again.", second_request_text)
        self.assertIn('"owner": "risk_operations"', second_request_text)

    async def test_task_output_validation_error_is_repaired_by_specialist(
        self,
    ) -> None:
        result = await run_task_validation_recovery()
        responses = _finish_task_responses(result)

        self.assertIsNone(result.error)
        self.assertEqual(
            len(result.models["recovering_triage"].requests),
            2,
        )
        self.assertEqual(len(responses), 2)
        self.assertIn("error", responses[0])
        self.assertEqual(responses[1]["result"], "Task completed.")
        self.assertEqual(
            result.session.state["triage_result"],
            decision_payload(),
        )

    async def test_hard_specialist_failure_propagates_without_fallback(
        self,
    ) -> None:
        result = await run_task_hard_failure()

        self.assertIsInstance(result.error, RuntimeError)
        self.assertEqual(str(result.error), "specialist model unavailable")
        self.assertEqual(
            len(result.models["failure_coordinator"].requests),
            1,
        )
        error_events = [
            event for event in result.events if event.error_code
        ]
        self.assertEqual(len(error_events), 1)
        self.assertEqual(error_events[0].author, "failure_coordinator")
        self.assertIn("/failing_triage@", error_events[0].node_info.path)
        self.assertNotIn("triage_result", result.session.state)

    async def test_overlapping_specialists_are_both_model_visible(
        self,
    ) -> None:
        result = await run_overlap_trace()
        request = result.models["overlap_coordinator"].requests[0]
        first = request.tools_dict["overlap_triage_a"]._get_declaration()
        second = request.tools_dict["overlap_triage_b"]._get_declaration()

        self.assertEqual(
            set(request.tools_dict),
            {"overlap_triage_a", "overlap_triage_b"},
        )
        self.assertEqual(first.description, second.description)
        self.assertEqual(
            first.parameters_json_schema,
            second.parameters_json_schema,
        )
        self.assertEqual(
            len(result.models["overlap_triage_a"].requests),
            0,
        )
        self.assertEqual(
            len(result.models["overlap_triage_b"].requests),
            1,
        )
        self.assertEqual(
            result.session.state["overlap_b_result"]["owner"],
            "priority_support",
        )
        self.assertNotEqual(
            result.session.state["overlap_b_result"],
            decision_payload(),
        )

    async def test_shared_state_key_is_silent_last_writer_wins(
        self,
    ) -> None:
        result = await run_shared_state_conflict()
        writes = [
            event.actions.state_delta["triage_result"]
            for event in result.events
            if "triage_result" in event.actions.state_delta
        ]

        self.assertIsNone(result.error)
        self.assertEqual(len(writes), 2)
        self.assertEqual(writes[0]["owner"], "risk_operations")
        self.assertEqual(writes[1]["owner"], "priority_support")
        self.assertEqual(
            result.session.state["triage_result"],
            writes[1],
        )
        self.assertFalse(any(event.error_code for event in result.events))

    async def test_task_specialist_cannot_transfer_out_of_boundary(
        self,
    ) -> None:
        result = (await run_baseline_comparison())["task"]
        request = result.models["task_triage"].requests[0]

        self.assertEqual(set(request.tools_dict), {"finish_task"})


if __name__ == "__main__":
    unittest.main()
