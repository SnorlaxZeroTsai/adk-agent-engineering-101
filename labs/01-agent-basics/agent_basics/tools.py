"""Deterministic capabilities for the order-support Agent."""

from __future__ import annotations

from typing import Literal


DestinationZone = Literal["local", "regional", "international"]

_ORDERS: dict[str, dict[str, str]] = {
    "A100": {
        "status": "processing",
        "estimated_ship_date": "2026-08-14",
        "carrier": "not_assigned",
    },
    "B200": {
        "status": "shipped",
        "estimated_ship_date": "2026-08-10",
        "carrier": "Parcel Express",
    },
}

_SHIPPING_RATES: dict[DestinationZone, tuple[float, float, str]] = {
    "local": (5.0, 1.2, "2-3 business days"),
    "regional": (8.0, 2.0, "3-5 business days"),
    "international": (20.0, 5.0, "7-12 business days"),
}


def _error(code: str, message: str) -> dict[str, object]:
    return {
        "ok": False,
        "error": {
            "code": code,
            "message": message,
        },
    }


def get_order_status(order_id: str) -> dict[str, object]:
    """Look up one order by ID without mutating it.

    Args:
        order_id: Customer-visible order ID, such as ``A100``.

    Returns:
        A structured success result with the order record, or an ``error``
        object whose code is ``invalid_order_id`` or ``order_not_found``.
    """

    normalized_id = order_id.strip().upper()
    if not normalized_id:
        return _error("invalid_order_id", "Order ID must not be empty.")

    record = _ORDERS.get(normalized_id)
    if record is None:
        return _error(
            "order_not_found",
            f"No order exists with ID {normalized_id}.",
        )

    return {
        "ok": True,
        "order": {
            "order_id": normalized_id,
            **record,
        },
    }


def estimate_shipping(
    destination_zone: DestinationZone,
    weight_kg: float,
) -> dict[str, object]:
    """Estimate shipping from a destination zone and package weight.

    Args:
        destination_zone: One of ``local``, ``regional`` or ``international``.
        weight_kg: Package weight greater than 0 and no more than 50 kilograms.

    Returns:
        A structured estimate, or an ``error`` object for invalid input.
    """

    normalized_zone = str(destination_zone).strip().lower()
    if normalized_zone not in _SHIPPING_RATES:
        return _error(
            "unsupported_destination_zone",
            "Destination zone must be local, regional, or international.",
        )

    if isinstance(weight_kg, bool) or not isinstance(weight_kg, (int, float)):
        return _error("invalid_weight", "Weight must be a number in kilograms.")
    if weight_kg <= 0:
        return _error("invalid_weight", "Weight must be greater than 0 kg.")
    if weight_kg > 50:
        return _error(
            "weight_limit_exceeded",
            "This estimator supports packages up to 50 kg.",
        )

    zone = normalized_zone
    base_cost, per_kg_cost, delivery_window = _SHIPPING_RATES[zone]
    total_cost = round(base_cost + per_kg_cost * weight_kg, 2)

    return {
        "ok": True,
        "estimate": {
            "destination_zone": zone,
            "weight_kg": weight_kg,
            "currency": "USD",
            "cost": total_cost,
            "delivery_window": delivery_window,
        },
    }
