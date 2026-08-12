from __future__ import annotations

import unittest

from context_memory_lab.domain import choose_placement
from context_memory_lab.domain import large_dossier_text
from context_memory_lab.domain import render_dossier


class DataPlacementPolicyTests(unittest.TestCase):
    def test_dossier_has_common_answer_facts(self) -> None:
        rendered = render_dossier()

        self.assertIn("SMS", rendered)
        self.assertIn("router reboot", rendered)

    def test_invocation_context_is_for_small_transient_data(self) -> None:
        self.assertEqual(
            choose_placement(
                lifetime="invocation",
                size="small",
                access="always",
            ),
            "model_input_context",
        )

    def test_session_state_is_for_small_session_data(self) -> None:
        self.assertEqual(
            choose_placement(
                lifetime="session",
                size="small",
                access="always",
            ),
            "session_state",
        )

    def test_artifact_is_for_large_or_on_demand_data(self) -> None:
        self.assertEqual(
            choose_placement(
                lifetime="session",
                size="large",
                access="always",
            ),
            "artifact",
        )
        self.assertEqual(
            choose_placement(
                lifetime="invocation",
                size="small",
                access="on_demand",
            ),
            "artifact",
        )

    def test_memory_requires_cross_session_semantic_recall(self) -> None:
        self.assertEqual(
            choose_placement(
                lifetime="cross_session",
                size="small",
                access="semantic_recall",
            ),
            "memory",
        )
        with self.assertRaisesRegex(ValueError, "cross_session"):
            choose_placement(
                lifetime="session",
                size="small",
                access="semantic_recall",
            )

    def test_large_dossier_is_large_enough_to_expose_repetition(self) -> None:
        self.assertGreater(len(large_dossier_text()), 20_000)


if __name__ == "__main__":
    unittest.main()
