"""ADK roots for the four specialist execution modes and breakages."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any
from typing import Literal

from google.adk.agents import LlmAgent
from google.adk.agents.context import Context
from google.adk.workflow import FunctionNode
from google.adk.workflow import START
from google.adk.workflow import Workflow
from google.genai import types
from pydantic import BaseModel

from .domain import case_payload
from .domain import decision_payload
from .domain import parse_case
from .domain import triage_case
from .scripted_model import function_call_response
from .scripted_model import ScriptedModel
from .scripted_model import text_response


class CaseInput(BaseModel):
    """Typed specialist input exposed in Agent tool declarations."""

    case_id: str
    amount_usd: int
    days_open: int
    chargeback_signal: bool
    customer_tier: Literal["standard", "priority"]


class DecisionOutput(BaseModel):
    """Typed specialist output enforced at the Agent boundary."""

    case_id: str
    risk_level: Literal["low", "medium", "high"]
    owner: Literal[
        "standard_support",
        "priority_support",
        "risk_operations",
    ]
    reasons: list[str]


class TriageState(BaseModel):
    """Declared shared state used only where an experiment needs it."""

    triage_result: dict[str, Any] | None = None


@dataclass
class Scenario:
    """One executable root and the concrete model instances it contains."""

    root: Any
    models: dict[str, ScriptedModel]


def _content_payload(value: Any) -> dict[str, Any]:
    if isinstance(value, types.Content):
        text = "".join(part.text or "" for part in value.parts or [])
    else:
        text = str(value)
    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise ValueError("case input must be a JSON object")
    return parsed


def _decision_text(payload: dict[str, Any] | None = None) -> str:
    return json.dumps(payload or decision_payload(), sort_keys=True)


def build_function_scenario() -> Scenario:
    """Run the capability as a deterministic Workflow function node."""

    def deterministic_triage(
        ctx: Context,
        node_input: Any,
    ) -> dict[str, Any]:
        case = parse_case(_content_payload(node_input))
        result = decision_payload(triage_case(case))
        ctx.state["triage_result"] = result
        return result

    workflow = Workflow(
        name="function_triage",
        state_schema=TriageState,
        edges=[
            (
                START,
                FunctionNode(
                    func=deterministic_triage,
                    name="deterministic_triage",
                ),
            )
        ],
    )
    return Scenario(root=workflow, models={})


def build_single_turn_scenario() -> Scenario:
    """Run the capability as one isolated LLM Workflow node."""

    model = ScriptedModel(responses=[text_response(_decision_text())])
    specialist = LlmAgent(
        name="single_turn_triage",
        description="Classify one support case and return a typed decision.",
        instruction="Classify exactly one supplied case.",
        model=model,
        mode="single_turn",
        input_schema=CaseInput,
        output_schema=DecisionOutput,
        output_key="triage_result",
    )
    workflow = Workflow(
        name="single_turn_triage_workflow",
        state_schema=TriageState,
        edges=[(START, specialist)],
    )
    cloned = next(
        node
        for node in workflow.graph.nodes
        if node.name == "single_turn_triage"
    )
    return Scenario(
        root=workflow,
        models={"single_turn_triage": cloned.model},
    )


def build_transfer_scenario(*, follow_up: bool) -> Scenario:
    """Transfer conversation ownership to a chat-mode specialist."""

    root_model = ScriptedModel(
        responses=[
            function_call_response(
                "transfer_to_agent",
                {"agent_name": "transfer_triage"},
                call_id="transfer-case-1",
            )
        ]
    )
    child_responses = [text_response(_decision_text())]
    if follow_up:
        child_responses.append(text_response(_decision_text()))
    child_model = ScriptedModel(responses=child_responses)
    specialist = LlmAgent(
        name="transfer_triage",
        description="Own the conversation for support case triage.",
        instruction="Classify the case and handle follow-up questions.",
        model=child_model,
        mode="chat",
        output_schema=DecisionOutput,
        output_key="triage_result",
    )
    coordinator = LlmAgent(
        name="transfer_coordinator",
        description="Route support conversations.",
        instruction="Transfer case-triage conversations to the specialist.",
        model=root_model,
        mode="chat",
        sub_agents=[specialist],
    )
    return Scenario(
        root=coordinator,
        models={
            "transfer_coordinator": root_model,
            "transfer_triage": child_model,
        },
    )


def _task_specialist(
    *,
    name: str,
    model: ScriptedModel,
    description: str = "Classify one support case and return a typed decision.",
    output_key: str = "triage_result",
) -> LlmAgent:
    return LlmAgent(
        name=name,
        description=description,
        instruction="Complete the delegated triage and call finish_task.",
        model=model,
        mode="task",
        disallow_transfer_to_parent=True,
        disallow_transfer_to_peers=True,
        input_schema=CaseInput,
        output_schema=DecisionOutput,
        output_key=output_key,
    )


def build_task_scenario() -> Scenario:
    """Let a chat coordinator select a task-mode specialist."""

    payload = case_payload()
    root_model = ScriptedModel(
        responses=[
            function_call_response(
                "task_triage",
                payload,
                call_id="delegate-case-1",
            ),
            text_response("CASE-100 was assigned to risk_operations."),
        ]
    )
    child_model = ScriptedModel(
        responses=[
            function_call_response(
                "finish_task",
                decision_payload(),
                call_id="finish-case-1",
            )
        ]
    )
    specialist = _task_specialist(
        name="task_triage",
        model=child_model,
    )
    coordinator = LlmAgent(
        name="task_coordinator",
        description="Coordinate bounded support tasks.",
        instruction="Delegate typed triage work, then report the result.",
        model=root_model,
        mode="chat",
        sub_agents=[specialist],
    )
    return Scenario(
        root=coordinator,
        models={
            "task_coordinator": root_model,
            "task_triage": child_model,
        },
    )


def build_task_validation_recovery_scenario() -> Scenario:
    """Make the task specialist violate then repair its output contract."""

    payload = case_payload()
    root_model = ScriptedModel(
        responses=[
            function_call_response(
                "recovering_triage",
                payload,
                call_id="delegate-recovery-1",
            ),
            text_response("Recovered specialist result accepted."),
        ]
    )
    child_model = ScriptedModel(
        responses=[
            function_call_response(
                "finish_task",
                {
                    "case_id": "CASE-100",
                    "risk_level": "severe",
                    "owner": "unknown_team",
                    "reasons": [],
                },
                call_id="finish-invalid-1",
            ),
            function_call_response(
                "finish_task",
                decision_payload(),
                call_id="finish-valid-2",
            ),
        ]
    )
    child = _task_specialist(
        name="recovering_triage",
        model=child_model,
    )
    root = LlmAgent(
        name="recovery_coordinator",
        model=root_model,
        mode="chat",
        sub_agents=[child],
    )
    return Scenario(
        root=root,
        models={
            "recovery_coordinator": root_model,
            "recovering_triage": child_model,
        },
    )


def build_task_hard_failure_scenario() -> Scenario:
    """Make the delegated specialist fail before producing task output."""

    root_model = ScriptedModel(
        responses=[
            function_call_response(
                "failing_triage",
                case_payload(),
                call_id="delegate-failure-1",
            ),
            text_response("This response must not be reached."),
        ]
    )
    child_model = ScriptedModel(
        responses=[RuntimeError("specialist model unavailable")]
    )
    child = _task_specialist(name="failing_triage", model=child_model)
    root = LlmAgent(
        name="failure_coordinator",
        model=root_model,
        mode="chat",
        sub_agents=[child],
    )
    return Scenario(
        root=root,
        models={
            "failure_coordinator": root_model,
            "failing_triage": child_model,
        },
    )


def build_overlap_scenario() -> Scenario:
    """Expose two indistinguishable specialists and script a wrong selection."""

    shared_description = (
        "Classify one support case and return a typed decision."
    )
    root_model = ScriptedModel(
        responses=[
            function_call_response(
                "overlap_triage_b",
                case_payload(),
                call_id="delegate-overlap-1",
            ),
            text_response("Selected overlap_triage_b."),
        ]
    )
    unused_model = ScriptedModel(responses=[])
    selected_payload = decision_payload()
    selected_payload["owner"] = "priority_support"
    selected_model = ScriptedModel(
        responses=[
            function_call_response(
                "finish_task",
                selected_payload,
                call_id="finish-overlap-1",
            )
        ]
    )
    first = _task_specialist(
        name="overlap_triage_a",
        model=unused_model,
        description=shared_description,
        output_key="overlap_a_result",
    )
    second = _task_specialist(
        name="overlap_triage_b",
        model=selected_model,
        description=shared_description,
        output_key="overlap_b_result",
    )
    root = LlmAgent(
        name="overlap_coordinator",
        model=root_model,
        mode="chat",
        sub_agents=[first, second],
    )
    return Scenario(
        root=root,
        models={
            "overlap_coordinator": root_model,
            "overlap_triage_a": unused_model,
            "overlap_triage_b": selected_model,
        },
    )


def build_shared_state_conflict_scenario() -> Scenario:
    """Let two specialists write different outputs to the same state key."""

    root_model = ScriptedModel(
        responses=[
            function_call_response(
                "conflict_triage_a",
                case_payload(),
                call_id="delegate-conflict-a",
            ),
            function_call_response(
                "conflict_triage_b",
                case_payload(),
                call_id="delegate-conflict-b",
            ),
            text_response("Both specialists completed."),
        ]
    )
    first_payload = decision_payload()
    second_payload = decision_payload()
    second_payload["owner"] = "priority_support"
    first_model = ScriptedModel(
        responses=[
            function_call_response(
                "finish_task",
                first_payload,
                call_id="finish-conflict-a",
            )
        ]
    )
    second_model = ScriptedModel(
        responses=[
            function_call_response(
                "finish_task",
                second_payload,
                call_id="finish-conflict-b",
            )
        ]
    )
    first = _task_specialist(
        name="conflict_triage_a",
        model=first_model,
        output_key="triage_result",
    )
    second = _task_specialist(
        name="conflict_triage_b",
        model=second_model,
        output_key="triage_result",
    )
    root = LlmAgent(
        name="conflict_coordinator",
        model=root_model,
        mode="chat",
        sub_agents=[first, second],
    )
    return Scenario(
        root=root,
        models={
            "conflict_coordinator": root_model,
            "conflict_triage_a": first_model,
            "conflict_triage_b": second_model,
        },
    )
