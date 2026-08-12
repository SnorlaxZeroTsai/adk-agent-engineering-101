"""Reproducible ADK Runner traces for success and failure paths."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.events import Event
from google.adk.models.llm_request import LlmRequest
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.sessions.session import Session
from google.adk.tools.tool_context import ToolContext
from google.genai import types

from .scripted_model import function_call_response
from .scripted_model import ScriptedModel
from .scripted_model import text_response
from .tools import get_order_status


APP_NAME = "order_support_trace"
USER_ID = "trace_user"
SESSION_ID = "trace_session"


@dataclass
class TraceResult:
    """Captured Runner output and persisted state for one experiment."""

    events: list[Event]
    session: Session
    requests: list[LlmRequest]
    error: Exception | None = None


def tracked_get_order_status(
    order_id: str,
    tool_context: ToolContext,
) -> dict[str, object]:
    """Look up an order and record the successful lookup in session state.

    Args:
        order_id: Customer-visible order ID, such as ``A100``.
        tool_context: ADK-injected runtime context; it is hidden from the model.

    Returns:
        The same structured result as ``get_order_status``.
    """

    result = get_order_status(order_id)
    if result["ok"]:
        tool_context.state["last_order_id"] = order_id.strip().upper()
    return result


def failing_order_backend(order_id: str) -> dict[str, object]:
    """Simulate an unexpected infrastructure failure for one order lookup."""

    raise RuntimeError(f"Order backend unavailable for {order_id}")


def failing_before_agent_callback(callback_context: Any) -> None:
    """Simulate a callback implementation failure before model execution."""

    del callback_context
    raise RuntimeError("before_agent_callback failed")


def _message(text: str) -> types.Content:
    return types.Content(
        role="user",
        parts=[types.Part.from_text(text=text)],
    )


async def _collect(
    runner: Runner,
    *,
    new_message: str,
) -> tuple[list[Event], Exception | None]:
    events: list[Event] = []
    error: Exception | None = None
    try:
        async for event in runner.run_async(
            user_id=USER_ID,
            session_id=SESSION_ID,
            new_message=_message(new_message),
            yield_user_message=True,
        ):
            events.append(event)
    except Exception as caught:
        error = caught
    return events, error


async def _stored_session(
    session_service: InMemorySessionService,
) -> Session:
    session = await session_service.get_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
    )
    if session is None:
        raise AssertionError("Trace session disappeared.")
    return session


async def run_success_trace(*, continue_session: bool = False) -> TraceResult:
    """Run a deterministic tool round trip, optionally followed by another turn."""

    responses = [
        function_call_response(
            "tracked_get_order_status",
            {"order_id": "A100"},
            call_id="call-order-status-1",
        ),
        text_response("Order A100 is processing."),
    ]
    if continue_session:
        responses.append(
            text_response("The last order checked in this session was A100.")
        )

    model = ScriptedModel(responses=responses)
    agent = Agent(
        name="order_trace_agent",
        model=model,
        instruction="Use the order lookup tool and report its result.",
        tools=[tracked_get_order_status],
        mode="chat",
    )
    session_service = InMemorySessionService()
    await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
    )
    runner = Runner(
        app=App(name=APP_NAME, root_agent=agent),
        session_service=session_service,
    )

    events, error = await _collect(
        runner,
        new_message="What is the status of order A100?",
    )
    if continue_session and error is None:
        continued_events, error = await _collect(
            runner,
            new_message="Which order did we just check?",
        )
        events.extend(continued_events)

    session = await _stored_session(session_service)
    await runner.close()
    return TraceResult(
        events=events,
        session=session,
        requests=model.requests,
        error=error,
    )


async def run_tool_failure_trace(*, recover: bool) -> TraceResult:
    """Compare an unhandled tool exception with callback-based recovery."""

    responses = [
        function_call_response(
            "failing_order_backend",
            {"order_id": "A100"},
            call_id="call-failing-order-1",
        )
    ]
    if recover:
        responses.append(
            text_response("I could not reach the order backend. Please retry.")
        )
    model = ScriptedModel(responses=responses)

    async def recover_tool_error(
        tool: object,
        args: dict[str, object],
        tool_context: ToolContext,
        error: Exception,
    ) -> dict[str, object]:
        del tool, args, tool_context
        return {
            "ok": False,
            "error": {
                "code": "order_backend_unavailable",
                "message": str(error),
            },
        }

    agent = Agent(
        name="failure_trace_agent",
        model=model,
        instruction="Use the order backend and report failures honestly.",
        tools=[failing_order_backend],
        mode="chat",
        on_tool_error_callback=recover_tool_error if recover else None,
    )
    session_service = InMemorySessionService()
    await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
    )
    runner = Runner(
        app=App(name=APP_NAME, root_agent=agent),
        session_service=session_service,
    )
    events, error = await _collect(
        runner,
        new_message="Check order A100.",
    )
    session = await _stored_session(session_service)
    await runner.close()
    return TraceResult(
        events=events,
        session=session,
        requests=model.requests,
        error=error,
    )


async def run_callback_failure_trace() -> TraceResult:
    """Observe a before-agent callback exception."""

    model = ScriptedModel(
        responses=[text_response("This response must never be reached.")]
    )
    agent = Agent(
        name="callback_failure_agent",
        model=model,
        before_agent_callback=failing_before_agent_callback,
    )
    session_service = InMemorySessionService()
    await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
    )
    runner = Runner(
        app=App(name=APP_NAME, root_agent=agent),
        session_service=session_service,
    )
    events, error = await _collect(
        runner,
        new_message="Trigger the callback.",
    )
    session = await _stored_session(session_service)
    await runner.close()
    return TraceResult(
        events=events,
        session=session,
        requests=model.requests,
        error=error,
    )


def summarize_event(event: Event) -> dict[str, object]:
    """Return deterministic, JSON-safe fields from an Event."""

    function_calls = [
        {
            "id": call.id,
            "name": call.name,
            "args": call.args,
        }
        for call in event.get_function_calls()
    ]
    function_responses = [
        {
            "id": response.id,
            "name": response.name,
            "response": response.response,
        }
        for response in event.get_function_responses()
    ]
    parts = event.content.parts if event.content and event.content.parts else []
    text = "".join(part.text or "" for part in parts)

    if event.error_code:
        kind = "error"
    elif function_calls:
        kind = "function_call"
    elif function_responses:
        kind = "function_response"
    else:
        kind = "message"

    return {
        "author": event.author,
        "kind": kind,
        "text": text,
        "function_calls": function_calls,
        "function_responses": function_responses,
        "state_delta": event.actions.state_delta,
        "error_code": event.error_code,
        "error_message": event.error_message,
        "node_path": event.node_info.path,
        "partial": event.partial,
    }


def summarize_trace(trace: TraceResult) -> dict[str, object]:
    """Return stable evidence suitable for a learning-note snapshot."""

    return {
        "yielded_events": [summarize_event(event) for event in trace.events],
        "stored_event_count": len(trace.session.events),
        "stored_state": trace.session.state,
        "model_request_count": len(trace.requests),
        "error": (
            {
                "type": type(trace.error).__name__,
                "message": str(trace.error),
            }
            if trace.error
            else None
        ),
    }
