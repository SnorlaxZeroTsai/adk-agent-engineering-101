"""Normalize real traces from Labs 01-05 into the Phase 6 contract."""

from __future__ import annotations

import json
import logging
from pathlib import Path
import sys
from typing import Any
import warnings


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
for relative in (
    "labs/01-agent-basics",
    "labs/02-workflow-engineering",
    "labs/03-multi-agent",
    "labs/04-context-and-memory",
    "labs/05-rag-engineering",
):
    path = str(REPOSITORY_ROOT / relative)
    if path not in sys.path:
        sys.path.insert(0, path)

from agent_basics.runtime_trace import run_success_trace  # noqa: E402
from agent_basics.runtime_trace import run_tool_failure_trace  # noqa: E402
from context_memory_lab.runtime import request_text  # noqa: E402
from context_memory_lab.runtime import run_leaky_memory_trace  # noqa: E402
from context_memory_lab.runtime import run_memory_context  # noqa: E402
from multi_agent_lab.builders import build_task_scenario  # noqa: E402
from multi_agent_lab.runtime import run_scenario  # noqa: E402
from multi_agent_lab.runtime import run_shared_state_conflict  # noqa: E402
from rag_lab.domain import query_case  # noqa: E402
from rag_lab.runtime import run_explicit_vector  # noqa: E402
from workflow_lab.graph_pipeline import build_graph_pipeline  # noqa: E402
from workflow_lab.legacy_pipeline import build_legacy_pipeline  # noqa: E402
from workflow_lab.runtime import run_once  # noqa: E402

from .contracts import ObservedRun
from .contracts import RetrievalEvidence
from .contracts import ToolCall
from .contracts import TraceSet
from .dataset import DATASET_ID
from .dataset import RAG_QUESTION
from .metrics import SCRIPTED_RESPONSE_QUALITY


logging.getLogger("google_adk").setLevel(logging.CRITICAL)
warnings.filterwarnings(
    "ignore",
    message=r".*JSON_SCHEMA_FOR_FUNC_DECL.*",
)
warnings.filterwarnings(
    "ignore",
    message=r"\[EXPERIMENTAL\] feature AGENT_STATE.*",
)


def _event_kind(event: Any) -> str:
    if event.error_code or event.error_message:
        return "error"
    if event.get_function_calls():
        return "function_call"
    if event.get_function_responses():
        return "function_response"
    if event.content:
        for part in event.content.parts or []:
            if part.text:
                return "message"
    if event.output is not None:
        return "output"
    return "metadata"


def _tool_calls(events: list[Any]) -> tuple[ToolCall, ...]:
    return tuple(
        ToolCall(
            name=call.name or "",
            arguments=dict(call.args or {}),
        )
        for event in events
        for call in event.get_function_calls()
    )


def _final_text(events: list[Any]) -> str:
    for event in reversed(events):
        if event.author == "user":
            continue
        if not event.content:
            continue
        for part in reversed(event.content.parts or []):
            if part.text:
                return part.text
    return ""


def _error(error: Exception | None) -> tuple[str | None, str | None]:
    if error is None:
        return None, None
    return type(error).__name__, str(error)


def _judge_score(output_text: str) -> float:
    """Stand in for a surface-form judge without claiming live-model evidence."""

    return 5.0 if output_text.strip() else 1.0


async def _agent_observation(*, broken: bool) -> ObservedRun:
    if broken:
        result = await run_tool_failure_trace(recover=False)
    else:
        result = await run_success_trace()
    output = _final_text(result.events)
    error_type, error_message = _error(result.error)
    return ObservedRun(
        case_id="agent-tool-round-trip",
        phase="foundations",
        output_text=output,
        tool_calls=_tool_calls(result.events),
        trajectory=tuple(_event_kind(event) for event in result.events),
        state=dict(result.session.state),
        model_request_count=len(result.requests),
        error_type=error_type,
        error_message=error_message,
        judge_scores={SCRIPTED_RESPONSE_QUALITY: _judge_score(output)},
    )


def _workflow_stage(event: Any) -> str:
    if event.node_info.path:
        leaf = event.node_info.path.rsplit("/", 1)[-1]
        return f"stage:{leaf.split('@', 1)[0]}"
    return f"stage:{event.author}"


async def _workflow_observation(*, broken: bool) -> ObservedRun:
    if broken:
        root = build_legacy_pipeline(
            required_reviews=99,
            max_iterations=2,
            unsafe_finalize=True,
        )
        result = await run_once(
            root,
            app_name="evaluation_legacy_loop_limit",
        )
    else:
        root = build_graph_pipeline(
            required_reviews=99,
            max_reviews=2,
        )
        result = await run_once(
            root,
            app_name="evaluation_graph_loop_limit",
        )
    terminal = (
        result.session.state.get("rejection")
        or result.session.state.get("final")
        or {}
    )
    output = json.dumps(terminal, sort_keys=True)
    error_type, error_message = _error(result.error)
    return ObservedRun(
        case_id="workflow-explicit-exhaustion",
        phase="workflow",
        output_text=output,
        trajectory=tuple(_workflow_stage(event) for event in result.events),
        state=dict(result.session.state),
        model_request_count=0,
        error_type=error_type,
        error_message=error_message,
        judge_scores={SCRIPTED_RESPONSE_QUALITY: _judge_score(output)},
    )


async def _multi_agent_observation(*, broken: bool) -> ObservedRun:
    if broken:
        result = await run_shared_state_conflict()
    else:
        result = await run_scenario(
            build_task_scenario(),
            app_name="evaluation_task_specialist",
        )
    output = _final_text(result.events)
    error_type, error_message = _error(result.error)
    return ObservedRun(
        case_id="bounded-task-specialist",
        phase="multi-agent",
        output_text=output,
        tool_calls=_tool_calls(result.events),
        trajectory=tuple(_event_kind(event) for event in result.events),
        state=dict(result.session.state),
        model_request_count=result.model_request_count,
        error_type=error_type,
        error_message=error_message,
        judge_scores={SCRIPTED_RESPONSE_QUALITY: _judge_score(output)},
    )


async def _memory_observation(*, broken: bool) -> ObservedRun:
    if broken:
        result = await run_leaky_memory_trace()
    else:
        result = await run_memory_context()
    output = _final_text(result.events)
    model_input = "\n".join(
        request_text(request) for request in result.model.requests
    )
    violations = ()
    if result.session.user_id == "bob" and "ALICE-SECRET" in model_input:
        violations = ("cross_user_memory_exposure",)
    error_type, error_message = _error(result.error)
    return ObservedRun(
        case_id="memory-user-isolation",
        phase="context-memory",
        output_text=output,
        trajectory=tuple(_event_kind(event) for event in result.events),
        state=dict(result.session.state),
        model_input_text=model_input,
        model_request_count=result.model_request_count,
        error_type=error_type,
        error_message=error_message,
        policy_violations=violations,
        judge_scores={
            SCRIPTED_RESPONSE_QUALITY: _judge_score(output)
        },
    )


async def _rag_observation(*, broken: bool) -> ObservedRun:
    result = await run_explicit_vector(
        query_case("current-payload"),
        include_provenance=not broken,
    )
    evaluation = result.evaluation()
    error_type, error_message = _error(result.error)
    return ObservedRun(
        case_id="rag-source-grounding",
        phase="rag",
        output_text=result.answer,
        tool_calls=_tool_calls(result.events),
        trajectory=tuple(_event_kind(event) for event in result.events),
        state=dict(result.session.state),
        model_request_count=result.model_request_count,
        error_type=error_type,
        error_message=error_message,
        retrieval=RetrievalEvidence(
            retrieval_recall=evaluation.retrieval_recall,
            retrieval_precision=evaluation.retrieval_precision,
            citation_recall=evaluation.citation_recall,
            citation_precision=evaluation.citation_precision,
            access_violations=evaluation.access_violations,
            stale_hits=evaluation.stale_hits,
            deleted_hits=evaluation.deleted_hits,
            grounded=evaluation.grounded,
        ),
        judge_scores={
            SCRIPTED_RESPONSE_QUALITY: _judge_score(result.answer)
        },
    )


async def collect_trace_set(variant: str) -> TraceSet:
    """Run one baseline or deliberately broken cross-phase trace set."""

    if variant not in {"baseline", "broken"}:
        raise ValueError("variant must be 'baseline' or 'broken'")
    broken = variant == "broken"
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=r".*JSON_SCHEMA_FOR_FUNC_DECL.*",
        )
        observations = (
            await _agent_observation(broken=broken),
            await _workflow_observation(broken=broken),
            await _multi_agent_observation(broken=broken),
            await _memory_observation(broken=broken),
            await _rag_observation(broken=broken),
        )
    return TraceSet(
        trace_set_id=f"phase-6-{variant}-traces",
        dataset_id=DATASET_ID,
        variant=variant,
        observations=observations,
    )
