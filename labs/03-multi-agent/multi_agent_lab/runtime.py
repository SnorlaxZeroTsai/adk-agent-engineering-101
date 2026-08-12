"""Runtime harness for specialist execution-mode comparisons."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
import json
from typing import Any

from google.adk.apps import App
from google.adk.events import Event
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.sessions import Session
from google.genai import types
from pydantic import BaseModel

from .builders import build_function_scenario
from .builders import build_overlap_scenario
from .builders import build_shared_state_conflict_scenario
from .builders import build_single_turn_scenario
from .builders import build_task_hard_failure_scenario
from .builders import build_task_scenario
from .builders import build_task_validation_recovery_scenario
from .builders import build_transfer_scenario
from .builders import Scenario
from .domain import case_payload
from .scripted_model import ScriptedModel


USER_ID = "multi_agent_lab_user"
SESSION_ID = "multi_agent_lab_session"


@dataclass
class RunResult:
    """Events, persisted Session, requests and terminal error for one run."""

    events: list[Event]
    session: Session
    models: dict[str, ScriptedModel]
    error: Exception | None = None
    turn_event_counts: list[int] = field(default_factory=list)

    @property
    def model_request_count(self) -> int:
        return sum(len(model.requests) for model in self.models.values())


def _message(value: str) -> types.Content:
    return types.Content(
        role="user",
        parts=[types.Part.from_text(text=value)],
    )


def fixed_case_message() -> str:
    return json.dumps(case_payload(), sort_keys=True)


async def run_scenario(
    scenario: Scenario,
    *,
    app_name: str,
    messages: list[str] | None = None,
) -> RunResult:
    """Run one or more turns against one in-memory Session."""

    service = InMemorySessionService()
    await service.create_session(
        app_name=app_name,
        user_id=USER_ID,
        session_id=SESSION_ID,
    )
    runner = Runner(
        app=App(name=app_name, root_agent=scenario.root),
        session_service=service,
    )
    events: list[Event] = []
    error: Exception | None = None
    turn_event_counts: list[int] = []
    for message in messages or [fixed_case_message()]:
        before = len(events)
        try:
            async for event in runner.run_async(
                user_id=USER_ID,
                session_id=SESSION_ID,
                new_message=_message(message),
                yield_user_message=False,
            ):
                events.append(event)
        except Exception as caught:
            error = caught
            turn_event_counts.append(len(events) - before)
            break
        turn_event_counts.append(len(events) - before)

    session = await service.get_session(
        app_name=app_name,
        user_id=USER_ID,
        session_id=SESSION_ID,
    )
    if session is None:
        raise AssertionError("multi-agent lab session disappeared")
    await runner.close()
    return RunResult(
        events=events,
        session=session,
        models=scenario.models,
        error=error,
        turn_event_counts=turn_event_counts,
    )


async def run_baseline_comparison() -> dict[str, RunResult]:
    """Run the same capability through four execution architectures."""

    return {
        "function": await run_scenario(
            build_function_scenario(),
            app_name="function_specialist",
        ),
        "single_turn": await run_scenario(
            build_single_turn_scenario(),
            app_name="single_turn_specialist",
        ),
        "transfer": await run_scenario(
            build_transfer_scenario(follow_up=False),
            app_name="transfer_specialist",
        ),
        "task": await run_scenario(
            build_task_scenario(),
            app_name="task_specialist",
        ),
    }


async def run_transfer_continuation() -> RunResult:
    """Show that a transferred chat specialist owns the next turn."""

    return await run_scenario(
        build_transfer_scenario(follow_up=True),
        app_name="transfer_continuation",
        messages=[
            fixed_case_message(),
            "Explain the same assignment again.",
        ],
    )


async def run_task_validation_recovery() -> RunResult:
    return await run_scenario(
        build_task_validation_recovery_scenario(),
        app_name="task_validation_recovery",
    )


async def run_task_hard_failure() -> RunResult:
    return await run_scenario(
        build_task_hard_failure_scenario(),
        app_name="task_hard_failure",
    )


async def run_overlap_trace() -> RunResult:
    return await run_scenario(
        build_overlap_scenario(),
        app_name="overlap_specialists",
    )


async def run_shared_state_conflict() -> RunResult:
    return await run_scenario(
        build_shared_state_conflict_scenario(),
        app_name="shared_state_conflict",
    )


def _json_safe(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    return value


def summarize_event(event: Event) -> dict[str, Any]:
    calls = [
        {
            "id": call.id,
            "name": call.name,
            "args": _json_safe(call.args),
        }
        for call in event.get_function_calls()
    ]
    responses = [
        {
            "id": response.id,
            "name": response.name,
            "response": _json_safe(response.response),
        }
        for response in event.get_function_responses()
    ]
    parts = event.content.parts if event.content and event.content.parts else []
    text = "".join(part.text or "" for part in parts)
    if event.error_code:
        kind = "error"
    elif calls:
        kind = "function_call"
    elif responses:
        kind = "function_response"
    elif event.output is not None:
        kind = "output"
    else:
        kind = "message"
    return {
        "author": event.author,
        "kind": kind,
        "text": text,
        "function_calls": calls,
        "function_responses": responses,
        "output": _json_safe(event.output),
        "state_delta": _json_safe(event.actions.state_delta),
        "transfer_to_agent": event.actions.transfer_to_agent,
        "node_path": event.node_info.path,
        "isolation_scope": event.isolation_scope,
        "branch": event.branch,
        "error_code": event.error_code,
        "error_message": event.error_message,
    }


def summarize_result(result: RunResult) -> dict[str, Any]:
    return {
        "yielded_events": [
            summarize_event(event) for event in result.events
        ],
        "stored_event_count": len(result.session.events),
        "stored_state": _json_safe(result.session.state),
        "model_requests": {
            name: len(model.requests)
            for name, model in result.models.items()
        },
        "model_request_count": result.model_request_count,
        "turn_event_counts": result.turn_event_counts,
        "error": (
            {
                "type": type(result.error).__name__,
                "message": str(result.error),
            }
            if result.error
            else None
        ),
    }
