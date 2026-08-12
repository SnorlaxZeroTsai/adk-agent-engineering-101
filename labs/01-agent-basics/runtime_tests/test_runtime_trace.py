from __future__ import annotations

import logging
import unittest
import warnings

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.errors.session_not_found_error import SessionNotFoundError
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.tools import FunctionTool
from google.genai import types

from agent_basics.runtime_trace import APP_NAME
from agent_basics.runtime_trace import run_callback_failure_trace
from agent_basics.runtime_trace import run_success_trace
from agent_basics.runtime_trace import run_tool_failure_trace
from agent_basics.runtime_trace import summarize_event
from agent_basics.runtime_trace import tracked_get_order_status
from agent_basics.scripted_model import ScriptedModel
from agent_basics.scripted_model import text_response
from agent_basics.tools import estimate_shipping
from agent_basics.tools import get_order_status


logging.getLogger("google_adk").setLevel(logging.CRITICAL)
warnings.filterwarnings(
    "ignore",
    message=r".*JSON_SCHEMA_FOR_FUNC_DECL.*",
)


class FunctionDeclarationTests(unittest.TestCase):
    def test_baseline_declarations_are_narrow_and_required(self) -> None:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            order_declaration = FunctionTool(
                get_order_status
            )._get_declaration()
            shipping_declaration = FunctionTool(
                estimate_shipping
            )._get_declaration()

        order_schema = order_declaration.parameters_json_schema
        shipping_schema = shipping_declaration.parameters_json_schema
        self.assertEqual(order_schema["required"], ["order_id"])
        self.assertEqual(
            shipping_schema["required"],
            ["destination_zone", "weight_kg"],
        )
        self.assertEqual(
            shipping_schema["properties"]["destination_zone"]["enum"],
            ["local", "regional", "international"],
        )

    def test_tool_context_is_not_model_visible(self) -> None:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            declaration = FunctionTool(
                tracked_get_order_status
            )._get_declaration()

        self.assertEqual(
            declaration.parameters_json_schema["required"],
            ["order_id"],
        )
        self.assertNotIn(
            "tool_context",
            declaration.parameters_json_schema["properties"],
        )


class RunnerTraceTests(unittest.IsolatedAsyncioTestCase):
    async def test_success_trace_is_persisted_and_correlated(self) -> None:
        trace = await run_success_trace()
        summaries = [summarize_event(event) for event in trace.events]

        self.assertIsNone(trace.error)
        self.assertEqual(
            [summary["kind"] for summary in summaries],
            ["message", "function_call", "function_response", "message"],
        )
        self.assertEqual(len(trace.session.events), 4)
        self.assertEqual(trace.session.state["last_order_id"], "A100")
        call = summaries[1]["function_calls"][0]
        response = summaries[2]["function_responses"][0]
        self.assertEqual(call["id"], response["id"])
        self.assertEqual(
            summaries[2]["state_delta"],
            {"last_order_id": "A100"},
        )
        self.assertEqual(len(trace.requests), 2)
        self.assertIn(
            "tracked_get_order_status",
            trace.requests[0].tools_dict,
        )
        self.assertEqual(
            trace.requests[1].contents[-1].parts[0].function_response.name,
            "tracked_get_order_status",
        )

    async def test_same_session_continuation_includes_history(self) -> None:
        trace = await run_success_trace(continue_session=True)

        self.assertIsNone(trace.error)
        self.assertEqual(len(trace.requests), 3)
        self.assertEqual(len(trace.session.events), 6)
        final_request = trace.requests[-1]
        all_text = [
            part.text
            for content in final_request.contents
            for part in (content.parts or [])
            if part.text
        ]
        self.assertIn("Order A100 is processing.", all_text)
        self.assertIn("Which order did we just check?", all_text)
        self.assertEqual(trace.session.state["last_order_id"], "A100")

    async def test_unhandled_tool_failure_emits_error_then_propagates(
        self,
    ) -> None:
        trace = await run_tool_failure_trace(recover=False)
        summaries = [summarize_event(event) for event in trace.events]

        self.assertIsInstance(trace.error, RuntimeError)
        self.assertEqual(
            [summary["kind"] for summary in summaries],
            ["message", "function_call", "error"],
        )
        self.assertEqual(summaries[-1]["error_code"], "RuntimeError")
        self.assertEqual(len(trace.session.events), 3)

    async def test_tool_error_callback_recovers_as_function_response(
        self,
    ) -> None:
        trace = await run_tool_failure_trace(recover=True)
        summaries = [summarize_event(event) for event in trace.events]

        self.assertIsNone(trace.error)
        self.assertEqual(
            [summary["kind"] for summary in summaries],
            ["message", "function_call", "function_response", "message"],
        )
        response = summaries[2]["function_responses"][0]["response"]
        self.assertEqual(
            response["error"]["code"],
            "order_backend_unavailable",
        )

    async def test_callback_failure_emits_error_then_propagates(self) -> None:
        trace = await run_callback_failure_trace()
        summaries = [summarize_event(event) for event in trace.events]

        self.assertIsInstance(trace.error, RuntimeError)
        self.assertEqual(
            [summary["kind"] for summary in summaries],
            ["message", "error"],
        )
        self.assertEqual(len(trace.requests), 0)
        self.assertEqual(len(trace.session.events), 2)

    async def test_missing_session_is_not_silently_created(self) -> None:
        model = ScriptedModel(responses=[text_response("unused")])
        agent = Agent(name="missing_session_agent", model=model)
        runner = Runner(
            app=App(name=APP_NAME, root_agent=agent),
            session_service=InMemorySessionService(),
        )

        with self.assertRaises(SessionNotFoundError):
            async for _ in runner.run_async(
                user_id="trace_user",
                session_id="does-not-exist",
                new_message=types.Content(
                    role="user",
                    parts=[types.Part.from_text(text="hello")],
                ),
            ):
                pass
        await runner.close()


if __name__ == "__main__":
    unittest.main()
