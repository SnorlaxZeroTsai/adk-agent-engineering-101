"""Pure deterministic business rules shared by both workflow adapters."""

from __future__ import annotations

from typing import Any


class UnapprovedBriefError(ValueError):
    """Raised when a caller tries to publish an unapproved brief."""


def normalize_topic(raw_topic: str) -> str:
    """Normalize and validate the requested research topic."""

    topic = " ".join(raw_topic.split()).strip()
    if not topic:
        raise ValueError("topic must not be empty")
    return topic


def collect_facts(topic: str) -> list[str]:
    """Return deterministic facts for the lab topic."""

    normalized = normalize_topic(topic)
    return [
        f"{normalized}: demand is measurable.",
        f"{normalized}: rollout can be staged.",
    ]


def collect_risks(topic: str) -> list[str]:
    """Return deterministic risks for the lab topic."""

    normalized = normalize_topic(topic)
    return [
        f"{normalized}: stale inputs can invalidate the recommendation.",
        f"{normalized}: an unbounded rollout increases blast radius.",
    ]


def compose_draft(
    topic: str,
    facts: list[str],
    risks: list[str],
) -> str:
    """Compose one stable draft from parallel analysis results."""

    if not facts:
        raise ValueError("facts must not be empty")
    if not risks:
        raise ValueError("risks must not be empty")
    return (
        f"Brief: {normalize_topic(topic)}\n"
        f"Facts: {' | '.join(facts)}\n"
        f"Risks: {' | '.join(risks)}"
    )


def review_draft(
    draft: str,
    attempt: int,
    *,
    required_reviews: int = 2,
) -> dict[str, Any]:
    """Score a draft and approve it after a configured number of reviews."""

    if not draft:
        raise ValueError("draft must not be empty")
    if attempt < 1:
        raise ValueError("attempt must be positive")
    if required_reviews < 1:
        raise ValueError("required_reviews must be positive")

    approved = attempt >= required_reviews
    return {
        "attempt": attempt,
        "score": 0.9 if approved else 0.6,
        "approved": approved,
    }


def revise_draft(draft: str, revision: int) -> str:
    """Add a deterministic mitigation note."""

    if revision < 1:
        raise ValueError("revision must be positive")
    return (
        f"{draft}\n"
        f"Revision {revision}: verify freshness and use a staged rollout."
    )


def finalize_brief(
    topic: str,
    draft: str,
    *,
    approved: bool,
    review_count: int,
) -> dict[str, Any]:
    """Publish an approved brief and reject unsafe finalization."""

    if not approved:
        raise UnapprovedBriefError("cannot finalize an unapproved brief")
    return {
        "status": "approved",
        "topic": normalize_topic(topic),
        "review_count": review_count,
        "body": draft,
    }


def unsafe_finalize_brief(
    topic: str,
    draft: str,
    *,
    approved: bool,
    review_count: int,
) -> dict[str, Any]:
    """Intentional counterexample that ignores the approval invariant."""

    return {
        "status": "approved" if approved else "unsafe_unapproved",
        "topic": normalize_topic(topic),
        "review_count": review_count,
        "body": draft,
    }
