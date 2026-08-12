#!/usr/bin/env python3
"""Render deterministic policy and approval evidence as JSON."""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
import sys
import warnings


LAB_ROOT = Path(__file__).resolve().parents[1]
if str(LAB_ROOT) not in sys.path:
    sys.path.insert(0, str(LAB_ROOT))

from safety_hitl_lab.domain import build_approval  # noqa: E402
from safety_hitl_lab.domain import FIXED_NOW_EPOCH  # noqa: E402
from safety_hitl_lab.runtime import BoundaryRun  # noqa: E402
from safety_hitl_lab.runtime import ConfirmationRun  # noqa: E402
from safety_hitl_lab.runtime import run_confirmation_payment  # noqa: E402
from safety_hitl_lab.runtime import run_plugin_payment  # noqa: E402
from safety_hitl_lab.runtime import run_prompt_only_payment  # noqa: E402
from safety_hitl_lab.runtime import run_unsafe_model_output  # noqa: E402
from safety_hitl_lab.runtime import run_unsafe_tool_output  # noqa: E402
from safety_hitl_lab.runtime import run_unsafe_user_input  # noqa: E402
from safety_hitl_lab.runtime import run_workflow_approval  # noqa: E402
from safety_hitl_lab.runtime import summarize_event  # noqa: E402


logging.getLogger("google_adk").setLevel(logging.CRITICAL)
warnings.filterwarnings(
    "ignore",
    message=r".*JSON_SCHEMA_FOR_FUNC_DECL.*",
)
warnings.filterwarnings(
    "ignore",
    message=r".*TOOL_CONFIRMATION.*",
)


def _error(error: Exception | None) -> dict[str, str] | None:
    if error is None:
        return None
    return {"type": type(error).__name__, "message": str(error)}


def _ledger(result) -> dict[str, object]:
    return {
        "effect_count": result.ledger.effect_count,
        "attempt_count": result.ledger.attempt_count,
        "entries": {
            key: {
                "action_id": value.action_id,
                "request_hash": value.request_hash,
                "authorization_id": value.authorization_id,
            }
            for key, value in sorted(result.ledger.entries.items())
        },
    }


def _boundary(result: BoundaryRun) -> dict[str, object]:
    return {
        "events": [summarize_event(event) for event in result.events],
        "state": result.session.state,
        "model_request_count": result.model_request_count,
        "plugin_hooks": result.plugin.hook_log if result.plugin else [],
        "ledger": _ledger(result),
        "error": _error(result.error),
    }


def _confirmation(result: ConfirmationRun) -> dict[str, object]:
    return {
        "first": [
            summarize_event(event) for event in result.first_events
        ],
        "resumed": [
            summarize_event(event) for event in result.resumed_events
        ],
        "replay": [
            summarize_event(event) for event in result.replay_events
        ],
        "state": result.session.state,
        "model_request_count": result.model_request_count,
        "tool_invocation_count": result.tool_invocation_count,
        "ledger": _ledger(result),
        "error": _error(result.error),
    }


async def build_bundle() -> dict[str, object]:
    prompt_only = await run_prompt_only_payment()
    plugin_complete = await run_plugin_payment(enforce_before_tool=True)
    plugin_too_late = await run_plugin_payment(enforce_before_tool=False)
    unsafe_user = await run_unsafe_user_input()
    unsafe_tool = await run_unsafe_tool_output()
    unsafe_model = await run_unsafe_model_output()
    approved = await run_confirmation_payment()
    rejected = await run_confirmation_payment(confirmed=False)
    expired = await run_confirmation_payment(
        approval=build_approval(
            expires_at_epoch=FIXED_NOW_EPOCH - 1,
        )
    )
    unauthorized = await run_confirmation_payment(
        approval=build_approval(approver_id="contractor-4")
    )
    tampered = await run_confirmation_payment(
        approval=build_approval(digest="tampered")
    )
    replay = await run_confirmation_payment(replay=True)
    workflow = await run_workflow_approval()
    return {
        "boundary_enforcement": {
            "prompt_only": _boundary(prompt_only),
            "plugin_complete": _boundary(plugin_complete),
            "plugin_too_late": _boundary(plugin_too_late),
            "unsafe_user": _boundary(unsafe_user),
            "unsafe_tool_output": _boundary(unsafe_tool),
            "unsafe_model_output": _boundary(unsafe_model),
        },
        "tool_confirmation": {
            "approved": _confirmation(approved),
            "rejected": _confirmation(rejected),
            "expired": _confirmation(expired),
            "unauthorized": _confirmation(unauthorized),
            "tampered": _confirmation(tampered),
            "replay": _confirmation(replay),
        },
        "workflow_request_input": {
            "first": [
                summarize_event(event) for event in workflow.first_events
            ],
            "resumed": [
                summarize_event(event) for event in workflow.resumed_events
            ],
            "state": workflow.session.state,
            "ledger": _ledger(workflow),
            "error": _error(workflow.error),
        },
    }


def main() -> None:
    print(
        json.dumps(
            asyncio.run(build_bundle()),
            indent=2,
            sort_keys=True,
            default=str,
        )
    )


if __name__ == "__main__":
    main()
