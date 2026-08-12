from __future__ import annotations

import unittest

from agent_basics.tools import estimate_shipping
from agent_basics.tools import get_order_status


class OrderStatusTests(unittest.TestCase):
    def test_known_order_is_normalized_and_returned(self) -> None:
        result = get_order_status("  a100 ")

        self.assertTrue(result["ok"])
        self.assertEqual(result["order"]["order_id"], "A100")
        self.assertEqual(result["order"]["status"], "processing")

    def test_unknown_order_is_a_structured_domain_error(self) -> None:
        result = get_order_status("z999")

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "order_not_found")

    def test_empty_order_id_is_rejected(self) -> None:
        result = get_order_status(" ")

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "invalid_order_id")


class ShippingEstimateTests(unittest.TestCase):
    def test_regional_estimate_is_deterministic(self) -> None:
        result = estimate_shipping("regional", 2.5)

        self.assertTrue(result["ok"])
        self.assertEqual(result["estimate"]["cost"], 13.0)
        self.assertEqual(result["estimate"]["currency"], "USD")

    def test_zone_is_normalized(self) -> None:
        result = estimate_shipping(" LOCAL ", 1)

        self.assertTrue(result["ok"])
        self.assertEqual(result["estimate"]["destination_zone"], "local")
        self.assertEqual(result["estimate"]["cost"], 6.2)

    def test_unknown_zone_is_rejected(self) -> None:
        result = estimate_shipping("moon", 1)

        self.assertFalse(result["ok"])
        self.assertEqual(
            result["error"]["code"],
            "unsupported_destination_zone",
        )

    def test_non_positive_weight_is_rejected(self) -> None:
        result = estimate_shipping("local", 0)

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "invalid_weight")

    def test_weight_limit_is_enforced(self) -> None:
        result = estimate_shipping("international", 50.1)

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "weight_limit_exceeded")


if __name__ == "__main__":
    unittest.main()
