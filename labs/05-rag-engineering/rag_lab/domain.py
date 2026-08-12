"""Shared corpus and question contract for both RAG architectures."""

from __future__ import annotations

from dataclasses import dataclass


PUBLIC = "public"
INTERNAL = "internal"
ABSTENTION = "I cannot answer from the indexed sources."


@dataclass(frozen=True)
class SourceDocument:
    """One versioned source document before retrieval-specific ingestion."""

    doc_id: str
    version: int
    title: str
    uri: str
    visibility: str
    text: str
    active: bool = True


@dataclass(frozen=True)
class QueryCase:
    """Expected retrieval and answer behavior for one principal."""

    case_id: str
    question: str
    principal_role: str
    expected_doc_ids: tuple[str, ...]
    expected_fragments: tuple[str, ...]
    answerable: bool = True


ATLAS_V1 = SourceDocument(
    doc_id="atlas-spec",
    version=1,
    title="Atlas-7 specification",
    uri="kb://products/atlas-7/v1",
    visibility=PUBLIC,
    text=(
        "Atlas-7 is Northwind Robotics' warehouse robot. The specification "
        "valid through 2026-06-30 sets its maximum payload at 75 kg. "
        "Battery runtime is 14 hours."
    ),
    active=False,
)

ATLAS_V2 = SourceDocument(
    doc_id="atlas-spec",
    version=2,
    title="Atlas-7 specification",
    uri="kb://products/atlas-7/v2",
    visibility=PUBLIC,
    text=(
        "Atlas-7 is Northwind Robotics' warehouse robot. The current "
        "specification, effective 2026-07-01, sets its maximum payload at "
        "80 kg. Battery runtime is 14 hours."
    ),
)

WARRANTY = SourceDocument(
    doc_id="warranty-policy",
    version=1,
    title="Standard warranty",
    uri="kb://policies/warranty/v1",
    visibility=PUBLIC,
    text=(
        "All Northwind Robotics robots include a standard 3-year limited "
        "warranty covering manufacturing defects."
    ),
)

RETURNS = SourceDocument(
    doc_id="return-policy",
    version=1,
    title="Hardware returns",
    uri="kb://policies/returns/v1",
    visibility=PUBLIC,
    text=(
        "Hardware can be returned for a full refund within 30 days of "
        "delivery after an RMA request."
    ),
)

SERVICE_BULLETIN = SourceDocument(
    doc_id="service-bulletin",
    version=1,
    title="Atlas-7 diagnostic bulletin",
    uri="kb://internal/atlas-7-diagnostics/v1",
    visibility=INTERNAL,
    text=(
        "Internal service bulletin SB-44. The Atlas-7 diagnostic port reset "
        "code is RST-44. This code must not be disclosed to customers."
    ),
)

BREEZE_SPEC = SourceDocument(
    doc_id="breeze-spec",
    version=1,
    title="Breeze-2 specification",
    uri="kb://products/breeze-2/v1",
    visibility=PUBLIC,
    text=(
        "The Breeze-2 inventory drone has a flight time of 28 minutes and a "
        "48 MP barcode-recognition camera."
    ),
)

DELETED_PROMOTION = SourceDocument(
    doc_id="legacy-promotion",
    version=1,
    title="Retired launch promotion",
    uri="kb://promotions/orbit15/v1",
    visibility=PUBLIC,
    text=(
        "The retired promotion code ORBIT15 provided a 15 percent discount "
        "on Atlas-7 orders."
    ),
    active=False,
)


QUERY_CASES = (
    QueryCase(
        case_id="current-payload",
        question="What is the current maximum payload of the Atlas-7?",
        principal_role=PUBLIC,
        expected_doc_ids=("atlas-spec",),
        expected_fragments=("80 kg",),
    ),
    QueryCase(
        case_id="warranty-and-return",
        question=(
            "What are the standard warranty length and hardware return window?"
        ),
        principal_role=PUBLIC,
        expected_doc_ids=("warranty-policy", "return-policy"),
        expected_fragments=("3-year", "30 days"),
    ),
    QueryCase(
        case_id="internal-reset",
        question="What is the Atlas-7 diagnostic port reset code?",
        principal_role=INTERNAL,
        expected_doc_ids=("service-bulletin",),
        expected_fragments=("RST-44",),
    ),
    QueryCase(
        case_id="public-reset",
        question="What is the Atlas-7 diagnostic port reset code?",
        principal_role=PUBLIC,
        expected_doc_ids=(),
        expected_fragments=(),
        answerable=False,
    ),
    QueryCase(
        case_id="unknown-product",
        question="What is the battery capacity of the Zephyr-9?",
        principal_role=PUBLIC,
        expected_doc_ids=(),
        expected_fragments=(),
        answerable=False,
    ),
)

DELETED_PROMOTION_CASE = QueryCase(
    case_id="deleted-promotion",
    question="What promotion code applies to an Atlas-7 order?",
    principal_role=PUBLIC,
    expected_doc_ids=(),
    expected_fragments=(),
    answerable=False,
)


def current_documents() -> tuple[SourceDocument, ...]:
    """Return the source-of-truth snapshot visible to a fresh ingestion."""

    return (
        ATLAS_V2,
        WARRANTY,
        RETURNS,
        SERVICE_BULLETIN,
        BREEZE_SPEC,
    )


def current_versions() -> dict[str, int]:
    return {document.doc_id: document.version for document in current_documents()}


def deleted_doc_ids() -> set[str]:
    return {DELETED_PROMOTION.doc_id}


def query_case(case_id: str) -> QueryCase:
    for case in QUERY_CASES:
        if case.case_id == case_id:
            return case
    raise KeyError(case_id)
