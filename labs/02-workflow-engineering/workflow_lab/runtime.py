"""Executable runtime experiments for the workflow comparison."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
import warnings
from typing import Any

from google.adk.apps import App
from google.adk.apps import ResumabilityConfig
from google.adk.events import Event
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.sessions import Session
from google.genai import types

from .graph_pipeline import APPROVAL_INTERRUPT_ID
from .graph_pipeline import build_duplicate_output_workflow
from .graph_pipeline import build_graph_approval_workflow
from .graph_pipeline import build_graph_pipeline
from .graph_pipeline import build_missing_state_workflow
from .graph_pipeline import build_retry_workflow
from .legacy_pipeline import build_legacy_approval_pipeline
from .legacy_pipeline import build_legacy_failure_pipeline
from .legacy_pipeline import build_legacy_pipeline


USER_ID = "workflow_lab_user"
SESSION_ID = "workflow_lab_session"


@dataclass
class RunResult:
    """Events, persisted Session and terminal exception for one run."""

    events: list[Event]
    session: Session
    error: Exception | None = None
    metrics: dict[str, Any] = field(default_factory=dict)


@dataclass
class ResumeResult:
    """Two turns around an interrupt plus the external side-effect ledger."""

    first: RunResult
    second: RunResult
    ledger: list[str]


def text_message(text: str) -> types.Content:
    return types.Content(
        role="user",
        parts=[types.Part(text=text)],
    )


def approval_message(*, approved: bool) -> types.Content:
    return types.Content(
        role="user",
        parts=[
            types.Part(
                function_response=types.FunctionResponse(
                    name="approve_brief",
                    id=APPROVAL_INTERRUPT_ID,
                    response={"approved": approved},
                )
            )
        ],
    )


def _app(name: str, root: Any, *, resumable: bool) -> App:
    config = None
    if resumable:
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message=r"\[EXPERIMENTAL\] ResumabilityConfig.*",
            )
            config = ResumabilityConfig(is_resumable=True)
    return App(
        name=name,
        root_agent=root,
        resumability_config=config,
    )


async def _stored_session(
    service: InMemorySessionService,
    *,
    app_name: str,
) -> Session:
    session = await service.get_session(
        app_name=app_name,
        user_id=USER_ID,
        session_id=SESSION_ID,
    )
    if session is None:
        raise AssertionError("workflow lab session disappeared")
    return session


async def _run_with_service(
    *,
    root: Any,
    app_name: str,
    service: InMemorySessionService,
    message: types.Content,
    resumable: bool = False,
) -> RunResult:
    runner = Runner(
        app=_app(app_name, root, resumable=resumable),
        session_service=service,
    )
    events: list[Event] = []
    error: Exception | None = None
    try:
        async for event in runner.run_async(
            user_id=USER_ID,
            session_id=SESSION_ID,
            new_message=message,
            yield_user_message=False,
        ):
            events.append(event)
    except Exception as caught:
        error = caught
    session = await _stored_session(service, app_name=app_name)
    await runner.close()
    return RunResult(events=events, session=session, error=error)


async def run_once(
    root: Any,
    *,
    app_name: str,
    message: str = "payment reliability",
    resumable: bool = False,
) -> RunResult:
    """Run a fresh root against a fresh in-memory Session."""

    service = InMemorySessionService()
    await service.create_session(
        app_name=app_name,
        user_id=USER_ID,
        session_id=SESSION_ID,
    )
    return await _run_with_service(
        root=root,
        app_name=app_name,
        service=service,
        message=text_message(message),
        resumable=resumable,
    )


async def run_baseline_comparison() -> dict[str, RunResult]:
    """Run equivalent legacy and graph pipelines."""

    legacy = await run_once(
        build_legacy_pipeline(),
        app_name="legacy_baseline",
        resumable=True,
    )
    graph = await run_once(
        build_graph_pipeline(),
        app_name="graph_baseline",
        resumable=True,
    )
    return {"legacy": legacy, "graph": graph}


async def run_loop_limit_comparison() -> dict[str, RunResult]:
    """Compare implicit LoopAgent exhaustion with explicit graph rejection."""

    legacy = await run_once(
        build_legacy_pipeline(
            required_reviews=99,
            max_iterations=2,
            unsafe_finalize=True,
        ),
        app_name="legacy_loop_limit",
    )
    graph = await run_once(
        build_graph_pipeline(
            required_reviews=99,
            max_reviews=2,
        ),
        app_name="graph_loop_limit",
    )
    return {"legacy": legacy, "graph": graph}


async def run_retry_comparison() -> dict[str, RunResult]:
    """Compare graph node retry with a legacy child failure."""

    graph_tracker: dict[str, int] = {}
    graph = await run_once(
        build_retry_workflow(graph_tracker),
        app_name="graph_retry",
    )
    graph.metrics["attempts"] = graph_tracker["attempts"]

    legacy_tracker: dict[str, int] = {}
    legacy = await run_once(
        build_legacy_failure_pipeline(legacy_tracker),
        app_name="legacy_retry",
    )
    legacy.metrics["attempts"] = legacy_tracker["attempts"]
    return {"legacy": legacy, "graph": graph}


async def run_missing_state_trace() -> RunResult:
    return await run_once(
        build_missing_state_workflow(),
        app_name="graph_missing_state",
    )


async def run_duplicate_output_comparison() -> dict[str, RunResult]:
    duplicate = await run_once(
        build_duplicate_output_workflow(delegate_output=False),
        app_name="graph_duplicate_output",
    )
    delegated = await run_once(
        build_duplicate_output_workflow(delegate_output=True),
        app_name="graph_delegated_output",
    )
    return {"duplicate": duplicate, "delegated": delegated}


async def run_graph_resume_trace() -> ResumeResult:
    """Resume with a fresh Workflow and Runner over the same Session service."""

    app_name = "graph_resume"
    ledger: list[str] = []
    service = InMemorySessionService()
    await service.create_session(
        app_name=app_name,
        user_id=USER_ID,
        session_id=SESSION_ID,
    )
    first = await _run_with_service(
        root=build_graph_approval_workflow(ledger),
        app_name=app_name,
        service=service,
        message=text_message("prepare the brief"),
        resumable=True,
    )
    second = await _run_with_service(
        root=build_graph_approval_workflow(ledger),
        app_name=app_name,
        service=service,
        message=approval_message(approved=True),
        resumable=True,
    )
    return ResumeResult(first=first, second=second, ledger=ledger)


async def run_legacy_resume_trace() -> ResumeResult:
    """Expose pinned-runtime legacy leaf resume behavior."""

    app_name = "legacy_resume"
    ledger: list[str] = []
    service = InMemorySessionService()
    await service.create_session(
        app_name=app_name,
        user_id=USER_ID,
        session_id=SESSION_ID,
    )
    first = await _run_with_service(
        root=build_legacy_approval_pipeline(ledger),
        app_name=app_name,
        service=service,
        message=text_message("prepare the brief"),
        resumable=True,
    )
    second = await _run_with_service(
        root=build_legacy_approval_pipeline(ledger),
        app_name=app_name,
        service=service,
        message=approval_message(approved=True),
        resumable=True,
    )
    return ResumeResult(first=first, second=second, ledger=ledger)


def summarize_event(event: Event) -> dict[str, Any]:
    """Extract stable workflow-relevant Event fields."""

    text = ""
    if event.content and event.content.parts:
        text = "".join(part.text or "" for part in event.content.parts)
    return {
        "author": event.author,
        "node_path": event.node_info.path,
        "branch": event.branch,
        "text": text,
        "output": event.output,
        "route": event.actions.route,
        "state_delta": event.actions.state_delta,
        "agent_state": event.actions.agent_state,
        "end_of_agent": event.actions.end_of_agent,
        "interrupt_ids": sorted(event.long_running_tool_ids or []),
        "error_code": event.error_code,
        "error_message": event.error_message,
    }


def summarize_run(result: RunResult) -> dict[str, Any]:
    return {
        "events": [summarize_event(event) for event in result.events],
        "stored_event_count": len(result.session.events),
        "state": result.session.state,
        "metrics": result.metrics,
        "error": (
            {
                "type": type(result.error).__name__,
                "message": str(result.error),
            }
            if result.error
            else None
        ),
    }


def summarize_resume(result: ResumeResult) -> dict[str, Any]:
    return {
        "first": summarize_run(result.first),
        "second": summarize_run(result.second),
        "ledger": result.ledger,
    }
