"""Dependency-free tests for approval and idempotency contracts."""

from __future__ import annotations

from dataclasses import replace
import unittest

from safety_hitl_lab.domain import ApprovalEnvelope
from safety_hitl_lab.domain import build_approval
from safety_hitl_lab.domain import FIXED_NOW_EPOCH
from safety_hitl_lab.domain import PAYMENT_REQUEST
from safety_hitl_lab.domain import PaymentLedger
from safety_hitl_lab.domain import request_hash
from safety_hitl_lab.domain import validate_approval


class ApprovalContractTests(unittest.TestCase):
    def test_valid_approval_binds_every_request_field(self) -> None:
        approval = build_approval()

        result = validate_approval(PAYMENT_REQUEST, approval)

        self.assertTrue(result.approved)
        self.assertEqual(result.code, "approved")
        self.assertEqual(approval.request_hash, request_hash(PAYMENT_REQUEST))

    def test_expired_approval_fails_closed(self) -> None:
        approval = build_approval(
            expires_at_epoch=FIXED_NOW_EPOCH - 1,
        )

        result = validate_approval(PAYMENT_REQUEST, approval)

        self.assertFalse(result.approved)
        self.assertEqual(result.code, "approval_expired")

    def test_unauthorized_approver_fails_closed(self) -> None:
        result = validate_approval(
            PAYMENT_REQUEST,
            build_approval(approver_id="contractor-4"),
        )

        self.assertEqual(result.code, "unauthorized_approver")

    def test_request_tampering_invalidates_digest(self) -> None:
        changed = replace(PAYMENT_REQUEST, amount_usd=9000)

        result = validate_approval(changed, build_approval())

        self.assertEqual(result.code, "request_hash_mismatch")

    def test_rejection_is_not_an_authorization(self) -> None:
        result = validate_approval(
            PAYMENT_REQUEST,
            build_approval(decision="reject"),
        )

        self.assertEqual(result.code, "decision_not_approved")

    def test_parser_rejects_truthy_timestamp_and_unknown_field(self) -> None:
        raw = build_approval().as_dict()
        raw["issued_at_epoch"] = "1786492740"
        raw["unexpected"] = True

        with self.assertRaisesRegex(ValueError, "fields differ"):
            ApprovalEnvelope.from_mapping(raw)

    def test_ledger_replay_is_idempotent(self) -> None:
        ledger = PaymentLedger()

        first = ledger.execute(
            PAYMENT_REQUEST,
            authorization_id="APR-1",
        )
        second = ledger.execute(
            PAYMENT_REQUEST,
            authorization_id="APR-1",
        )

        self.assertEqual(first["status"], "executed")
        self.assertEqual(second["status"], "already_executed")
        self.assertEqual(ledger.effect_count, 1)
        self.assertEqual(ledger.attempt_count, 2)


if __name__ == "__main__":
    unittest.main()
