"""ADK runtime comparison for provider-native and explicit RAG."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import replace
import json
from typing import Any

from google.adk.agents import LlmAgent
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.apps import App
from google.adk.events import Event
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.sessions import Session
from google.adk.tools import VertexAiSearchTool
from google.adk.tools.tool_context import ToolContext
from google.genai import types

from .domain import ATLAS_V1
from .domain import ATLAS_V2
from .domain import current_documents
from .domain import current_versions
from .domain import DELETED_PROMOTION
from .domain import deleted_doc_ids
from .domain import QueryCase
from .evaluation import CaseEvaluation
from .evaluation import evaluate_case
from .retrieval import ExplicitVectorIndex
from .retrieval import ManagedSearchSimulator
from .retrieval import RetrievalHit
from .scripted_models import ExplicitRetrievalModel
from .scripted_models import ManagedSearchModel


APP_NAME = "rag_engineering_lab"
USER_ID = "analyst"
DATA_STORE = (
    "projects/lab/locations/global/collections/lab/dataStores/northwind"
)


@dataclass
class RagRunResult:
    mode: str
    case: QueryCase
    events: list[Event]
    session: Session
    model: ManagedSearchModel | ExplicitRetrievalModel
    hits: list[RetrievalHit | dict[str, Any]]
    error: Exception | None = None

    @property
    def answer(self) -> str:
        for event in reversed(self.events):
            if event.content:
                for part in event.content.parts or []:
                    if part.text:
                        return part.text
        return ""

    @property
    def model_request_count(self) -> int:
        return len(self.model.requests)

    def evaluation(self) -> CaseEvaluation:
        return evaluate_case(
            case=self.case,
            hits=self.hits,
            answer=self.answer,
            current_versions=current_versions(),
            deleted_doc_ids=deleted_doc_ids(),
        )


class PrincipalFilteredSearchTool(VertexAiSearchTool):
    """Bind native search filtering to trusted Session state."""

    def _build_vertex_ai_search_config(
        self,
        readonly_context: ReadonlyContext,
    ) -> types.VertexAISearch:
        principal_role = readonly_context.state.get(
            "principal_role",
            "public",
        )
        if principal_role == "internal":
            filter_text = 'visibility IN ("public", "internal")'
        else:
            filter_text = 'visibility = "public"'
        return types.VertexAISearch(
            datastore=self.data_store_id,
            filter=filter_text,
            max_results=self.max_results,
        )


def _message(text: str) -> types.Content:
    return types.UserContent(text)


async def _run(
    *,
    agent: LlmAgent,
    case: QueryCase,
) -> tuple[list[Event], Session, Exception | None]:
    service = InMemorySessionService()
    await service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=case.case_id,
        state={"principal_role": case.principal_role},
    )
    runner = Runner(
        app=App(name=APP_NAME, root_agent=agent),
        session_service=service,
    )
    events: list[Event] = []
    error: Exception | None = None
    try:
        async for event in runner.run_async(
            user_id=USER_ID,
            session_id=case.case_id,
            new_message=_message(case.question),
            yield_user_message=False,
        ):
            events.append(event)
    except Exception as caught:
        error = caught
    session = await service.get_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=case.case_id,
    )
    await runner.close()
    if session is None:
        raise AssertionError("RAG session disappeared")
    return events, session, error


async def run_managed_search(
    case: QueryCase,
    *,
    backend: ManagedSearchSimulator | None = None,
    enforce_principal_filter: bool = True,
) -> RagRunResult:
    resolved_backend = backend or ManagedSearchSimulator()
    if backend is None:
        resolved_backend.sync(current_documents())
    model = ManagedSearchModel(backend=resolved_backend)
    if enforce_principal_filter:
        tool = PrincipalFilteredSearchTool(
            data_store_id=DATA_STORE,
            max_results=3,
        )
    else:
        tool = VertexAiSearchTool(
            data_store_id=DATA_STORE,
            max_results=3,
        )
    agent = LlmAgent(
        name="managed_search_agent",
        model=model,
        include_contents="none",
        instruction=(
            "Answer knowledge questions only from native search evidence and "
            "preserve source identity."
        ),
        tools=[tool],
    )
    events, session, error = await _run(agent=agent, case=case)
    hits = model.hit_batches[-1] if model.hit_batches else []
    return RagRunResult(
        mode="managed",
        case=case,
        events=events,
        session=session,
        model=model,
        hits=hits,
        error=error,
    )


def build_explicit_index() -> ExplicitVectorIndex:
    index = ExplicitVectorIndex()
    index.ingest(current_documents())
    return index


def build_stale_index() -> ExplicitVectorIndex:
    index = ExplicitVectorIndex()
    index.ingest(
        [replace(ATLAS_V1, active=True)],
        delete_missing=False,
    )
    index.ingest(
        [ATLAS_V2],
        replace_versions=False,
        delete_missing=False,
    )
    return index


def build_deletion_lag_index() -> ExplicitVectorIndex:
    index = ExplicitVectorIndex()
    active_promotion = replace(DELETED_PROMOTION, active=True)
    index.ingest(
        [*current_documents(), active_promotion],
    )
    index.ingest(
        current_documents(),
        delete_missing=False,
    )
    return index


async def run_explicit_vector(
    case: QueryCase,
    *,
    index: ExplicitVectorIndex | None = None,
    include_provenance: bool = True,
) -> RagRunResult:
    resolved_index = index or build_explicit_index()
    captured_hits: list[RetrievalHit] = []

    def retrieve_documents(
        query: str,
        tool_context: ToolContext,
    ) -> dict[str, object]:
        """Retrieve ACL-filtered chunks with stable source provenance.

        Args:
            query: The knowledge-base search query.

        Returns:
            Matching chunks with source ID, version, URI and score.
        """

        hits = resolved_index.search(
            query=query,
            principal_role=tool_context.state.get(
                "principal_role",
                "public",
            ),
            top_k=3,
        )
        captured_hits[:] = hits
        return {
            "hits": [
                hit.as_dict(include_provenance=include_provenance)
                for hit in hits
            ]
        }

    model = ExplicitRetrievalModel()
    agent = LlmAgent(
        name="explicit_vector_agent",
        model=model,
        include_contents="none",
        instruction=(
            "Call retrieve_documents for every knowledge question. Answer "
            "only from returned evidence and cite source IDs and versions."
        ),
        tools=[retrieve_documents],
    )
    events, session, error = await _run(agent=agent, case=case)
    if include_provenance:
        hits: list[RetrievalHit | dict[str, Any]] = list(captured_hits)
    else:
        hits = list(model.response_hits)
    return RagRunResult(
        mode="explicit",
        case=case,
        events=events,
        session=session,
        model=model,
        hits=hits,
        error=error,
    )


def _event_kind(event: Event) -> str:
    if event.error_code or event.error_message:
        return "error"
    if event.grounding_metadata:
        return "grounded_text"
    if not event.content:
        return "metadata"
    for part in event.content.parts or []:
        if part.function_call:
            return "function_call"
        if part.function_response:
            return "function_response"
        if part.text:
            return "text"
    return "content"


def _request_char_count(request) -> int:
    chunks: list[str] = []
    if request.config and request.config.system_instruction:
        chunks.append(str(request.config.system_instruction))
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
    return len("\n".join(chunks))


def _grounding_sources(result: RagRunResult) -> list[str]:
    sources: list[str] = []
    for event in result.events:
        metadata = event.grounding_metadata
        if not metadata:
            continue
        for chunk in metadata.grounding_chunks or []:
            if chunk.retrieved_context and chunk.retrieved_context.uri:
                sources.append(chunk.retrieved_context.uri)
    return sources


def summarize_result(result: RagRunResult) -> dict[str, object]:
    return {
        "mode": result.mode,
        "case_id": result.case.case_id,
        "principal_role": result.case.principal_role,
        "answer": result.answer,
        "hits": [
            hit.as_dict() if isinstance(hit, RetrievalHit) else hit
            for hit in result.hits
        ],
        "evaluation": result.evaluation().as_dict(),
        "model_request_count": result.model_request_count,
        "request_char_counts": [
            _request_char_count(request)
            for request in result.model.requests
        ],
        "yielded_event_kinds": [_event_kind(event) for event in result.events],
        "stored_event_count": len(result.session.events),
        "grounding_sources": _grounding_sources(result),
        "error": (
            {
                "type": type(result.error).__name__,
                "message": str(result.error),
            }
            if result.error
            else None
        ),
    }
