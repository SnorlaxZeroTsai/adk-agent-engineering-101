"""Intentionally weak tool boundaries kept for comparison."""

from __future__ import annotations


def handle_order_request(query: str) -> str:
    """Parse, route and answer every order request from one free-form string."""

    normalized = query.upper()
    if "A100" in normalized:
        return "Order A100 is processing."
    if "REGIONAL" in normalized and "2.5" in normalized:
        return "Shipping costs USD 13.00."
    return "I could not handle that order request."


def get_order_status_or_raise(order_id: str) -> dict[str, str]:
    """Look up an order but raise for the expected not-found outcome."""

    if order_id.strip().upper() != "A100":
        raise KeyError(f"Order {order_id} was not found")
    return {
        "order_id": "A100",
        "status": "processing",
    }
