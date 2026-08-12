"""Deterministic provider-native and FunctionTool RAG models."""

from __future__ import annotations

from collections.abc import AsyncGenerator
import json
from typing import Any

from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types
from pydantic import Field
from typing_extensions import override

from .evaluation import compose_grounded_answer
from .retrieval import ManagedSearchSimulator
from .retrieval import RetrievalHit


def _request_question(request: LlmRequest) -> str:
    texts: list[str] = []
    for content in request.contents or []:
        for part in content.parts or []:
            if part.text:
                texts.append(part.text)
    if not texts:
        raise AssertionError("RAG model request has no user question")
    return texts[-1]


def _function_response(request: LlmRequest) -> dict[str, Any] | None:
    for content in reversed(request.contents or []):
        for part in reversed(content.parts or []):
            response = part.function_response
            if response and response.name == "retrieve_documents":
                payload = response.response
                if isinstance(payload, dict):
                    return payload
                return json.loads(str(payload))
    return None


def _usage(
    request: LlmRequest,
    output: str,
) -> types.GenerateContentResponseUsageMetadata:
    prompt_chars = sum(
        len(part.text or "")
        for content in request.contents or []
        for part in content.parts or []
    )
    prompt_units = max(1, prompt_chars // 4)
    output_units = max(1, len(output) // 4)
    return types.GenerateContentResponseUsageMetadata(
        prompt_token_count=prompt_units,
        candidates_token_count=output_units,
        total_token_count=prompt_units + output_units,
    )


def _grounding_metadata(
    *,
    query: str,
    hits: list[RetrievalHit],
) -> types.GroundingMetadata:
    return types.GroundingMetadata(
        retrieval_queries=[query],
        grounding_chunks=[
            types.GroundingChunk(
                retrieved_context=types.GroundingChunkRetrievedContext(
                    uri=hit.uri,
                    title=f"{hit.doc_id}@v{hit.version}",
                    text=hit.text,
                )
            )
            for hit in hits
        ],
    )


class ManagedSearchModel(BaseLlm):
    """Simulate provider-side retrieval from native Vertex AI Search config."""

    model: str = "gemini-2.5-flash"
    backend: Any
    requests: list[LlmRequest] = Field(default_factory=list)
    hit_batches: list[list[Any]] = Field(default_factory=list)

    @override
    async def generate_content_async(
        self,
        llm_request: LlmRequest,
        stream: bool = False,
    ) -> AsyncGenerator[LlmResponse, None]:
        del stream
        self.requests.append(llm_request.model_copy(deep=True))
        question = _request_question(llm_request)
        search_config = None
        for tool in (llm_request.config.tools if llm_request.config else []) or []:
            if (
                tool.retrieval
                and tool.retrieval.vertex_ai_search is not None
            ):
                search_config = tool.retrieval.vertex_ai_search
                break
        if search_config is None:
            raise AssertionError("native search config was not added to request")

        filter_text = search_config.filter or ""
        if "internal" in filter_text:
            principal_role = "internal"
            enforce_acl = True
        elif "public" in filter_text:
            principal_role = "public"
            enforce_acl = True
        else:
            principal_role = "internal"
            enforce_acl = False

        hits = self.backend.search(
            query=question,
            principal_role=principal_role,
            top_k=search_config.max_results or 3,
            enforce_acl=enforce_acl,
        )
        self.hit_batches.append(hits)
        answer = compose_grounded_answer(
            question,
            [hit.as_dict() for hit in hits],
        )
        yield LlmResponse(
            content=types.ModelContent(answer.text),
            grounding_metadata=_grounding_metadata(
                query=question,
                hits=hits,
            ),
            usage_metadata=_usage(llm_request, answer.text),
        )


class ExplicitRetrievalModel(BaseLlm):
    """Call retrieval as a FunctionTool, then answer from its response."""

    model: str = "scripted-explicit-rag"
    requests: list[LlmRequest] = Field(default_factory=list)
    response_hits: list[dict[str, Any]] = Field(default_factory=list)

    @override
    async def generate_content_async(
        self,
        llm_request: LlmRequest,
        stream: bool = False,
    ) -> AsyncGenerator[LlmResponse, None]:
        del stream
        self.requests.append(llm_request.model_copy(deep=True))
        question = _request_question(llm_request)
        response = _function_response(llm_request)
        if response is None:
            marker = "retrieve_documents"
            yield LlmResponse(
                content=types.Content(
                    role="model",
                    parts=[
                        types.Part(
                            function_call=types.FunctionCall(
                                id="retrieve-1",
                                name=marker,
                                args={"query": question},
                            )
                        )
                    ],
                ),
                usage_metadata=_usage(llm_request, marker),
            )
            return

        hits = response.get("hits", [])
        if not isinstance(hits, list):
            raise AssertionError("retrieval response hits must be a list")
        self.response_hits = [
            dict(hit)
            for hit in hits
            if isinstance(hit, dict)
        ]
        answer = compose_grounded_answer(question, self.response_hits)
        yield LlmResponse(
            content=types.ModelContent(answer.text),
            usage_metadata=_usage(llm_request, answer.text),
        )
