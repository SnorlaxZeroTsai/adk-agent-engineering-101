"""Deterministic global policy plugin used by Lab 07."""

from __future__ import annotations

from typing import Any

from google.adk.agents.invocation_context import InvocationContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.adk.plugins import BasePlugin
from google.adk.plugins.base_plugin import CallbackContext
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext
from google.genai import types


BLOCKED_USER_MESSAGE = "Request blocked before model execution."
BLOCKED_TOOL_INPUT = "Payment blocked before side-effect execution."
REDACTED_TOOL_OUTPUT = "Tool output removed by policy."
REDACTED_MODEL_OUTPUT = "Model output removed by policy."


class BoundaryPolicyPlugin(BasePlugin):
    """Cover user/model and tool input/output with deterministic rules."""

    def __init__(
        self,
        *,
        enforce_tool_input: bool = True,
        mask_payment_after_execution: bool = False,
    ) -> None:
        super().__init__(name="boundary_policy")
        self.enforce_tool_input = enforce_tool_input
        self.mask_payment_after_execution = mask_payment_after_execution
        self.hook_log: list[str] = []

    async def on_user_message_callback(
        self,
        invocation_context: InvocationContext,
        user_message: types.Content,
    ) -> types.Content | None:
        self.hook_log.append("on_user_message")
        text = "".join(
            part.text or "" for part in user_message.parts or []
        )
        if "IGNORE POLICY" in text:
            invocation_context.session.state["_block_current_run"] = True
            return types.UserContent("[removed unsafe user input]")
        return None

    async def before_run_callback(
        self,
        invocation_context: InvocationContext,
    ) -> types.Content | None:
        self.hook_log.append("before_run")
        if invocation_context.session.state.get("_block_current_run", False):
            return types.ModelContent(BLOCKED_USER_MESSAGE)
        return None

    async def after_run_callback(
        self,
        invocation_context: InvocationContext,
    ) -> None:
        self.hook_log.append("after_run")
        invocation_context.session.state.pop("_block_current_run", None)

    async def before_tool_callback(
        self,
        tool: BaseTool,
        tool_args: dict[str, Any],
        tool_context: ToolContext,
    ) -> dict[str, Any] | None:
        del tool_context
        self.hook_log.append(f"before_tool:{tool.name}")
        if (
            self.enforce_tool_input
            and tool.name == "execute_vendor_payment"
            and int(tool_args.get("amount_usd", 0)) >= 1000
        ):
            return {
                "ok": False,
                "error": "approval_required",
                "message": BLOCKED_TOOL_INPUT,
            }
        return None

    async def before_model_callback(
        self,
        callback_context: CallbackContext,
        llm_request: LlmRequest,
    ) -> LlmResponse | None:
        del llm_request
        self.hook_log.append("before_model")
        if callback_context.state.get("_block_current_run", False):
            return LlmResponse(
                content=types.ModelContent(BLOCKED_USER_MESSAGE)
            )
        return None

    async def after_tool_callback(
        self,
        tool: BaseTool,
        tool_args: dict[str, Any],
        tool_context: ToolContext,
        result: dict[str, Any],
    ) -> dict[str, Any] | None:
        del tool_args, tool_context
        self.hook_log.append(f"after_tool:{tool.name}")
        if "RAW-SECRET" in str(result):
            return {
                "ok": False,
                "error": "unsafe_tool_output",
                "message": REDACTED_TOOL_OUTPUT,
            }
        if (
            self.mask_payment_after_execution
            and tool.name == "execute_vendor_payment"
        ):
            return {
                "ok": False,
                "error": "blocked_too_late",
                "message": BLOCKED_TOOL_INPUT,
            }
        return None

    async def after_model_callback(
        self,
        callback_context: CallbackContext,
        llm_response: LlmResponse,
    ) -> LlmResponse | None:
        del callback_context
        self.hook_log.append("after_model")
        content = llm_response.content
        text = ""
        if content:
            text = "".join(part.text or "" for part in content.parts or [])
        if "RAW-SECRET" not in text:
            return None
        return LlmResponse(
            content=types.ModelContent(REDACTED_MODEL_OUTPUT)
        )
