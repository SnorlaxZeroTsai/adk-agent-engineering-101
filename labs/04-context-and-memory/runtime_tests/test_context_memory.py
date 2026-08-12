"""Behavioral tests for prompt, state, artifact and memory placement."""

from __future__ import annotations

import logging
import unittest
import warnings

from pydantic import BaseModel

from context_memory_lab.domain import EXPECTED_ANSWER
from context_memory_lab.domain import render_dossier
from context_memory_lab.runtime import request_text
from context_memory_lab.runtime import run_artifact_scope_trace
from context_memory_lab.runtime import run_baseline_comparison
from context_memory_lab.runtime import run_large_context_comparison
from context_memory_lab.runtime import run_leaky_memory_trace
from context_memory_lab.runtime import run_memory_lifecycle_trace
from context_memory_lab.runtime import run_state_context
from context_memory_lab.runtime import run_state_scope_trace
from google.adk.sessions.state import State
from google.adk.sessions.state import StateSchemaError


logging.getLogger("google_adk").setLevel(logging.CRITICAL)
warnings.filterwarnings(
    "ignore",
    message=r".*JSON_SCHEMA_FOR_FUNC_DECL.*",
)


def _final_text(result) -> str:
    texts = [
        part.text
        for event in result.events
        if event.content
        for part in event.content.parts or []
        if part.text
    ]
    return texts[-1]


class PlacementBaselineTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self._asyncioTestLoop.slow_callback_duration = 10

    async def test_all_placements_produce_same_scripted_answer(self) -> None:
        results = await run_baseline_comparison()

        for name, result in results.items():
            with self.subTest(placement=name):
                self.assertIsNone(result.error)
                self.assertEqual(_final_text(result), EXPECTED_ANSWER)

    async def test_model_request_count_reflects_explicit_artifact_load(
        self,
    ) -> None:
        results = await run_baseline_comparison()

        self.assertEqual(
            {
                name: result.model_request_count
                for name, result in results.items()
            },
            {
                "transient": 1,
                "state": 1,
                "artifact": 2,
                "memory": 1,
            },
        )

    async def test_transient_context_is_model_visible_not_persisted(
        self,
    ) -> None:
        result = (await run_baseline_comparison())["transient"]
        request = request_text(result.model.requests[0])

        self.assertIn(render_dossier(), request)
        self.assertNotIn("support_context", result.session.state)
        stored_text = "\n".join(
            part.text or ""
            for event in result.session.events
            if event.content
            for part in event.content.parts or []
        )
        self.assertNotIn(render_dossier(), stored_text)

    async def test_state_context_is_in_instruction_and_session(self) -> None:
        result = (await run_baseline_comparison())["state"]
        request = request_text(result.model.requests[0])

        self.assertIn(
            "Use this support context: Preferred contact channel: SMS",
            request,
        )
        self.assertEqual(
            result.session.state["support_context"],
            render_dossier(),
        )

    async def test_artifact_is_invisible_until_tool_response(self) -> None:
        result = (await run_baseline_comparison())["artifact"]
        first = request_text(result.model.requests[0])
        second = request_text(result.model.requests[1])

        self.assertNotIn(render_dossier(), first)
        self.assertIn(render_dossier(), second)
        self.assertEqual(
            await result.artifact_service.list_versions(
                app_name="context_memory_lab",
                user_id="alice",
                session_id="current",
                filename="user:support-dossier.txt",
            ),
            [0, 1],
        )
        responses = [
            response
            for event in result.events
            for response in event.get_function_responses()
        ]
        self.assertEqual(responses[0].name, "load_support_dossier")

    async def test_memory_is_preloaded_without_copying_into_session(
        self,
    ) -> None:
        result = (await run_baseline_comparison())["memory"]
        request = request_text(result.model.requests[0])

        self.assertIn("<PAST_CONVERSATIONS>", request)
        self.assertIn(render_dossier(), request)
        self.assertEqual(result.session.state, {})
        stored_text = "\n".join(
            part.text or ""
            for event in result.session.events
            if event.content
            for part in event.content.parts or []
        )
        self.assertNotIn(render_dossier(), stored_text)


class LifecycleFailureTests(unittest.IsolatedAsyncioTestCase):
    async def test_state_remains_stale_until_an_explicit_write(self) -> None:
        result = await run_state_context(stale_second_turn=True)
        second = request_text(result.model.requests[1])

        self.assertIn("Preferred contact channel: SMS", second)
        self.assertIn("changed their preferred channel to email", second)
        self.assertEqual(
            result.session.state["support_context"],
            render_dossier(),
        )

    async def test_large_transient_context_repeats_while_artifact_is_on_demand(
        self,
    ) -> None:
        results = await run_large_context_comparison()
        transient_requests = [
            request_text(request)
            for request in results["transient"].model.requests
        ]
        artifact_requests = [
            request_text(request)
            for request in results["artifact"].model.requests
        ]

        self.assertEqual(
            [
                "Diagnostic sample:" in request
                for request in transient_requests
            ],
            [True, True],
        )
        self.assertEqual(
            [
                "Diagnostic sample:" in request
                for request in artifact_requests
            ],
            [False, True, False],
        )
        self.assertGreater(len(transient_requests[0]), 20_000)
        self.assertLess(len(artifact_requests[-1]), 500)

    async def test_state_prefixes_have_different_lifetimes(self) -> None:
        trace = await run_state_scope_trace()

        self.assertEqual(
            trace.invocation_state["temp:scratch"],
            "invocation-only",
        )
        self.assertNotIn("temp:scratch", trace.persisted_event_delta)
        self.assertNotIn("temp:scratch", trace.same_session)
        self.assertEqual(trace.same_session["case_status"], "open")
        self.assertNotIn(
            "case_status",
            trace.same_user_new_session,
        )
        self.assertEqual(
            trace.same_user_new_session["user:channel"],
            "SMS",
        )
        self.assertNotIn(
            "user:channel",
            trace.other_user_new_session,
        )
        self.assertEqual(
            trace.other_user_new_session["app:policy_version"],
            "2026-08",
        )

    async def test_artifacts_enforce_scope_version_and_delete(self) -> None:
        trace = await run_artifact_scope_trace()

        self.assertEqual(trace.session_versions, [0, 1])
        self.assertEqual(trace.latest_session_text, "session version one")
        self.assertEqual(trace.old_session_text, "session version zero")
        self.assertIsNone(trace.same_user_other_session_text)
        self.assertEqual(
            trace.user_scoped_other_session_text,
            render_dossier(),
        )
        self.assertIsNone(trace.other_user_text)
        self.assertEqual(trace.versions_after_delete, [])

    async def test_memory_is_user_scoped_but_outlives_source_session(
        self,
    ) -> None:
        trace = await run_memory_lifecycle_trace()

        self.assertEqual(trace.same_user_matches, [render_dossier()])
        self.assertEqual(trace.other_user_matches, [])
        self.assertEqual(
            trace.after_session_delete_matches,
            [render_dossier()],
        )
        self.assertEqual(
            trace.ttl_zero_matches,
            ["Temporary channel is fax."],
        )

    async def test_broken_memory_adapter_leaks_another_user(self) -> None:
        result = await run_leaky_memory_trace()
        request = request_text(result.model.requests[0])

        self.assertIsNone(result.error)
        self.assertIn("ALICE-SECRET", request)
        self.assertEqual(result.session.user_id, "bob")


class StateSchemaTests(unittest.TestCase):
    def test_prefixed_keys_bypass_state_schema_validation(self) -> None:
        class DeclaredState(BaseModel):
            counter: int | None = None

        state = State({}, {}, schema=DeclaredState)
        with self.assertRaisesRegex(StateSchemaError, "unknown"):
            state["unknown"] = "not allowed"

        state["user:unknown"] = {"unvalidated": True}
        state["app:unknown"] = object()
        state["temp:unknown"] = "scratch"

        self.assertIn("user:unknown", state)
        self.assertIn("app:unknown", state)
        self.assertIn("temp:unknown", state)


if __name__ == "__main__":
    unittest.main()
