from __future__ import annotations

import inspect
import unittest

from agent_basics.tools import estimate_shipping
from agent_basics.tools import get_order_status
from experiments.broken_tools import get_order_status_or_raise
from experiments.broken_tools import handle_order_request


class BrokenVariantObservationTests(unittest.TestCase):
    def test_catch_all_tool_hides_explicit_domain_inputs(self) -> None:
        catch_all_parameters = list(inspect.signature(handle_order_request).parameters)
        baseline_parameters = {
            *inspect.signature(get_order_status).parameters,
            *inspect.signature(estimate_shipping).parameters,
        }

        self.assertEqual(catch_all_parameters, ["query"])
        self.assertEqual(
            baseline_parameters,
            {"order_id", "destination_zone", "weight_kg"},
        )

    def test_raising_variant_conflates_domain_miss_with_failure(self) -> None:
        baseline = get_order_status("z999")

        self.assertEqual(baseline["error"]["code"], "order_not_found")
        with self.assertRaises(KeyError):
            get_order_status_or_raise("z999")


if __name__ == "__main__":
    unittest.main()
