# Deterministic Workflow

Status: candidate, validated locally against pinned ADK 2.6.3.

## Problem

An Agent system has ordering, fan-out, retry, approval or loop invariants that
must remain predictable under model variation and failure.

## Architecture

Represent invariants as graph edges and typed nodes:

```text
START -> validate -> [A, B] -> join -> evaluate
                                      | pass -> finish
                                      | retry -> repair -> evaluate
                                      | exhausted -> reject
```

Keep semantic model work inside bounded nodes. Keep transition policy in code.

## When To Use

- prerequisite order is mandatory;
- all parallel results are required;
- side effects need approval or idempotency;
- retries are exception-specific;
- loops need explicit pass and exhaustion outcomes;
- trajectory and resume must be auditable.

## When Not To Use

- the task is one bounded model decision with narrow tools;
- the next step genuinely depends on open-ended semantic interpretation;
- a normal function call expresses the entire operation;
- the graph would only mirror incidental prompt wording.

## Why

The graph makes control decisions testable independently of model output and
gives each execution a node path, run ID, route and failure boundary.

## Alternatives

- one `LlmAgent` selecting tools;
- legacy `SequentialAgent`/`ParallelAgent`/`LoopAgent`;
- application code calling functions directly;
- LLM coordinator delegating to specialists;
- external workflow engine for cross-service durability.

## Trade-Offs

- more explicit nodes and schemas;
- graph evolution must preserve replay compatibility;
- parallel branches need conflict-free state or an explicit join;
- ADK retry state is local and not durable across resume;
- an external engine may still be required for long-lived distributed work.

## Failure Modes

- treating `max_iterations` as success;
- unconditional or accidentally unbounded cycles;
- multiple retry owners;
- duplicate parent/child output Events;
- missing state hidden until a downstream node;
- replaying non-idempotent side effects;
- renaming nodes without testing historical Session replay;
- using an LLM router for fixed policy.

## ADK Implementation

- `Workflow` and routed `Edge` definitions;
- `FunctionNode` for deterministic functions;
- `JoinNode` for required fan-in;
- `RetryConfig` on the narrow failing node;
- `RequestInput` or interrupt Events for HITL;
- `use_as_output=True` for delegated output ownership;
- Session Event replay for resume.

## Primary Sources

- pinned `Workflow`, `Graph`, `NodeRunner` and replay utilities;
- R03 `llm-auditor`;
- R05 `deep-search`;
- R13 `ambient-expense-agent`.

See [`../references/source-index.md`](../references/source-index.md).

## Minimal Example

See
[`../labs/02-workflow-engineering/workflow_lab/graph_pipeline.py`](../labs/02-workflow-engineering/workflow_lab/graph_pipeline.py)
and its runtime tests.
