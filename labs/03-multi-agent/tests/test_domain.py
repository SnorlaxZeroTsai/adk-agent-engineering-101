from __future__ import annotations

import unittest

from multi_agent_lab.domain import decision_payload
from multi_agent_lab.domain import parse_case
from multi_agent_lab.domain import SupportCase
from multi_agent_lab.domain import triage_case


class CaseTriageTests(unittest.TestCase):
    def test_high_value_chargeback_routes_to_risk_operations(self) -> None:
        decision = triage_case(
            SupportCase(
                case_id="CASE-1",
                amount_usd=1200,
                days_open=1,
                chargeback_signal=True,
                customer_tier="standard",
            )
        )

        self.assertEqual(decision.risk_level, "high")
        self.assertEqual(decision.owner, "risk_operations")
        self.assertEqual(
            decision.reasons,
            ("chargeback_signal", "high_value"),
        )

    def test_stale_case_routes_to_priority_support(self) -> None:
        decision = triage_case(
            SupportCase(
                case_id="CASE-2",
                amount_usd=40,
                days_open=8,
                chargeback_signal=False,
                customer_tier="standard",
            )
        )

        self.assertEqual(decision.risk_level, "medium")
        self.assertEqual(decision.owner, "priority_support")

    def test_routine_case_has_explicit_reason(self) -> None:
        decision = triage_case(
            SupportCase(
                case_id="CASE-3",
                amount_usd=40,
                days_open=1,
                chargeback_signal=False,
                customer_tier="standard",
            )
        )

        self.assertEqual(decision.risk_level, "low")
        self.assertEqual(decision.owner, "standard_support")
        self.assertEqual(decision.reasons, ("routine_case",))

    def test_parse_case_normalizes_identity_and_tier(self) -> None:
        case = parse_case({
            "case_id": " case-4 ",
            "amount_usd": 5,
            "days_open": 0,
            "chargeback_signal": False,
            "customer_tier": " PRIORITY ",
        })

        self.assertEqual(case.case_id, "CASE-4")
        self.assertEqual(case.customer_tier, "priority")

    def test_parse_case_rejects_missing_contract_fields(self) -> None:
        with self.assertRaisesRegex(ValueError, "chargeback_signal"):
            parse_case({
                "case_id": "CASE-5",
                "amount_usd": 5,
                "days_open": 0,
                "customer_tier": "standard",
            })

    def test_parse_case_does_not_coerce_string_boolean(self) -> None:
        with self.assertRaisesRegex(ValueError, "must be a boolean"):
            parse_case({
                "case_id": "CASE-6",
                "amount_usd": 5,
                "days_open": 0,
                "chargeback_signal": "false",
                "customer_tier": "standard",
            })

    def test_decision_payload_is_json_safe(self) -> None:
        payload = decision_payload()

        self.assertIsInstance(payload["reasons"], list)
        self.assertEqual(payload["owner"], "risk_operations")


if __name__ == "__main__":
    unittest.main()
