# Durable Approval Boundary

Status: candidate pattern, observed in Phase 7 local/scripted experiments.

## Problem

A model can ignore a prompt that asks it to wait. A boolean confirmation can
also be replayed, expire, come from the wrong principal or authorize different
arguments than the ones eventually executed.

## Context

Use this pattern when a tool or Workflow node can create an irreversible,
regulated or financially consequential effect.

## Architecture

```text
immutable action request
  -> policy says approval is required
  -> runtime emits interrupt
  -> authenticated approver returns scoped envelope
  -> application validates identity/scope/hash/time/policy
  -> idempotent side-effect service executes by action ID
  -> decision and effect evidence persist separately
```

ADK confirmation or `RequestInput` transports the interrupt and response. The
application owns authorization. The external system owns effect idempotency.

## Invariants

- Approval identifies an authenticated approver.
- Approval names one action ID and action type.
- Approval binds every consequential argument through a stable digest.
- Decision, policy version, issue time and expiry are explicit.
- Rejection or validation failure cannot call the side-effect service.
- One action ID can produce at most one external effect.
- Replayed responses remain observable but harmless.
- Approval payloads contain no raw credential.

## Forces

- More envelope and ledger code than a simple confirmation boolean.
- Better auditability and deterministic negative tests.
- Durable storage and atomicity become production dependencies.
- Short expiry reduces stale authorization but increases operator friction.
- Exact request binding can require reapproval after any material edit.

## Implementation

1. Construct the immutable action request before interrupting.
2. Compute a canonical digest over all consequential fields.
3. Choose tool-level confirmation or node-level `RequestInput`.
4. Authenticate the approval channel outside the model.
5. Validate envelope schema without truthy coercion.
6. Fail closed on identity, scope, digest, policy or time mismatch.
7. Persist decision evidence before/with execution.
8. Execute through a service that enforces action-ID idempotency.
9. Test fresh-object resume, rejection, expiry, tampering and replay.
10. Add the action contract to a per-case release gate.

## Failure Modes

- Natural-language "ask first" instruction.
- `confirmed=true` without approver identity.
- Approval for amount A reused for amount B.
- `after_tool` filter expected to undo an external effect.
- Session-only dedup used as payment idempotency.
- Credential or access token embedded in the approval payload.
- Approval UI protected by authentication but not authorization scope.
- Durable checkpoint committed separately from a non-idempotent side effect.

## Counterexamples

Do not add human approval to a reversible, low-risk read operation when a
deterministic authorization rule is sufficient.

Do not use approval to compensate for an over-privileged tool. Apply least
privilege and argument validation even after approval.

## Trade-Offs

- Higher implementation and storage cost.
- Explicit ownership across runtime, policy and external service.
- Reliable replay and retry behavior.
- Stronger audit and evaluation evidence.
- Additional recovery design for partial commits and process failure.

## Evidence

Lab 07 observed:

- prompt-only payment executed once;
- `before_tool` blocked before execution;
- `after_tool` masking occurred after one effect;
- rejected, expired, unauthorized and tampered approvals produced zero effects;
- fresh Runner resume executed one approved payment;
- later-run replay re-entered the tool but retained one ledger effect;
- node-level `RequestInput` used the same approval contract;
- the prompt-only variant failed the cross-phase release gate.

## Sources

- ADK `BasePlugin` and `PluginManager`
- ADK `FunctionTool`, `ToolConfirmation` and confirmation processor
- ADK `RequestInput` and Workflow HITL utilities
- `safety-plugins` and `ambient-expense-agent` recipes
- [`../docs/safety/safety-and-hitl.md`](../docs/safety/safety-and-hitl.md)
- [`../labs/07-safety-hitl`](../labs/07-safety-hitl/)
