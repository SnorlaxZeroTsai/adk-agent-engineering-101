"""Dependency-free retrieval and evaluation tests."""

from __future__ import annotations

from dataclasses import replace
import unittest

from rag_lab.domain import ATLAS_V1
from rag_lab.domain import ATLAS_V2
from rag_lab.domain import current_documents
from rag_lab.domain import current_versions
from rag_lab.domain import DELETED_PROMOTION
from rag_lab.domain import deleted_doc_ids
from rag_lab.domain import INTERNAL
from rag_lab.domain import PUBLIC
from rag_lab.domain import query_case
from rag_lab.evaluation import compose_grounded_answer
from rag_lab.evaluation import evaluate_case
from rag_lab.retrieval import ExplicitVectorIndex
from rag_lab.retrieval import ManagedSearchSimulator


class RetrievalContractTests(unittest.TestCase):
    def test_current_source_has_one_version_per_document(self) -> None:
        documents = current_documents()
        self.assertEqual(len(documents), len({doc.doc_id for doc in documents}))
        self.assertEqual(current_versions()["atlas-spec"], 2)

    def test_managed_sync_keeps_latest_active_version(self) -> None:
        backend = ManagedSearchSimulator()
        backend.sync([ATLAS_V1, ATLAS_V2])
        hits = backend.search(
            query="current Atlas-7 maximum payload",
            principal_role=PUBLIC,
        )
        self.assertEqual([hit.version for hit in hits], [2])

    def test_explicit_ingestion_replaces_old_version(self) -> None:
        index = ExplicitVectorIndex()
        index.ingest(
            [replace(ATLAS_V1, active=True)],
            delete_missing=False,
        )
        index.ingest([ATLAS_V2], delete_missing=False)
        self.assertEqual({chunk.version for chunk in index.chunks}, {2})

    def test_explicit_ingestion_can_expose_stale_version_bug(self) -> None:
        index = ExplicitVectorIndex()
        index.ingest(
            [replace(ATLAS_V1, active=True)],
            delete_missing=False,
        )
        index.ingest(
            [ATLAS_V2],
            replace_versions=False,
            delete_missing=False,
        )
        self.assertEqual({chunk.version for chunk in index.chunks}, {1, 2})

    def test_acl_is_applied_before_results_are_returned(self) -> None:
        index = ExplicitVectorIndex()
        index.ingest(current_documents())
        public_hits = index.search(
            query="Atlas-7 diagnostic port reset code",
            principal_role=PUBLIC,
        )
        internal_hits = index.search(
            query="Atlas-7 diagnostic port reset code",
            principal_role=INTERNAL,
        )
        self.assertNotIn(
            "service-bulletin",
            {hit.doc_id for hit in public_hits},
        )
        self.assertIn(
            "service-bulletin",
            {hit.doc_id for hit in internal_hits},
        )

    def test_delete_missing_removes_retired_document(self) -> None:
        index = ExplicitVectorIndex()
        active_promotion = replace(DELETED_PROMOTION, active=True)
        index.ingest([*current_documents(), active_promotion])
        index.ingest(current_documents(), delete_missing=True)
        self.assertNotIn(
            DELETED_PROMOTION.doc_id,
            {chunk.doc_id for chunk in index.chunks},
        )


class GroundingEvaluationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.index = ExplicitVectorIndex()
        self.index.ingest(current_documents())

    def _evaluate(self, case_id: str):
        case = query_case(case_id)
        hits = self.index.search(
            query=case.question,
            principal_role=case.principal_role,
        )
        answer = compose_grounded_answer(
            case.question,
            [hit.as_dict() for hit in hits],
        )
        return evaluate_case(
            case=case,
            hits=hits,
            answer=answer.text,
            current_versions=current_versions(),
            deleted_doc_ids=deleted_doc_ids(),
        )

    def test_payload_case_is_retrieved_and_cited(self) -> None:
        evaluation = self._evaluate("current-payload")
        self.assertTrue(evaluation.grounded)
        self.assertEqual(evaluation.retrieval_recall, 1.0)
        self.assertEqual(evaluation.citation_recall, 1.0)

    def test_multi_document_case_requires_both_citations(self) -> None:
        evaluation = self._evaluate("warranty-and-return")
        self.assertTrue(evaluation.grounded)
        self.assertEqual(
            set(evaluation.retrieved_doc_ids),
            {"warranty-policy", "return-policy"},
        )

    def test_unanswerable_case_abstains_without_citation(self) -> None:
        evaluation = self._evaluate("unknown-product")
        self.assertTrue(evaluation.answer_correct)
        self.assertTrue(evaluation.grounded)
        self.assertEqual(evaluation.cited_sources, ())

    def test_text_without_provenance_fails_grounding_gate(self) -> None:
        case = query_case("current-payload")
        hits = self.index.search(
            query=case.question,
            principal_role=case.principal_role,
        )
        stripped = [hit.as_dict(include_provenance=False) for hit in hits]
        answer = compose_grounded_answer(case.question, stripped)
        evaluation = evaluate_case(
            case=case,
            hits=stripped,
            answer=answer.text,
            current_versions=current_versions(),
            deleted_doc_ids=deleted_doc_ids(),
        )
        self.assertTrue(evaluation.answer_correct)
        self.assertFalse(evaluation.grounded)
        self.assertEqual(evaluation.citation_recall, 0.0)


if __name__ == "__main__":
    unittest.main()
