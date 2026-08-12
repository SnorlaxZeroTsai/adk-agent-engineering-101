"""ADK-backed policy and approval lifecycle tests."""

from __future__ import annotations

import logging
import unittest
from unittest.mock import MagicMock
from unittest.mock import patch
import warnings

from google.adk.agents.context import Context

from safety_hitl_lab.domain import build_approval
from safety_hitl_lab.domain import FIXED_NOW_EPOCH
from safety_hitl_lab.policy import BLOCKED_USER_MESSAGE
from safety_hitl_lab.policy import REDACTED_MODEL_OUTPUT
from safety_hitl_lab.runtime import request_text
from safety_hitl_lab.runtime import run_confirmation_payment
from safety_hitl_lab.runtime import run_plugin_payment
from safety_hitl_lab.runtime import run_prompt_only_payment
from safety_hitl_lab.runtime import run_unsafe_model_output
from safety_hitl_lab.runtime import run_unsafe_tool_output
from safety_hitl_lab.runtime import run_unsafe_user_input
from safety_hitl_lab.runtime import run_workflow_approval


logging.getLogger("google_adk").setLevel(logging.CRITICAL)
warnings.filterwarnings(
    "ignore",
    message=r".*JSON_SCHEMA_FOR_FUNC_DECL.*",
)
warnings.filterwarnings(
    "ignore",
    message=r".*TOOL_CONFIRMATION.*",
)


class BoundaryPolicyTests(unittest.IsolatedAsyncioTestCase):
    async def test_prompt_only_confirmation_does_not_block_action(
        self,
    ) -> None:
        result = await run_prompt_only_payment()

        self.assertIsNone(result.error)
        self.assertEqual(result.ledger.effect_count, 1)
        self.assertEqual(result.output_text, "Payment executed.")

    async def test_before_tool_policy_blocks_before_side_effect(self) -> None:
        result = await run_plugin_payment(enforce_before_tool=True)

        self.assertIsNone(result.error)
        self.assertEqual(result.ledger.effect_count, 0)
        self.assertIn(
            "before_tool:execute_vendor_payment",
            result.plugin.hook_log,
        )

    async def test_after_tool_mask_is_too_late_to_undo_side_effect(
        self,
    ) -> None:
        result = await run_plugin_payment(enforce_before_tool=False)

        self.assertIsNone(result.error)
        self.assertEqual(result.ledger.effect_count, 1)
        self.assertIn(
            "after_tool:execute_vendor_payment",
            result.plugin.hook_log,
        )

    async def test_unsafe_user_input_halts_before_model(self) -> None:
        result = await run_unsafe_user_input()

        self.assertIsNone(result.error)
        self.assertEqual(result.model_request_count, 0)
        self.assertEqual(result.output_text, BLOCKED_USER_MESSAGE)

    async def test_unsafe_tool_output_is_removed_before_next_model_call(
        self,
    ) -> None:
        result = await run_unsafe_tool_output()

        self.assertIsNone(result.error)
        self.assertEqual(result.model_request_count, 2)
        visible = request_text(result.model.requests[1])
        self.assertNotIn("RAW-SECRET", visible)
        self.assertIn("unsafe_tool_output", visible)

    async def test_unsafe_model_output_is_replaced(self) -> None:
        result = await run_unsafe_model_output()

        self.assertIsNone(result.error)
        self.assertEqual(result.output_text, REDACTED_MODEL_OUTPUT)


class ToolConfirmationTests(unittest.IsolatedAsyncioTestCase):
    async def test_valid_approval_resumes_with_fresh_runner_once(
        self,
    ) -> None:
        result = await run_confirmation_payment()

        self.assertIsNone(result.error)
        self.assertEqual(result.ledger.effect_count, 1)
        self.assertEqual(result.tool_invocation_count, 2)
        self.assertEqual(
            result.session.state["approval_decision"]["status"],
            "approved",
        )
        self.assertEqual(
            result.session.state["payment_effect"]["status"],
            "executed",
        )

    async def test_rejection_never_executes_side_effect(self) -> None:
        result = await run_confirmation_payment(confirmed=False)

        self.assertIsNone(result.error)
        self.assertEqual(result.ledger.effect_count, 0)
        self.assertEqual(
            result.session.state["approval_decision"]["code"],
            "confirmation_rejected",
        )

    async def test_expired_approval_never_executes_side_effect(self) -> None:
        result = await run_confirmation_payment(
            approval=build_approval(
                expires_at_epoch=FIXED_NOW_EPOCH - 1,
            )
        )

        self.assertIsNone(result.error)
        self.assertEqual(result.ledger.effect_count, 0)
        self.assertEqual(
            result.session.state["approval_decision"]["code"],
            "approval_expired",
        )

    async def test_unauthorized_approver_never_executes_side_effect(
        self,
    ) -> None:
        result = await run_confirmation_payment(
            approval=build_approval(approver_id="contractor-4")
        )

        self.assertEqual(result.ledger.effect_count, 0)
        self.assertEqual(
            result.session.state["approval_decision"]["code"],
            "unauthorized_approver",
        )

    async def test_mismatched_request_hash_never_executes_side_effect(
        self,
    ) -> None:
        result = await run_confirmation_payment(
            approval=build_approval(digest="tampered")
        )

        self.assertEqual(result.ledger.effect_count, 0)
        self.assertEqual(
            result.session.state["approval_decision"]["code"],
            "request_hash_mismatch",
        )

    async def test_replayed_confirmation_relies_on_ledger_idempotency(
        self,
    ) -> None:
        result = await run_confirmation_payment(replay=True)

        self.assertIsNone(result.error)
        self.assertEqual(result.ledger.effect_count, 1)
        self.assertEqual(result.tool_invocation_count, 3)
        self.assertEqual(result.ledger.attempt_count, 2)
        self.assertTrue(result.replay_events)


class WorkflowRequestInputTests(unittest.IsolatedAsyncioTestCase):
    async def test_request_input_resumes_downstream_with_fresh_objects(
        self,
    ) -> None:
        result = await run_workflow_approval()

        self.assertIsNone(result.error)
        self.assertEqual(result.ledger.effect_count, 1)
        self.assertEqual(
            result.session.state["workflow_approval"]["status"],
            "executed",
        )
        self.assertTrue(
            any(
                call.name == "adk_request_input"
                for event in result.first_events
                for call in event.get_function_calls()
            )
        )


class CredentialBoundaryTests(unittest.TestCase):
    def _context(self, function_call_id=None) -> Context:
        invocation = MagicMock()
        invocation.session.state = {}
        invocation._state_schema = None
        return Context(
            invocation,
            function_call_id=function_call_id,
        )

    def test_callback_context_cannot_request_tool_credential(self) -> None:
        context = self._context()

        with self.assertRaisesRegex(ValueError, "requires function_call_id"):
            context.request_credential(MagicMock())

    def test_tool_credential_request_is_scoped_to_function_call(self) -> None:
        context = self._context(function_call_id="payment-call")
        auth_config = MagicMock()

        with patch(
            "google.adk.auth.auth_handler.AuthHandler",
            autospec=True,
        ) as handler:
            handler.return_value.generate_auth_request.return_value = (
                "credential-request"
            )
            context.request_credential(auth_config)

        self.assertEqual(
            context.actions.requested_auth_configs,
            {"payment-call": "credential-request"},
        )


if __name__ == "__main__":
    unittest.main()
