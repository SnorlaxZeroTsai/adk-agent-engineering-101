"""Dependency-free data placement rules and shared support dossier."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


Placement = Literal[
    "model_input_context",
    "session_state",
    "artifact",
    "memory",
]


@dataclass(frozen=True)
class SupportDossier:
    """Facts required to answer one support follow-up."""

    contact_channel: str
    previous_fix: str
    product: str
    account_tier: str


DOSSIER = SupportDossier(
    contact_channel="SMS",
    previous_fix="router reboot",
    product="HomeHub",
    account_tier="priority",
)

EXPECTED_ANSWER = "Contact via SMS and mention the previous router reboot."


def render_dossier(dossier: SupportDossier = DOSSIER) -> str:
    """Render a stable plain-text datum for every runtime variant."""

    return (
        f"Preferred contact channel: {dossier.contact_channel}. "
        f"Previous successful fix: {dossier.previous_fix}. "
        f"Product: {dossier.product}. "
        f"Account tier: {dossier.account_tier}."
    )


def large_dossier_text() -> str:
    """Return a deterministic payload large enough to expose prompt repetition."""

    diagnostic_line = (
        "Diagnostic sample: downstream signal stable; upstream jitter observed. "
    )
    return render_dossier() + "\n" + diagnostic_line * 320


def choose_placement(
    *,
    lifetime: Literal["invocation", "session", "cross_session"],
    size: Literal["small", "large"],
    access: Literal["always", "on_demand", "semantic_recall"],
) -> Placement:
    """Recommend a storage surface from explicit lifecycle requirements."""

    if access == "semantic_recall":
        if lifetime != "cross_session":
            raise ValueError("semantic recall requires cross_session lifetime")
        return "memory"
    if size == "large" or access == "on_demand":
        return "artifact"
    if lifetime == "session":
        return "session_state"
    if lifetime == "invocation":
        return "model_input_context"
    raise ValueError(
        "small always-visible cross-session data needs an explicit product "
        "policy; choose user state, artifact or memory deliberately"
    )
