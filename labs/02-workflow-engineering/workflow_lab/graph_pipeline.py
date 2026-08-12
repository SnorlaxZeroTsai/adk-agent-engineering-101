"""ADK 2.0 graph Workflow implementations for Lab 02."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from typing import Any

from google.adk.agents.context import Context
from google.adk.events import Event
from google.adk.workflow import BaseNode
from google.adk.workflow import FunctionNode
from google.adk.workflow import JoinNode
from google.adk.workflow import RetryConfig
from google.adk.workflow import START
from google.adk.workflow import Workflow
from google.genai import types
from pydantic import BaseModel

from .domain import collect_facts
from .domain import collect_risks
from .domain import compose_draft
from .domain import finalize_brief
from .domain import normalize_topic
from .domain import review_draft
from .domain import revise_draft


APPROVAL_INTERRUPT_ID = "approve-brief-1"


class BriefState(BaseModel):
    """Declared unprefixed state owned by the research workflow."""

    topic: str | None = None
    facts: list[str] | None = None
    risks: list[str] | None = None
    draft: str | None = None
    review_count: int | None = None
    review_score: float | None = None
    approved: bool | None = None
    revision_count: int | None = None
    final: dict[str, Any] | None = None
    rejection: dict[str, Any] | None = None
    prepared: bool | None = None


class TransientResearchError(RuntimeError):
    """Retryable infrastructure-style failure used by the experiment."""


class ApprovalNode(BaseNode):
    """Pause for one approval response and rerun with the resolved input."""

    rerun_on_resume: bool = True

    async def _run_impl(
        self,
        *,
        ctx: Context,
        node_input: Any,
    ) -> AsyncGenerator[Any, None]:
        response = ctx.resume_inputs.get(APPROVAL_INTERRUPT_ID)
        if response is not None:
            approved = bool(response.get("approved"))
            yield {"approved": approved, "prepared": node_input}
            return

        yield Event(
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


def _content_text(value: Any) -> str:
    if isinstance(value, types.Content):
        return "".join(part.text or "" for part in value.parts or [])
    return str(value)


def build_graph_pipeline(
    *,
    required_reviews: int = 2,
    max_reviews: int = 3,
) -> Workflow:
    """Build the graph equivalent of the legacy composite pipeline."""

    if max_reviews < 1:
        raise ValueError("max_reviews must be positive")

    def intake(ctx: Context, node_input: Any) -> dict[str, str]:
        topic = normalize_topic(_content_text(node_input))
        ctx.state["topic"] = topic
        return {"topic": topic}

    async def facts(ctx: Context, node_input: Any) -> dict[str, list[str]]:
        del node_input
        await asyncio.sleep(0)
        result = collect_facts(ctx.state["topic"])
        ctx.state["facts"] = result
        return {"facts": result}

    async def risks(ctx: Context, node_input: Any) -> dict[str, list[str]]:
        del node_input
        await asyncio.sleep(0)
        result = collect_risks(ctx.state["topic"])
        ctx.state["risks"] = result
        return {"risks": result}

    def compose(ctx: Context, node_input: Any) -> dict[str, str]:
        del node_input
        draft = compose_draft(
            ctx.state["topic"],
            ctx.state["facts"],
            ctx.state["risks"],
        )
        ctx.state["draft"] = draft
        return {"draft": draft}

    def review(ctx: Context, node_input: Any) -> Event:
        del node_input
        attempt = int(ctx.state.get("review_count", 0)) + 1
        result = review_draft(
            ctx.state["draft"],
            attempt,
            required_reviews=required_reviews,
        )
        ctx.state["review_count"] = attempt
        ctx.state["review_score"] = result["score"]
        ctx.state["approved"] = result["approved"]

        if result["approved"]:
            route = "approved"
        elif attempt >= max_reviews:
            route = "exhausted"
        else:
            route = "revise"
        return Event(output=result, route=route)

    def revise(ctx: Context, node_input: Any) -> dict[str, str]:
        del node_input
        revision = int(ctx.state.get("revision_count", 0)) + 1
        draft = revise_draft(ctx.state["draft"], revision)
        ctx.state["revision_count"] = revision
        ctx.state["draft"] = draft
        return {"draft": draft}

    def finalize(ctx: Context, node_input: Any) -> dict[str, Any]:
        del node_input
        result = finalize_brief(
            ctx.state["topic"],
            ctx.state["draft"],
            approved=bool(ctx.state["approved"]),
            review_count=int(ctx.state["review_count"]),
        )
        ctx.state["final"] = result
        return result

    def reject(ctx: Context, node_input: Any) -> dict[str, Any]:
        del node_input
        result = {
            "status": "rejected",
            "reason": "review_limit_exhausted",
            "review_count": int(ctx.state["review_count"]),
        }
        ctx.state["rejection"] = result
        return result

    intake_node = FunctionNode(func=intake, name="intake")
    facts_node = FunctionNode(func=facts, name="facts")
    risks_node = FunctionNode(func=risks, name="risks")
    join_node = JoinNode(name="analysis_join")
    compose_node = FunctionNode(func=compose, name="compose")
    review_node = FunctionNode(func=review, name="review")
    revise_node = FunctionNode(func=revise, name="revise")
    finalize_node = FunctionNode(func=finalize, name="finalize")
    reject_node = FunctionNode(func=reject, name="reject")

    return Workflow(
        name="graph_research_pipeline",
        state_schema=BriefState,
        edges=[
            (START, intake_node, (facts_node, risks_node)),
            (facts_node, join_node),
            (risks_node, join_node),
            (join_node, compose_node, review_node),
            (
                review_node,
                {
                    "revise": revise_node,
                    "approved": finalize_node,
                    "exhausted": reject_node,
                },
            ),
            (revise_node, review_node),
        ],
    )


def build_retry_workflow(tracker: dict[str, int]) -> Workflow:
    """Build a node-local retry experiment."""

    def flaky_fetch() -> dict[str, str]:
        tracker["attempts"] = tracker.get("attempts", 0) + 1
        if tracker["attempts"] == 1:
            raise TransientResearchError("temporary research backend failure")
        return {"status": "recovered"}

    flaky_node = FunctionNode(
        func=flaky_fetch,
        name="flaky_fetch",
        retry_config=RetryConfig(
            max_attempts=2,
            initial_delay=0,
            jitter=0,
            exceptions=[TransientResearchError],
        ),
    )
    return Workflow(
        name="graph_retry_pipeline",
        edges=[(START, flaky_node)],
    )


def build_missing_state_workflow() -> Workflow:
    """Build an intentional runtime missing-state failure."""

    def consume_draft(draft: str) -> str:
        return draft.upper()

    return Workflow(
        name="missing_state_pipeline",
        state_schema=BriefState,
        edges=[
            (
                START,
                FunctionNode(func=consume_draft, name="consume_draft"),
            )
        ],
    )


def build_duplicate_output_workflow(*, delegate_output: bool) -> Workflow:
    """Build a dynamic-node output experiment."""

    def child_output() -> str:
        return "shared-output"

    async def parent(ctx: Context) -> str:
        return await ctx.run_node(
            child_output,
            use_as_output=delegate_output,
        )

    parent_node = FunctionNode(
        func=parent,
        name="parent",
        rerun_on_resume=True,
    )
    return Workflow(
        name=(
            "delegated_output_pipeline"
            if delegate_output
            else "duplicate_output_pipeline"
        ),
        edges=[(START, parent_node)],
    )


def build_graph_approval_workflow(ledger: list[str]) -> Workflow:
    """Build a resumable workflow with one externally visible side effect."""

    def prepare(ctx: Context, node_input: Any) -> dict[str, bool]:
        del node_input
        ledger.append("prepared")
        ctx.state["prepared"] = True
        return {"prepared": True}

    def finalize(ctx: Context, node_input: Any) -> dict[str, bool]:
        approved = bool(node_input["approved"])
        result = {"finalized": approved}
        ctx.state["final"] = result
        return result

    return Workflow(
        name="graph_approval_pipeline",
        state_schema=BriefState,
        edges=[
            (
                START,
                FunctionNode(func=prepare, name="prepare"),
                ApprovalNode(name="approval"),
                FunctionNode(func=finalize, name="finalize_approval"),
            )
        ],
    )
