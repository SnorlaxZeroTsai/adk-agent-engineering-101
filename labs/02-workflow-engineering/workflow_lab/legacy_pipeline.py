"""Legacy Sequential/Parallel/Loop Agent implementations for Lab 02."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from typing import Literal
import warnings

from google.adk.agents import BaseAgent
from google.adk.agents import LoopAgent
from google.adk.agents import ParallelAgent
from google.adk.agents import SequentialAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.adk.events.event_actions import EventActions
from google.genai import types
from pydantic import ConfigDict
from pydantic import PrivateAttr

from .domain import collect_facts
from .domain import collect_risks
from .domain import compose_draft
from .domain import finalize_brief
from .domain import normalize_topic
from .domain import review_draft
from .domain import revise_draft
from .domain import unsafe_finalize_brief
from .graph_pipeline import APPROVAL_INTERRUPT_ID
from .graph_pipeline import TransientResearchError


Stage = Literal[
    "intake",
    "facts",
    "risks",
    "compose",
    "review",
    "checker",
    "revise",
    "finalize",
]


def _user_text(ctx: InvocationContext) -> str:
    content = ctx.user_content
    if not content:
        return ""
    return "".join(part.text or "" for part in content.parts or [])


class DeterministicStageAgent(BaseAgent):
    """Adapt one shared deterministic business step to the legacy Agent API."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    stage: Stage
    required_reviews: int = 2
    unsafe_finalize: bool = False

    async def _run_async_impl(
        self,
        ctx: InvocationContext,
    ) -> AsyncGenerator[Event, None]:
        state = ctx.session.state
        state_delta: dict[str, object] = {}
        escalate = False

        if self.stage == "intake":
            state_delta["topic"] = normalize_topic(_user_text(ctx))
        elif self.stage == "facts":
            await asyncio.sleep(0)
            state_delta["facts"] = collect_facts(state["topic"])
        elif self.stage == "risks":
            await asyncio.sleep(0)
            state_delta["risks"] = collect_risks(state["topic"])
        elif self.stage == "compose":
            state_delta["draft"] = compose_draft(
                state["topic"],
                state["facts"],
                state["risks"],
            )
        elif self.stage == "review":
            attempt = int(state.get("review_count", 0)) + 1
            result = review_draft(
                state["draft"],
                attempt,
                required_reviews=self.required_reviews,
            )
            state_delta.update(
                {
                    "review_count": attempt,
                    "review_score": result["score"],
                    "approved": result["approved"],
                }
            )
        elif self.stage == "checker":
            escalate = bool(state.get("approved"))
        elif self.stage == "revise":
            revision = int(state.get("revision_count", 0)) + 1
            state_delta.update(
                {
                    "revision_count": revision,
                    "draft": revise_draft(state["draft"], revision),
                }
            )
        elif self.stage == "finalize":
            finalizer = (
                unsafe_finalize_brief
                if self.unsafe_finalize
                else finalize_brief
            )
            state_delta["final"] = finalizer(
                state["topic"],
                state["draft"],
                approved=bool(state.get("approved")),
                review_count=int(state.get("review_count", 0)),
            )

        yield Event(
            author=self.name,
            branch=ctx.branch,
            content=types.Content(
                role="model",
                parts=[types.Part(text=self.stage)],
            ),
            actions=EventActions(
                state_delta=state_delta,
                escalate=escalate,
            ),
        )
        if ctx.is_resumable:
            ctx.set_agent_state(self.name, end_of_agent=True)
            yield self._create_agent_state_event(ctx)

    async def _run_live_impl(
        self,
        ctx: InvocationContext,
    ) -> AsyncGenerator[Event, None]:
        del ctx
        if False:
            yield


class LegacyFlakyAgent(BaseAgent):
    """Fail once to expose the absence of composite-level retry policy."""

    _tracker: dict[str, int] = PrivateAttr()

    def __init__(self, *, name: str, tracker: dict[str, int]):
        super().__init__(name=name)
        self._tracker = tracker

    async def _run_async_impl(
        self,
        ctx: InvocationContext,
    ) -> AsyncGenerator[Event, None]:
        del ctx
        self._tracker["attempts"] = self._tracker.get("attempts", 0) + 1
        raise TransientResearchError("temporary research backend failure")
        yield

    async def _run_live_impl(
        self,
        ctx: InvocationContext,
    ) -> AsyncGenerator[Event, None]:
        del ctx
        if False:
            yield


class LegacyPrepareAgent(BaseAgent):
    """Record one external effect before an approval pause."""

    _ledger: list[str] = PrivateAttr()

    def __init__(self, *, name: str, ledger: list[str]):
        super().__init__(name=name)
        self._ledger = ledger

    async def _run_async_impl(
        self,
        ctx: InvocationContext,
    ) -> AsyncGenerator[Event, None]:
        self._ledger.append("prepared")
        yield Event(
            author=self.name,
            branch=ctx.branch,
            content=types.Content(
                role="model",
                parts=[types.Part(text="prepared")],
            ),
            actions=EventActions(state_delta={"prepared": True}),
        )
        if ctx.is_resumable:
            ctx.set_agent_state(self.name, end_of_agent=True)
            yield self._create_agent_state_event(ctx)

    async def _run_live_impl(
        self,
        ctx: InvocationContext,
    ) -> AsyncGenerator[Event, None]:
        del ctx
        if False:
            yield


class LegacyApprovalAgent(BaseAgent):
    """Pause and resolve approval as a legacy leaf Agent."""

    def _resolved_response(
        self,
        ctx: InvocationContext,
    ) -> dict[str, object] | None:
        for event in reversed(ctx.session.events):
            for response in event.get_function_responses():
                if response.id == APPROVAL_INTERRUPT_ID:
                    return response.response
        return None

    async def _run_async_impl(
        self,
        ctx: InvocationContext,
    ) -> AsyncGenerator[Event, None]:
        response = self._resolved_response(ctx)
        if response is None:
            yield Event(
                author=self.name,
                branch=ctx.branch,
                content=types.Content(
                    role="model",
                    parts=[
                        types.Part(
                            function_call=types.FunctionCall(
                                name="approve_brief",
                                id=APPROVAL_INTERRUPT_ID,
                                args={},
                            )
                        )
                    ],
                ),
                long_running_tool_ids={APPROVAL_INTERRUPT_ID},
            )
            return

        yield Event(
            author=self.name,
            branch=ctx.branch,
            content=types.Content(
                role="model",
                parts=[types.Part(text="approval resolved")],
            ),
            actions=EventActions(
                state_delta={"approved": bool(response.get("approved"))}
            ),
        )
        if ctx.is_resumable:
            ctx.set_agent_state(self.name, end_of_agent=True)
            yield self._create_agent_state_event(ctx)

    async def _run_live_impl(
        self,
        ctx: InvocationContext,
    ) -> AsyncGenerator[Event, None]:
        del ctx
        if False:
            yield


class LegacyFinalizeApprovalAgent(BaseAgent):
    """Write the approval result if the composite parent reaches its tail."""

    async def _run_async_impl(
        self,
        ctx: InvocationContext,
    ) -> AsyncGenerator[Event, None]:
        result = {"finalized": bool(ctx.session.state.get("approved"))}
        yield Event(
            author=self.name,
            branch=ctx.branch,
            content=types.Content(
                role="model",
                parts=[types.Part(text="approval finalized")],
            ),
            actions=EventActions(state_delta={"final": result}),
        )
        if ctx.is_resumable:
            ctx.set_agent_state(self.name, end_of_agent=True)
            yield self._create_agent_state_event(ctx)

    async def _run_live_impl(
        self,
        ctx: InvocationContext,
    ) -> AsyncGenerator[Event, None]:
        del ctx
        if False:
            yield


def _deprecated_composites():
    warnings.filterwarnings(
        "ignore",
        message=".*deprecated in favor of Workflow.*",
    )
    warnings.filterwarnings(
        "ignore",
        message=r"\[EXPERIMENTAL\] feature AGENT_STATE.*",
    )


def build_legacy_pipeline(
    *,
    required_reviews: int = 2,
    max_iterations: int = 3,
    unsafe_finalize: bool = False,
) -> SequentialAgent:
    """Build a legacy composite with the same deterministic domain rules."""

    with warnings.catch_warnings():
        _deprecated_composites()
        quality_loop = LoopAgent(
            name="quality_loop",
            max_iterations=max_iterations,
            sub_agents=[
                DeterministicStageAgent(
                    name="review",
                    stage="review",
                    required_reviews=required_reviews,
                ),
                DeterministicStageAgent(
                    name="approval_checker",
                    stage="checker",
                ),
                DeterministicStageAgent(
                    name="revise",
                    stage="revise",
                ),
            ],
        )
        analysis = ParallelAgent(
            name="parallel_analysis",
            sub_agents=[
                DeterministicStageAgent(name="facts", stage="facts"),
                DeterministicStageAgent(name="risks", stage="risks"),
            ],
        )
        return SequentialAgent(
            name="legacy_research_pipeline",
            sub_agents=[
                DeterministicStageAgent(name="intake", stage="intake"),
                analysis,
                DeterministicStageAgent(name="compose", stage="compose"),
                quality_loop,
                DeterministicStageAgent(
                    name="finalize",
                    stage="finalize",
                    unsafe_finalize=unsafe_finalize,
                ),
            ],
        )


def build_legacy_failure_pipeline(
    tracker: dict[str, int],
) -> SequentialAgent:
    """Build a legacy sequence whose first child fails transiently."""

    with warnings.catch_warnings():
        _deprecated_composites()
        return SequentialAgent(
            name="legacy_failure_pipeline",
            sub_agents=[
                LegacyFlakyAgent(name="flaky_fetch", tracker=tracker),
                DeterministicStageAgent(name="finalize", stage="finalize"),
            ],
        )


def build_legacy_approval_pipeline(
    ledger: list[str],
) -> SequentialAgent:
    """Build a legacy pause/resume comparison."""

    with warnings.catch_warnings():
        _deprecated_composites()
        return SequentialAgent(
            name="legacy_approval_pipeline",
            sub_agents=[
                LegacyPrepareAgent(name="prepare", ledger=ledger),
                LegacyApprovalAgent(name="approval"),
                LegacyFinalizeApprovalAgent(name="finalize"),
            ],
        )
