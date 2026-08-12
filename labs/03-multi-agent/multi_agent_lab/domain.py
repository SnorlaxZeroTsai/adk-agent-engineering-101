"""Pure case-triage capability shared by every Lab 03 architecture."""

from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SupportCase:
    """Inputs required to assign one support case."""

    case_id: str
    amount_usd: int
    days_open: int
    chargeback_signal: bool
    customer_tier: str


@dataclass(frozen=True)
class TriageDecision:
    """Stable output contract used by functions and specialist Agents."""

    case_id: str
    risk_level: str
    owner: str
    reasons: tuple[str, ...]


FIXED_CASE = SupportCase(
    case_id="CASE-100",
    amount_usd=1500,
    days_open=10,
    chargeback_signal=True,
    customer_tier="standard",
)


def parse_case(value: dict[str, Any]) -> SupportCase:
    """Validate a plain mapping without requiring ADK or Pydantic."""

    required = {
        "case_id",
        "amount_usd",
        "days_open",
        "chargeback_signal",
        "customer_tier",
    }
    missing = sorted(required.difference(value))
    if missing:
        raise ValueError(f"Missing case fields: {', '.join(missing)}")

    amount_value = value["amount_usd"]
    days_value = value["days_open"]
    signal_value = value["chargeback_signal"]
    if isinstance(amount_value, bool) or not isinstance(amount_value, int):
        raise ValueError("amount_usd must be an integer")
    if isinstance(days_value, bool) or not isinstance(days_value, int):
        raise ValueError("days_open must be an integer")
    if not isinstance(signal_value, bool):
        raise ValueError("chargeback_signal must be a boolean")

    case_id = str(value["case_id"]).strip().upper()
    amount_usd = amount_value
    days_open = days_value
    customer_tier = str(value["customer_tier"]).strip().lower()
    if not case_id:
        raise ValueError("case_id must not be empty")
    if amount_usd < 0:
        raise ValueError("amount_usd must be non-negative")
    if days_open < 0:
        raise ValueError("days_open must be non-negative")
    if customer_tier not in {"standard", "priority"}:
        raise ValueError("customer_tier must be standard or priority")

    return SupportCase(
        case_id=case_id,
        amount_usd=amount_usd,
        days_open=days_open,
        chargeback_signal=signal_value,
        customer_tier=customer_tier,
    )


def triage_case(case: SupportCase) -> TriageDecision:
    """Assign a case using deterministic, reviewable business rules."""

    reasons: list[str] = []
    if case.chargeback_signal:
        reasons.append("chargeback_signal")
    if case.amount_usd >= 1000:
        reasons.append("high_value")
    if case.days_open >= 7:
        reasons.append("stale_case")

    if case.chargeback_signal and case.amount_usd >= 1000:
        risk_level = "high"
        owner = "risk_operations"
    elif case.customer_tier == "priority" or case.days_open >= 7:
        risk_level = "medium"
        owner = "priority_support"
    else:
        risk_level = "low"
        owner = "standard_support"

    return TriageDecision(
        case_id=case.case_id,
        risk_level=risk_level,
        owner=owner,
        reasons=tuple(reasons or ["routine_case"]),
    )


def case_payload(case: SupportCase = FIXED_CASE) -> dict[str, Any]:
    """Return the model/tool-visible input payload."""

    return asdict(case)


def decision_payload(
    decision: TriageDecision | None = None,
) -> dict[str, Any]:
    """Return the canonical JSON-safe specialist result."""

    resolved = decision or triage_case(FIXED_CASE)
    payload = asdict(resolved)
    payload["reasons"] = list(resolved.reasons)
    return payload
