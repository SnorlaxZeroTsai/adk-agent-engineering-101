# Deterministic Workflow

Status: `validated`.

Portability: `portable`.

Canonical manifest:
[`manifests/deterministic-workflow.json`](manifests/deterministic-workflow.json).

## Problem

An Agent system has ordering, fan-out, retry, approval or loop invariants that
must remain predictable under model variation, failure and resume.

## Context

Use this pattern when mandatory control decisions must be testable independently
of model output and the execution path must remain auditable.

## Forces

- Explicit nodes and schemas add implementation work.
- Stable node identity and idempotent effects are required for replay.
- A distributed workflow engine may still own very long-lived service work.

## Decision

Represent business control as code-owned graph edges and typed nodes. Keep
semantic model work inside bounded nodes, give retry and terminal outcomes one
owner, and make external effects idempotent.

## Architecture

```text
START -> validate -> [analyze-a, analyze-b] -> join -> evaluate
                                                 | pass -> finish
                                                 | retry -> repair -> evaluate
                                                 | exhausted -> reject
```

## Observable Contract

| ID | Contract |
|---|---|
| `explicit-control` | Ordering, routing and terminal outcomes appear in graph structure and Event node paths. |
| `typed-fan-in` | Required branch outputs are joined into a typed payload before downstream execution. |
| `bounded-retry` | One narrow node owns retry and emits failure evidence before recovery or exhaustion. |
| `replay-safe-effects` | Resume can re-surface output without repeating an external effect or duplicating terminal ownership. |

## When To Use

- prerequisite order is mandatory;
- all parallel results are required;
- retry and exhaustion need explicit domain outcomes;
- side effects require approval, idempotency or replay evidence;
- trajectory and resume must be audited.

## When Not To Use

- one function expresses the whole operation;
- one bounded semantic transformation needs no graph;
- the graph would only mirror incidental prompt wording;
- cross-service durability belongs in an external workflow engine.

## Implementation

1. Use deterministic functions or `FunctionNode` for policy-owned work.
2. Use typed join payloads for required fan-in.
3. Route success, rejection and loop exhaustion explicitly.
4. Put `RetryConfig` on the narrow failing node.
5. Persist Event evidence and protect external effects with idempotency.
6. Delegate one logical output owner.

## Failure Modes

| ID | Failure |
|---|---|
| `implicit-exhaustion` | A technical loop bound is treated as a domain outcome. |
| `multiple-retry-owners` | Framework, node and tool retries stack without one budget. |
| `state-output-conflict` | Missing join state or duplicate parent/child output stays hidden until downstream failure. |
| `replay-incompatibility` | Renamed nodes or non-idempotent effects make historical replay unsafe. |

## Counterexamples

A normal function is preferable for one deterministic operation. A single-turn
Agent node is preferable for one bounded semantic transformation.

## ADK Versions

- ADK 2.6.3 graph Workflow behavior is validated at the pinned commit.
- ADK 1.x composite Agents are comparative evidence with different
  parent-continuation behavior.

## Evidence

- Source and claim-level links:
  [`manifests/deterministic-workflow.json`](manifests/deterministic-workflow.json)
- Architecture analysis:
  [`../docs/workflows/deterministic-workflows.md`](../docs/workflows/deterministic-workflows.md)
- Executable evidence:
  [`../labs/02-workflow-engineering`](../labs/02-workflow-engineering/)

## Rejected Decisions

`llm-router-for-fixed-policy`: reject using an LLM coordinator for a route
already defined by business policy. Encode the route in Workflow edges and use
model calls only for bounded semantic nodes.
