"""Dependency-free tests for the shared workflow business rules."""

from __future__ import annotations

import unittest

from workflow_lab.domain import collect_facts
from workflow_lab.domain import collect_risks
from workflow_lab.domain import compose_draft
from workflow_lab.domain import finalize_brief
from workflow_lab.domain import normalize_topic
from workflow_lab.domain import review_draft
from workflow_lab.domain import revise_draft
from workflow_lab.domain import UnapprovedBriefError


class DomainRuleTests(unittest.TestCase):
    def test_topic_is_normalized(self) -> None:
        self.assertEqual(
            normalize_topic("  payment   reliability "),
            "payment reliability",
        )

    def test_empty_topic_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "topic"):
            normalize_topic("   ")

    def test_parallel_analysis_is_deterministic(self) -> None:
        topic = "payment reliability"
        self.assertEqual(collect_facts(topic), collect_facts(topic))
        self.assertEqual(collect_risks(topic), collect_risks(topic))

    def test_review_requires_two_attempts_by_default(self) -> None:
        first = review_draft("draft", 1)
        second = review_draft("draft", 2)
        self.assertFalse(first["approved"])
        self.assertTrue(second["approved"])

    def test_revision_adds_explicit_mitigation(self) -> None:
        revised = revise_draft("draft", 1)
        self.assertIn("verify freshness", revised)
        self.assertIn("staged rollout", revised)

    def test_finalization_enforces_approval(self) -> None:
        with self.assertRaises(UnapprovedBriefError):
            finalize_brief(
                "payment reliability",
                "draft",
                approved=False,
                review_count=1,
            )

    def test_full_domain_path_produces_approved_brief(self) -> None:
        topic = normalize_topic("payment reliability")
        draft = compose_draft(
            topic,
            collect_facts(topic),
            collect_risks(topic),
        )
        draft = revise_draft(draft, 1)
        result = finalize_brief(
            topic,
            draft,
            approved=review_draft(draft, 2)["approved"],
            review_count=2,
        )
        self.assertEqual(result["status"], "approved")
        self.assertEqual(result["review_count"], 2)


if __name__ == "__main__":
    unittest.main()
