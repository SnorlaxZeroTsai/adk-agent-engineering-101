# Durable Approval Boundary

Status: `validated`.

Portability: `portable`.

Canonical manifest:
[`manifests/durable-approval-boundary.json`](manifests/durable-approval-boundary.json).

## Problem

A model can ignore a prompt asking it to wait. A boolean confirmation can be
replayed, expire, come from the wrong principal or authorize different
arguments from those eventually executed.

## Context

Use this pattern when a tool or Workflow node can create an irreversible,
regulated or financially consequential effect.

## Forces

- A scoped envelope and ledger cost more than a confirmation boolean.
- Durable storage and partial-commit recovery become production dependencies.
- Exact request binding can require reapproval after a material edit.

## Decision

Treat framework confirmation as interrupt transport, not authorization. Bind
an authenticated approval to the immutable action request, validate it before
execution, and enforce action-ID idempotency in the external effect service.

## Architecture

```text
immutable action request
  -> approval-required policy
  -> runtime interrupt
  -> authenticated scoped approval envelope
  -> identity/scope/hash/time/policy validation
  -> action-ID idempotent effect
  -> separate decision and effect evidence
```

## Observable Contract

| ID | Contract |
|---|---|
| `scoped-authorization` | Approval binds approver, action ID/type, request digest, policy and expiry. |
| `pre-effect-enforcement` | Rejected or invalid approval cannot call the side-effect service. |
| `fresh-object-resume` | Fresh runtime objects resume one valid approved action. |
| `external-idempotency` | Later replay can re-enter the tool but cannot repeat the effect. |

## When To Use

- effects are irreversible or regulated;
- a human must authorize exact consequential arguments;
- resume and replay are expected;
- audit evidence must separate decision from execution.

## When Not To Use

- a reversible low-risk read has deterministic authorization;
- approval is being used to compensate for an over-privileged tool;
- the approval channel cannot authenticate or authorize the approver.

## Implementation

1. Construct and hash the immutable action request.
2. Choose tool-level confirmation or node-level `RequestInput`.
3. Authenticate the approval channel outside the model.
4. Validate schema without truthy coercion.
5. Fail closed on identity, scope, digest, policy or time mismatch.
6. Persist decision evidence.
7. Execute through an action-ID idempotent service.
8. Test rejection, expiry, tampering, fresh resume and replay.

## Failure Modes

| ID | Failure |
|---|---|
| `prompt-only-confirmation` | Natural-language instructions do not prevent the call. |
| `after-tool-enforcement` | Output masking occurs after the external effect. |
| `unscoped-boolean` | `confirmed=true` has no identity, request binding or expiry. |
| `session-dedup` | Session state is mistaken for external idempotency. |

## Counterexamples

Apply deterministic authorization directly to low-risk reads. Reduce tool
privilege and validate arguments even when human approval is present.

## ADK Versions

- ADK 2.6.3 `ToolConfirmation` and Workflow `RequestInput` are validated.
- The authorization envelope is portable; interrupt transport needs
  runtime-specific replay tests.

## Evidence

- Source and claim-level links:
  [`manifests/durable-approval-boundary.json`](manifests/durable-approval-boundary.json)
- Architecture analysis:
  [`../docs/safety/safety-and-hitl.md`](../docs/safety/safety-and-hitl.md)
- Executable evidence:
  [`../labs/07-safety-hitl`](../labs/07-safety-hitl/)

## Rejected Decisions

`framework-confirmation-as-authorization`: reject treating `confirmed=true` as
complete business authorization. Validate a scoped envelope and execute through
an idempotent effect service.
