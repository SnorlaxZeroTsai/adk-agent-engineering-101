# Bounded Specialist

Status: `validated`.

Portability: `version-specific`.

Canonical manifest:
[`manifests/bounded-specialist.json`](manifests/bounded-specialist.json).

## Problem

A coordinator needs independent semantic work, but unconstrained multi-agent
delegation would blur responsibility, context, state and failure ownership.

## Context

Use this pattern when a capability needs independent model reasoning, distinct
tools or policy, isolated context, or explicit conversation ownership.

## Forces

- Each specialist adds model calls, Events and failure states.
- Schema-valid output can still violate business invariants.
- Transfer and task completion create different conversation lifecycles.

## Decision

Choose function, single-turn, transfer or task mode from ownership
requirements. Bound a true specialist with typed input/output, deterministic
post-validation, explicit failure ownership and namespaced state.

## Architecture

```text
coordinator
  -> typed task request
  -> isolated specialist reasoning
  -> typed completion
  -> deterministic domain validation
  -> coordinator synthesis
```

Conversational transfer replaces the return edge only when the specialist
should own future user turns.

## Observable Contract

| ID | Contract |
|---|---|
| `typed-completion` | The coordinator receives a typed result and validates domain invariants before synthesis. |
| `context-isolation` | Task and single-turn specialists receive bounded input rather than unrelated history. |
| `ownership-mode` | Transfer owns future conversation; task mode returns completion to the coordinator. |
| `state-boundary` | Specialist outputs use distinct keys or an explicit merge policy. |

## When To Use

- independent model reasoning is required;
- tools or policy need a distinct boundary;
- unrelated conversation context should be excluded;
- a coordinator needs a typed result before continuing;
- specialist trajectory and failure must remain observable.

## When Not To Use

- a deterministic function expresses the capability;
- one semantic Workflow node is sufficient;
- specialist descriptions overlap;
- shared state has no owner or merge rule;
- delegation only adds a model call before the same deterministic result.

## Implementation

1. Use task mode for coordinator-owned results.
2. Use transfer only for specialist-owned future turns.
3. Disable parent and peer transfer on bounded task specialists.
4. Define `input_schema`, `output_schema` and post-output domain validation.
5. Namespace `output_key` or merge outputs explicitly.
6. Define hard-failure fallback outside the specialist.

## Failure Modes

| ID | Failure |
|---|---|
| `overlapping-charters` | Two model-visible specialists are indistinguishable and the wrong one is selected. |
| `hard-failure-without-route` | An unhandled child model failure aborts the coordinator without fallback. |
| `shared-state-overwrite` | Multiple specialists silently overwrite one Session key. |
| `transfer-escape` | A bounded task specialist transfers outside its responsibility. |

## Counterexamples

Use a function for deterministic capability. Use one single-turn node when
separate conversational ownership and task delegation add no contract value.

## ADK Versions

- ADK 2.6.3 `chat`, `single_turn`, `task` and `FinishTaskTool` behavior is
  validated.
- Direct ADK 1.x `AgentTool` composition remains comparative legacy evidence.

## Evidence

- Source and claim-level links:
  [`manifests/bounded-specialist.json`](manifests/bounded-specialist.json)
- Architecture analysis:
  [`../docs/multi-agent/specialist-boundaries.md`](../docs/multi-agent/specialist-boundaries.md)
- Executable evidence:
  [`../labs/03-multi-agent`](../labs/03-multi-agent/)

## Rejected Decisions

`agent-for-deterministic-capability`: reject creating a specialist for work that
a typed function or deterministic Workflow node can perform without independent
reasoning or ownership.
