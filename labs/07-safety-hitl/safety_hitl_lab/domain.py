"""Deterministic approval and side-effect contracts for Lab 07."""

from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
import hashlib
import json
from typing import Any
from typing import Mapping


ACTION_TYPE = "vendor_payment"
POLICY_VERSION = "payments-v1"
AUTHORIZED_APPROVERS = frozenset({"finance-manager-7"})
FIXED_NOW_EPOCH = 1_786_492_800


@dataclass(frozen=True)
class PaymentRequest:
    """Immutable business request that will be bound to one approval."""

    action_id: str
    vendor_id: str
    amount_usd: int
    destination_account: str
    memo: str

    def __post_init__(self) -> None:
        if not self.action_id.strip():
            raise ValueError("action_id must not be empty")
        if not self.vendor_id.strip():
            raise ValueError("vendor_id must not be empty")
        if self.amount_usd <= 0:
            raise ValueError("amount_usd must be positive")
        if not self.destination_account.strip():
            raise ValueError("destination_account must not be empty")

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


PAYMENT_REQUEST = PaymentRequest(
    action_id="PAY-2026-0812-01",
    vendor_id="vendor-atlas",
    amount_usd=2500,
    destination_account="acct-vendor-atlas",
    memo="August platform support",
)


def request_hash(request: PaymentRequest) -> str:
    """Return a stable digest over every consequential request field."""

    payload = json.dumps(
        request.as_dict(),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class ApprovalEnvelope:
    """Application-owned authorization data carried by ADK confirmation."""

    approval_id: str
    action_id: str
    action_type: str
    request_hash: str
    approver_id: str
    decision: str
    policy_version: str
    issued_at_epoch: int
    expires_at_epoch: int

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "ApprovalEnvelope":
        """Parse without truthy coercion or accepting unknown fields."""

        expected = {
            "approval_id",
            "action_id",
            "action_type",
            "request_hash",
            "approver_id",
            "decision",
            "policy_version",
            "issued_at_epoch",
            "expires_at_epoch",
        }
        if set(raw) != expected:
            missing = sorted(expected - set(raw))
            extra = sorted(set(raw) - expected)
            raise ValueError(
                f"approval envelope fields differ; missing={missing}, "
                f"extra={extra}"
            )
        string_fields = expected - {"issued_at_epoch", "expires_at_epoch"}
        for name in string_fields:
            if not isinstance(raw[name], str) or not raw[name].strip():
                raise ValueError(f"{name} must be a non-empty string")
        for name in ("issued_at_epoch", "expires_at_epoch"):
            if type(raw[name]) is not int:
                raise ValueError(f"{name} must be an integer")
        return cls(**dict(raw))

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ApprovalValidation:
    """One explicit authorization verdict."""

    approved: bool
    code: str


def build_approval(
    request: PaymentRequest = PAYMENT_REQUEST,
    *,
    approval_id: str = "APR-2026-0812-01",
    approver_id: str = "finance-manager-7",
    decision: str = "approve",
    action_id: str | None = None,
    action_type: str = ACTION_TYPE,
    digest: str | None = None,
    policy_version: str = POLICY_VERSION,
    issued_at_epoch: int = FIXED_NOW_EPOCH - 60,
    expires_at_epoch: int = FIXED_NOW_EPOCH + 300,
) -> ApprovalEnvelope:
    """Build a deterministic envelope, with overrides for breakage tests."""

    return ApprovalEnvelope(
        approval_id=approval_id,
        action_id=action_id or request.action_id,
        action_type=action_type,
        request_hash=digest or request_hash(request),
        approver_id=approver_id,
        decision=decision,
        policy_version=policy_version,
        issued_at_epoch=issued_at_epoch,
        expires_at_epoch=expires_at_epoch,
    )


def validate_approval(
    request: PaymentRequest,
    approval: ApprovalEnvelope,
    *,
    now_epoch: int = FIXED_NOW_EPOCH,
) -> ApprovalValidation:
    """Fail closed on identity, scope, integrity, policy and time."""

    checks = (
        (approval.decision == "approve", "decision_not_approved"),
        (approval.action_id == request.action_id, "action_id_mismatch"),
        (approval.action_type == ACTION_TYPE, "action_scope_mismatch"),
        (
            approval.request_hash == request_hash(request),
            "request_hash_mismatch",
        ),
        (
            approval.approver_id in AUTHORIZED_APPROVERS,
            "unauthorized_approver",
        ),
        (
            approval.policy_version == POLICY_VERSION,
            "policy_version_mismatch",
        ),
        (approval.issued_at_epoch <= now_epoch, "approval_not_yet_valid"),
        (now_epoch <= approval.expires_at_epoch, "approval_expired"),
    )
    for passed, code in checks:
        if not passed:
            return ApprovalValidation(approved=False, code=code)
    return ApprovalValidation(approved=True, code="approved")


@dataclass(frozen=True)
class LedgerEntry:
    """One externally visible payment effect."""

    action_id: str
    request_hash: str
    authorization_id: str


class PaymentLedger:
    """Idempotent external side-effect simulator keyed by action ID."""

    def __init__(self) -> None:
        self.entries: dict[str, LedgerEntry] = {}
        self.attempt_count = 0

    def execute(
        self,
        request: PaymentRequest,
        *,
        authorization_id: str,
    ) -> dict[str, Any]:
        self.attempt_count += 1
        digest = request_hash(request)
        existing = self.entries.get(request.action_id)
        if existing:
            if existing.request_hash != digest:
                raise ValueError(
                    "idempotency key reused for a different payment request"
                )
            return {
                "ok": True,
                "status": "already_executed",
                "action_id": request.action_id,
            }
        self.entries[request.action_id] = LedgerEntry(
            action_id=request.action_id,
            request_hash=digest,
            authorization_id=authorization_id,
        )
        return {
            "ok": True,
            "status": "executed",
            "action_id": request.action_id,
        }

    @property
    def effect_count(self) -> int:
        return len(self.entries)
