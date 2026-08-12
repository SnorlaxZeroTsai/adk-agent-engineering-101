"""ADK event and failure-path tests for both RAG architectures."""

from __future__ import annotations

from types import SimpleNamespace
import unittest

from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.sessions import Session

from rag_lab.domain import DELETED_PROMOTION_CASE
from rag_lab.domain import query_case
from rag_lab.runtime import build_deletion_lag_index
from rag_lab.runtime import build_stale_index
from rag_lab.runtime import PrincipalFilteredSearchTool
from rag_lab.runtime import run_explicit_vector
from rag_lab.runtime import run_managed_search


class RagRuntimeTests(unittest.IsolatedAsyncioTestCase):
    async def test_managed_search_is_one_grounded_model_event(self) -> None:
        result = await run_managed_search(query_case("current-payload"))
        self.assertIsNone(result.error)
        self.assertEqual(result.model_request_count, 1)
        self.assertEqual(len(result.events), 1)
        self.assertIsNotNone(result.events[0].grounding_metadata)
        self.assertTrue(result.evaluation().grounded)

    async def test_explicit_vector_has_function_call_round_trip(self) -> None:
        result = await run_explicit_vector(query_case("current-payload"))
        self.assertIsNone(result.error)
        self.assertEqual(result.model_request_count, 2)
        self.assertEqual(len(result.events), 3)
        self.assertTrue(
            any(
                part.function_call
                for event in result.events
                if event.content
                for part in event.content.parts or []
            )
        )
        self.assertTrue(
            any(
                part.function_response
                for event in result.events
                if event.content
                for part in event.content.parts or []
            )
        )
        self.assertTrue(result.evaluation().grounded)

    async def test_same_corpus_baselines_pass_all_query_gates(self) -> None:
        for case_id in (
            "current-payload",
            "warranty-and-return",
            "internal-reset",
            "public-reset",
            "unknown-product",
        ):
            case = query_case(case_id)
            managed = await run_managed_search(case)
            explicit = await run_explicit_vector(case)
            with self.subTest(case_id=case_id, mode="managed"):
                self.assertTrue(managed.evaluation().grounded)
            with self.subTest(case_id=case_id, mode="explicit"):
                self.assertTrue(explicit.evaluation().grounded)

    async def test_native_search_filter_comes_from_principal_state(self) -> None:
        tool = PrincipalFilteredSearchTool(
            data_store_id=(
                "projects/p/locations/global/collections/c/dataStores/d"
            )
        )
        public_context = ReadonlyContext(
            SimpleNamespace(
                session=Session(
                    app_name="x",
                    user_id="u",
                    id="s",
                    state={"principal_role": "public"},
                )
            )
        )
        config = tool._build_vertex_ai_search_config(public_context)
        self.assertEqual(config.filter, 'visibility = "public"')

    async def test_unfiltered_native_search_leaks_internal_source(self) -> None:
        result = await run_managed_search(
            query_case("public-reset"),
            enforce_principal_filter=False,
        )
        evaluation = result.evaluation()
        self.assertEqual(evaluation.access_violations, 1)
        self.assertFalse(evaluation.grounded)
        self.assertIn("RST-44", result.answer)

    async def test_provenance_loss_keeps_answer_but_fails_citation(self) -> None:
        result = await run_explicit_vector(
            query_case("current-payload"),
            include_provenance=False,
        )
        evaluation = result.evaluation()
        self.assertTrue(evaluation.answer_correct)
        self.assertEqual(evaluation.citation_recall, 0.0)
        self.assertFalse(evaluation.grounded)

    async def test_stale_index_is_detected_even_if_answer_is_current(self) -> None:
        result = await run_explicit_vector(
            query_case("current-payload"),
            index=build_stale_index(),
        )
        evaluation = result.evaluation()
        self.assertGreater(evaluation.stale_hits, 0)
        self.assertFalse(evaluation.grounded)

    async def test_deletion_lag_can_resurface_retired_promotion(self) -> None:
        result = await run_explicit_vector(
            DELETED_PROMOTION_CASE,
            index=build_deletion_lag_index(),
        )
        evaluation = result.evaluation()
        self.assertEqual(evaluation.deleted_hits, 1)
        self.assertFalse(evaluation.answer_correct)
        self.assertFalse(evaluation.grounded)
        self.assertIn("ORBIT15", result.answer)

    async def test_retrieval_miss_abstains_without_fake_citation(self) -> None:
        for run in (run_managed_search, run_explicit_vector):
            result = await run(query_case("unknown-product"))
            with self.subTest(mode=result.mode):
                self.assertEqual(
                    result.answer,
                    "I cannot answer from the indexed sources.",
                )
                self.assertEqual(result.evaluation().cited_sources, ())

    async def test_model_call_cost_surface_is_explicit(self) -> None:
        case = query_case("warranty-and-return")
        managed = await run_managed_search(case)
        explicit = await run_explicit_vector(case)
        self.assertEqual(managed.model_request_count, 1)
        self.assertEqual(explicit.model_request_count, 2)
        self.assertLess(
            len(managed.events),
            len(explicit.events),
        )


if __name__ == "__main__":
    unittest.main()
