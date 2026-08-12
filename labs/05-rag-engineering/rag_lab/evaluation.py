"""Deterministic retrieval, grounding and citation evaluation."""

from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
import re
from typing import Iterable
from typing import Mapping

from .domain import ABSTENTION
from .domain import QueryCase
from .retrieval import RetrievalHit


CITATION_PATTERN = re.compile(r"\[([a-z0-9-]+)@v(\d+)\]")


@dataclass(frozen=True)
class GroundedAnswer:
    text: str
    cited_sources: tuple[tuple[str, int], ...]


@dataclass(frozen=True)
class CaseEvaluation:
    case_id: str
    retrieved_doc_ids: tuple[str, ...]
    retrieval_recall: float
    retrieval_precision: float
    answer_correct: bool
    cited_sources: tuple[tuple[str, int], ...]
    citation_precision: float
    citation_recall: float
    grounded: bool
    access_violations: int
    stale_hits: int
    deleted_hits: int

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def _citation(doc_id: object, version: object) -> str:
    if not isinstance(doc_id, str) or not isinstance(version, int):
        return ""
    return f" [{doc_id}@v{version}]"


def _matching_hit(
    hits: Iterable[Mapping[str, object]],
    pattern: str,
) -> Mapping[str, object] | None:
    compiled = re.compile(pattern, re.IGNORECASE)
    for hit in hits:
        if compiled.search(str(hit.get("text", ""))):
            return hit
    return None


def compose_grounded_answer(
    question: str,
    hits: list[Mapping[str, object]],
) -> GroundedAnswer:
    """Create deterministic model output from retrieved evidence only."""

    question_lower = question.lower()
    parts: list[str] = []
    cited: list[tuple[str, int]] = []

    def cite(hit: Mapping[str, object]) -> str:
        doc_id = hit.get("doc_id")
        version = hit.get("version")
        if isinstance(doc_id, str) and isinstance(version, int):
            source = (doc_id, version)
            if source not in cited:
                cited.append(source)
        return _citation(doc_id, version)

    if "payload" in question_lower:
        hit = _matching_hit(hits, r"maximum payload at 80 kg")
        if hit:
            parts.append(
                "The current Atlas-7 maximum payload is 80 kg" + cite(hit) + "."
            )
    elif "warranty" in question_lower and "return" in question_lower:
        warranty = _matching_hit(hits, r"3-year limited warranty")
        returns = _matching_hit(hits, r"within 30 days")
        if warranty:
            parts.append(
                "The standard warranty lasts 3-year" + cite(warranty) + "."
            )
        if returns:
            parts.append(
                "The hardware return window is 30 days" + cite(returns) + "."
            )
    elif "reset code" in question_lower:
        hit = _matching_hit(hits, r"reset code is ([A-Z0-9-]+)")
        if hit:
            match = re.search(
                r"reset code is ([A-Z0-9-]+)",
                str(hit.get("text", "")),
            )
            if match:
                parts.append(
                    f"The diagnostic reset code is {match.group(1)}"
                    + cite(hit)
                    + "."
                )
    elif "flight time" in question_lower:
        hit = _matching_hit(hits, r"flight time of 28 minutes")
        if hit:
            parts.append(
                "The Breeze-2 flight time is 28 minutes" + cite(hit) + "."
            )
    elif "promotion code" in question_lower:
        hit = _matching_hit(hits, r"promotion code ([A-Z0-9-]+)")
        if hit:
            match = re.search(
                r"promotion code ([A-Z0-9-]+)",
                str(hit.get("text", "")),
            )
            if match:
                parts.append(
                    f"The promotion code is {match.group(1)}"
                    + cite(hit)
                    + "."
                )

    if not parts:
        return GroundedAnswer(text=ABSTENTION, cited_sources=())
    return GroundedAnswer(
        text=" ".join(parts),
        cited_sources=tuple(cited),
    )


def parse_citations(answer: str) -> tuple[tuple[str, int], ...]:
    return tuple(
        (doc_id, int(version))
        for doc_id, version in CITATION_PATTERN.findall(answer)
    )


def evaluate_case(
    *,
    case: QueryCase,
    hits: Iterable[RetrievalHit | Mapping[str, object]],
    answer: str,
    current_versions: Mapping[str, int],
    deleted_doc_ids: set[str],
) -> CaseEvaluation:
    normalized: list[Mapping[str, object]] = []
    for hit in hits:
        if isinstance(hit, RetrievalHit):
            normalized.append(hit.as_dict())
        else:
            normalized.append(hit)

    retrieved_doc_ids = tuple(
        dict.fromkeys(
            str(hit["doc_id"])
            for hit in normalized
            if isinstance(hit.get("doc_id"), str)
        )
    )
    expected = set(case.expected_doc_ids)
    retrieved = set(retrieved_doc_ids)
    overlap = expected & retrieved
    if expected:
        recall = len(overlap) / len(expected)
    else:
        recall = 1.0 if not retrieved else 0.0
    if retrieved:
        precision = len(overlap) / len(retrieved)
    else:
        precision = 1.0 if not expected else 0.0

    if case.answerable:
        answer_correct = all(
            fragment.lower() in answer.lower()
            for fragment in case.expected_fragments
        )
    else:
        answer_correct = answer == ABSTENTION

    citations = parse_citations(answer)
    retrieved_sources = {
        (str(hit["doc_id"]), int(hit["version"]))
        for hit in normalized
        if isinstance(hit.get("doc_id"), str)
        and isinstance(hit.get("version"), int)
    }
    valid_citations = {
        source
        for source in citations
        if source in retrieved_sources and source[0] in expected
    }
    if citations:
        citation_precision = len(valid_citations) / len(set(citations))
    else:
        citation_precision = 1.0 if not expected else 0.0
    if expected:
        citation_recall = len(
            {doc_id for doc_id, _ in valid_citations}
        ) / len(expected)
    else:
        citation_recall = 1.0 if not citations else 0.0

    access_violations = sum(
        1
        for hit in normalized
        if case.principal_role == "public"
        and hit.get("visibility") == "internal"
    )
    stale_hits = sum(
        1
        for hit in normalized
        if isinstance(hit.get("doc_id"), str)
        and isinstance(hit.get("version"), int)
        and hit["doc_id"] in current_versions
        and hit["version"] != current_versions[hit["doc_id"]]
    )
    deleted_hits = sum(
        1
        for hit in normalized
        if hit.get("doc_id") in deleted_doc_ids
    )
    grounded = (
        answer_correct
        and recall == 1.0
        and citation_precision == 1.0
        and citation_recall == 1.0
        and access_violations == 0
        and stale_hits == 0
        and deleted_hits == 0
    )
    return CaseEvaluation(
        case_id=case.case_id,
        retrieved_doc_ids=retrieved_doc_ids,
        retrieval_recall=recall,
        retrieval_precision=precision,
        answer_correct=answer_correct,
        cited_sources=citations,
        citation_precision=citation_precision,
        citation_recall=citation_recall,
        grounded=grounded,
        access_violations=access_violations,
        stale_hits=stale_hits,
        deleted_hits=deleted_hits,
    )
