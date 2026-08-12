"""Deterministic ADK model for specialist execution experiments."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types
from pydantic import Field
from typing_extensions import override


class ScriptedModel(BaseLlm):
    """Yield fixed responses or raise fixed failures while retaining requests."""

    model: str = "scripted-multi-agent-model"
    responses: list[Any]
    requests: list[LlmRequest] = Field(default_factory=list)
    response_index: int = 0

    @override
    async def generate_content_async(
        self,
        llm_request: LlmRequest,
        stream: bool = False,
    ) -> AsyncGenerator[LlmResponse, None]:
        del stream
        self.requests.append(llm_request.model_copy(deep=True))
        if self.response_index >= len(self.responses):
            raise AssertionError(
                "ScriptedModel received more calls than configured "
                f"({len(self.responses)})."
            )

        response = self.responses[self.response_index]
        self.response_index += 1
        if isinstance(response, BaseException):
            raise response
        yield response


def function_call_response(
    name: str,
    arguments: dict[str, Any],
    *,
    call_id: str,
) -> LlmResponse:
    """Build one model function-call response with a stable call ID."""

    return LlmResponse(
        content=types.Content(
            role="model",
            parts=[
                types.Part(
                    function_call=types.FunctionCall(
                        id=call_id,
                        name=name,
                        args=arguments,
                    )
                )
            ],
        )
    )


def text_response(text: str) -> LlmResponse:
    """Build one model text response."""

    return LlmResponse(
        content=types.Content(
            role="model",
            parts=[types.Part.from_text(text=text)],
        )
    )
