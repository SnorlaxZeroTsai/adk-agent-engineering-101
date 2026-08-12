"""Executable data-placement and lifecycle experiments."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
import json
from typing import Any

from google.adk.agents import LlmAgent
from google.adk.agents.run_config import RunConfig
from google.adk.apps import App
from google.adk.artifacts import InMemoryArtifactService
from google.adk.events import Event
from google.adk.events.event_actions import EventActions
from google.adk.memory import InMemoryMemoryService
from google.adk.memory.base_memory_service import SearchMemoryResponse
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.sessions import Session
from google.adk.sessions.state import State
from google.adk.tools.preload_memory_tool import preload_memory_tool
from google.adk.tools.tool_context import ToolContext
from google.genai import types

from .domain import EXPECTED_ANSWER
from .domain import large_dossier_text
from .domain import render_dossier
from .scripted_model import function_call_response
from .scripted_model import ScriptedModel
from .scripted_model import text_response


APP_NAME = "context_memory_lab"
USER_ID = "alice"
OTHER_USER_ID = "bob"
SESSION_ID = "current"
USER_ARTIFACT = "user:support-dossier.txt"
QUESTION = "Which contact channel and previous router fix should I use?"
FIXED_TIMESTAMP = 1_786_500_000.0


@dataclass
class PlacementResult:
    """One Agent run plus the services that own its data."""

    events: list[Event]
    session: Session
    model: ScriptedModel
    session_service: InMemorySessionService
    artifact_service: InMemoryArtifactService | None = None
    memory_service: InMemoryMemoryService | None = None
    error: Exception | None = None
    metrics: dict[str, Any] = field(default_factory=dict)

    @property
    def model_request_count(self) -> int:
        return len(self.model.requests)


@dataclass
class StateScopeResult:
    """Materialized views of one state delta across lifecycle scopes."""

    invocation_state: dict[str, Any]
    same_session: dict[str, Any]
    same_user_new_session: dict[str, Any]
    other_user_new_session: dict[str, Any]
    persisted_event_delta: dict[str, Any]


@dataclass
class ArtifactScopeResult:
    """Artifact versions, visibility and deletion observations."""

    session_versions: list[int]
    latest_session_text: str | None
    old_session_text: str | None
    same_user_other_session_text: str | None
    user_scoped_other_session_text: str | None
    other_user_text: str | None
    versions_after_delete: list[int]


@dataclass
class MemoryLifecycleResult:
    """Memory isolation, retention and TTL observations."""

    same_user_matches: list[str]
    other_user_matches: list[str]
    after_session_delete_matches: list[str]
    ttl_zero_matches: list[str]


def _message(text: str) -> types.Content:
    return types.Content(
        role="user",
        parts=[types.Part.from_text(text=text)],
    )


async def _get_session(
    service: InMemorySessionService,
    *,
    user_id: str = USER_ID,
    session_id: str = SESSION_ID,
) -> Session:
    session = await service.get_session(
        app_name=APP_NAME,
        user_id=user_id,
        session_id=session_id,
    )
    if session is None:
        raise AssertionError("Lab 04 session disappeared")
    return session


async def _run_agent(
    *,
    agent: LlmAgent,
    session_service: InMemorySessionService,
    user_id: str = USER_ID,
    session_id: str = SESSION_ID,
    artifact_service: InMemoryArtifactService | None = None,
    memory_service: InMemoryMemoryService | None = None,
    message: str = QUESTION,
    run_config: RunConfig | None = None,
) -> PlacementResult:
    runner = Runner(
        app=App(name=APP_NAME, root_agent=agent),
        session_service=session_service,
        artifact_service=artifact_service,
        memory_service=memory_service,
    )
    events: list[Event] = []
    error: Exception | None = None
    try:
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=_message(message),
            run_config=run_config,
            yield_user_message=False,
        ):
            events.append(event)
    except Exception as caught:
        error = caught
    session = await _get_session(
        session_service,
        user_id=user_id,
        session_id=session_id,
    )
    await runner.close()
    return PlacementResult(
        events=events,
        session=session,
        model=agent.model,
        session_service=session_service,
        artifact_service=artifact_service,
        memory_service=memory_service,
        error=error,
    )


async def run_transient_context(
    *,
    context_text: str | None = None,
    responses: list[str] | None = None,
    messages: list[str] | None = None,
) -> PlacementResult:
    """Provide context for each invocation without persisting it."""

    service = InMemorySessionService()
    await service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
    )
    model = ScriptedModel(
        responses=[
            text_response(text)
            for text in (responses or [EXPECTED_ANSWER])
        ]
    )
    agent = LlmAgent(
        name="transient_context_agent",
        model=model,
        include_contents="none",
    )
    result: PlacementResult | None = None
    supplied_context = context_text or render_dossier()
    for message in messages or [QUESTION]:
        result = await _run_agent(
            agent=agent,
            session_service=service,
            message=message,
            run_config=RunConfig(
                model_input_context=[
                    types.UserContent(supplied_context),
                ]
            ),
        )
    if result is None:
        raise AssertionError("transient context experiment did not run")
    return result


async def run_state_context(*, stale_second_turn: bool = False) -> PlacementResult:
    """Inject persistent Session state into a dynamic instruction."""

    service = InMemorySessionService()
    await service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
        state={"support_context": render_dossier()},
    )
    responses = [text_response(EXPECTED_ANSWER)]
    if stale_second_turn:
        responses.append(text_response(EXPECTED_ANSWER))
    model = ScriptedModel(responses=responses)
    agent = LlmAgent(
        name="state_context_agent",
        model=model,
        include_contents="none",
        instruction="Use this support context: {support_context}",
    )
    first = await _run_agent(
        agent=agent,
        session_service=service,
    )
    if not stale_second_turn:
        return first
    return await _run_agent(
        agent=agent,
        session_service=service,
        message=(
            "The customer changed their preferred channel to email. "
            "Which channel should I use now?"
        ),
    )


async def load_support_dossier(
    tool_context: ToolContext,
) -> dict[str, str | None]:
    """Load the current user's support dossier artifact."""

    artifact = await tool_context.load_artifact(USER_ARTIFACT)
    return {
        "dossier": artifact.text if artifact and artifact.text else None,
    }


async def run_artifact_context(
    *,
    artifact_text: str | None = None,
    unrelated_second_turn: bool = False,
) -> PlacementResult:
    """Load versioned user-scoped context only when the model requests it."""

    session_service = InMemorySessionService()
    await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
    )
    artifact_service = InMemoryArtifactService()
    await artifact_service.save_artifact(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
        filename=USER_ARTIFACT,
        artifact=types.Part.from_text(text="obsolete dossier"),
        custom_metadata={"source": "lab", "status": "obsolete"},
    )
    await artifact_service.save_artifact(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
        filename=USER_ARTIFACT,
        artifact=types.Part.from_text(
            text=artifact_text or render_dossier()
        ),
        custom_metadata={"source": "lab", "status": "current"},
    )
    responses = [
        function_call_response(
            "load_support_dossier",
            {},
            call_id="load-dossier-1",
        ),
        text_response(EXPECTED_ANSWER),
    ]
    if unrelated_second_turn:
        responses.append(text_response("Hello."))
    model = ScriptedModel(responses=responses)
    agent = LlmAgent(
        name="artifact_context_agent",
        model=model,
        include_contents="none",
        tools=[load_support_dossier],
    )
    first = await _run_agent(
        agent=agent,
        session_service=session_service,
        artifact_service=artifact_service,
    )
    if not unrelated_second_turn:
        return first
    return await _run_agent(
        agent=agent,
        session_service=session_service,
        artifact_service=artifact_service,
        message="Say hello without loading the dossier.",
    )


def _memory_event(
    text: str,
    *,
    event_id: str,
    author: str = "user",
) -> Event:
    return Event(
        id=event_id,
        invocation_id=f"inv-{event_id}",
        author=author,
        content=_message(text),
        timestamp=FIXED_TIMESTAMP,
    )


async def _seed_memory(
    memory_service: InMemoryMemoryService,
    *,
    user_id: str,
    text: str,
    session_id: str,
) -> Session:
    session = Session(
        app_name=APP_NAME,
        user_id=user_id,
        id=session_id,
        events=[_memory_event(text, event_id=f"memory-{session_id}")],
    )
    await memory_service.add_session_to_memory(session)
    return session


async def run_memory_context(
    *,
    memory_service: InMemoryMemoryService | None = None,
    user_id: str = USER_ID,
) -> PlacementResult:
    """Recall an explicitly ingested prior Session into a new Session."""

    service = InMemorySessionService()
    await service.create_session(
        app_name=APP_NAME,
        user_id=user_id,
        session_id=SESSION_ID,
    )
    resolved_memory = memory_service or InMemoryMemoryService()
    if memory_service is None:
        await _seed_memory(
            resolved_memory,
            user_id=USER_ID,
            text=render_dossier(),
            session_id="prior",
        )
    model = ScriptedModel(responses=[text_response(EXPECTED_ANSWER)])
    agent = LlmAgent(
        name="memory_context_agent",
        model=model,
        include_contents="none",
        tools=[preload_memory_tool],
    )
    return await _run_agent(
        agent=agent,
        session_service=service,
        memory_service=resolved_memory,
        user_id=user_id,
    )


async def run_baseline_comparison() -> dict[str, PlacementResult]:
    return {
        "transient": await run_transient_context(),
        "state": await run_state_context(),
        "artifact": await run_artifact_context(),
        "memory": await run_memory_context(),
    }


async def run_large_context_comparison() -> dict[str, PlacementResult]:
    large = large_dossier_text()
    transient = await run_transient_context(
        context_text=large,
        responses=[EXPECTED_ANSWER, "Hello."],
        messages=[QUESTION, "Say hello."],
    )
    artifact = await run_artifact_context(
        artifact_text=large,
        unrelated_second_turn=True,
    )
    transient.metrics["payload_length"] = len(large)
    artifact.metrics["payload_length"] = len(large)
    return {"transient": transient, "artifact": artifact}


async def run_state_scope_trace() -> StateScopeResult:
    service = InMemorySessionService()
    first = await service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id="scope-one",
    )
    event = Event(
        author="state_writer",
        actions=EventActions(
            state_delta={
                "case_status": "open",
                "user:channel": "SMS",
                "app:policy_version": "2026-08",
                "temp:scratch": "invocation-only",
            }
        ),
    )
    await service.append_event(first, event)
    same_session = await _get_session(
        service,
        session_id="scope-one",
    )
    same_user_new = await service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id="scope-two",
    )
    other_user_new = await service.create_session(
        app_name=APP_NAME,
        user_id=OTHER_USER_ID,
        session_id="scope-three",
    )
    return StateScopeResult(
        invocation_state=dict(first.state),
        same_session=dict(same_session.state),
        same_user_new_session=dict(same_user_new.state),
        other_user_new_session=dict(other_user_new.state),
        persisted_event_delta=dict(event.actions.state_delta),
    )


def _part_text(part: types.Part | None) -> str | None:
    return part.text if part and part.text else None


async def run_artifact_scope_trace() -> ArtifactScopeResult:
    service = InMemoryArtifactService()
    session_file = "session-dossier.txt"
    await service.save_artifact(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id="artifact-one",
        filename=session_file,
        artifact=types.Part.from_text(text="session version zero"),
    )
    await service.save_artifact(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id="artifact-one",
        filename=session_file,
        artifact=types.Part.from_text(text="session version one"),
    )
    await service.save_artifact(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id="artifact-one",
        filename=USER_ARTIFACT,
        artifact=types.Part.from_text(text=render_dossier()),
    )
    versions = await service.list_versions(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id="artifact-one",
        filename=session_file,
    )
    latest = await service.load_artifact(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id="artifact-one",
        filename=session_file,
    )
    old = await service.load_artifact(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id="artifact-one",
        filename=session_file,
        version=0,
    )
    wrong_session = await service.load_artifact(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id="artifact-two",
        filename=session_file,
    )
    user_visible = await service.load_artifact(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id="artifact-two",
        filename=USER_ARTIFACT,
    )
    other_user = await service.load_artifact(
        app_name=APP_NAME,
        user_id=OTHER_USER_ID,
        session_id="artifact-other-user",
        filename=USER_ARTIFACT,
    )
    await service.delete_artifact(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id="artifact-one",
        filename=session_file,
    )
    versions_after_delete = await service.list_versions(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id="artifact-one",
        filename=session_file,
    )
    return ArtifactScopeResult(
        session_versions=versions,
        latest_session_text=_part_text(latest),
        old_session_text=_part_text(old),
        same_user_other_session_text=_part_text(wrong_session),
        user_scoped_other_session_text=_part_text(user_visible),
        other_user_text=_part_text(other_user),
        versions_after_delete=versions_after_delete,
    )


def _memory_texts(response: SearchMemoryResponse) -> list[str]:
    return [
        " ".join(
            part.text
            for part in memory.content.parts or []
            if part.text
        )
        for memory in response.memories
    ]


async def run_memory_lifecycle_trace() -> MemoryLifecycleResult:
    session_service = InMemorySessionService()
    source = await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id="memory-source",
    )
    await session_service.append_event(
        source,
        _memory_event(
            render_dossier(),
            event_id="memory-source-event",
        ),
    )
    memory = InMemoryMemoryService()
    stored_source = await _get_session(
        session_service,
        session_id="memory-source",
    )
    await memory.add_session_to_memory(stored_source)
    same_user = await memory.search_memory(
        app_name=APP_NAME,
        user_id=USER_ID,
        query="contact router",
    )
    other_user = await memory.search_memory(
        app_name=APP_NAME,
        user_id=OTHER_USER_ID,
        query="contact router",
    )
    await session_service.delete_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id="memory-source",
    )
    after_delete = await memory.search_memory(
        app_name=APP_NAME,
        user_id=USER_ID,
        query="contact router",
    )
    ttl_event = _memory_event(
        "Temporary channel is fax.",
        event_id="ttl-zero",
    )
    await memory.add_events_to_memory(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id="ttl-source",
        events=[ttl_event],
        custom_metadata={"ttl": "0s"},
    )
    ttl_zero = await memory.search_memory(
        app_name=APP_NAME,
        user_id=USER_ID,
        query="temporary fax",
    )
    return MemoryLifecycleResult(
        same_user_matches=_memory_texts(same_user),
        other_user_matches=_memory_texts(other_user),
        after_session_delete_matches=_memory_texts(after_delete),
        ttl_zero_matches=_memory_texts(ttl_zero),
    )


class LeakyMemoryService(InMemoryMemoryService):
    """Intentional boundary violation that ignores the requesting user."""

    async def search_memory(
        self,
        *,
        app_name: str,
        user_id: str,
        query: str,
    ) -> SearchMemoryResponse:
        del user_id
        return await super().search_memory(
            app_name=app_name,
            user_id=USER_ID,
            query=query,
        )


async def run_leaky_memory_trace() -> PlacementResult:
    memory = LeakyMemoryService()
    await _seed_memory(
        memory,
        user_id=USER_ID,
        text=(
            render_dossier()
            + " Private note: Alice account recovery code is ALICE-SECRET."
        ),
        session_id="alice-private",
    )
    return await run_memory_context(
        memory_service=memory,
        user_id=OTHER_USER_ID,
    )


def request_text(request) -> str:
    """Flatten model-visible text and structured tool responses."""

    chunks: list[str] = []
    system_instruction = request.config.system_instruction
    if system_instruction:
        chunks.append(str(system_instruction))
    for content in request.contents or []:
        for part in content.parts or []:
            if part.text:
                chunks.append(part.text)
            if part.function_response:
                chunks.append(
                    json.dumps(
                        part.function_response.response,
                        sort_keys=True,
                    )
                )
    return "\n".join(chunks)


def _event_text(event: Event) -> str:
    if not event.content:
        return ""
    chunks: list[str] = []
    for part in event.content.parts or []:
        if part.text:
            chunks.append(part.text)
        if part.function_response:
            chunks.append(
                json.dumps(
                    part.function_response.response,
                    sort_keys=True,
                )
            )
    return "\n".join(chunks)


def summarize_result(result: PlacementResult) -> dict[str, Any]:
    return {
        "model_request_count": result.model_request_count,
        "request_char_counts": [
            len(request_text(request)) for request in result.model.requests
        ],
        "request_contains_dossier": [
            "Preferred contact channel: SMS" in request_text(request)
            for request in result.model.requests
        ],
        "stored_event_count": len(result.session.events),
        "stored_state": result.session.state,
        "event_text": [_event_text(event) for event in result.session.events],
        "error": (
            {
                "type": type(result.error).__name__,
                "message": str(result.error),
            }
            if result.error
            else None
        ),
        "metrics": result.metrics,
    }
