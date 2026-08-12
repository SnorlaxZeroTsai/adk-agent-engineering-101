# Bounded Specialist

Status: candidate, validated locally against pinned ADK 2.6.3.

## Problem

A coordinator needs semantic work that is too independent for a normal
function, but unconstrained multi-agent delegation would blur responsibility,
state ownership and failure handling.

## Architecture

```text
coordinator
  -> typed task request
  -> specialist with narrow instruction/tools and isolated scope
  -> typed completion
  -> deterministic domain validation
  -> coordinator synthesis
```

Use conversational transfer instead only when the specialist should own future
user turns.

## When To Use

- the work requires independent model reasoning;
- the specialist needs a distinct tool or policy boundary;
- context should be isolated from unrelated conversation;
- the coordinator needs a typed result before continuing;
- specialist trajectory and failure must remain observable.

## When Not To Use

- a deterministic function expresses the capability;
- a single semantic Workflow node is sufficient;
- specialist descriptions overlap;
- shared state has no ownership or merge policy;
- delegation only adds a model call before the same deterministic result.

## Why

The boundary makes responsibility, input, output, context and completion
explicit while retaining coordinator ownership of the user-facing response.

## Alternatives

- pure function or `FunctionNode`;
- `single_turn` Agent node;
- chat-mode transfer;
- direct `AgentTool`;
- external service or remote A2A Agent;
- deterministic router plus one selected specialist.

## Trade-Offs

- at least one child model call plus coordinator calls;
- more Event and failure states;
- schema validation still needs domain validation;
- task isolation does not provide fallback automatically;
- recursive task delegation is limited in the pinned runtime;
- state keys and operational budgets must be partitioned.

## Failure Modes

- two specialists with indistinguishable charters;
- model selects a schema-compatible but semantically wrong specialist;
- hard child failure aborts without an explicit fallback route;
- multiple children overwrite one Session state key;
- task Agent can transfer out of its intended boundary;
- coordinator summarizes before validated task completion;
- final-answer eval ignores delegation trajectory.

## ADK Implementation

- `LlmAgent(mode="task")` with `input_schema` and `output_schema`;
- attach it through the coordinator's `sub_agents`;
- `FinishTaskTool` for validated completion;
- function-call ID as task run ID and isolation scope;
- `disallow_transfer_to_parent=True`;
- `disallow_transfer_to_peers=True`;
- namespaced `output_key` or explicit merge node;
- deterministic post-output invariant validator.

## Primary Sources

- pinned `LlmAgent`, `AgentTool` and transfer processor;
- pinned LLM Agent Workflow wrapper and `FinishTaskTool`;
- pinned Task API E2E tests;
- R06 financial-advisor specialist composition.

See [`../references/source-index.md`](../references/source-index.md).

## Minimal Example

See
[`../labs/03-multi-agent/multi_agent_lab/builders.py`](../labs/03-multi-agent/multi_agent_lab/builders.py)
and its runtime tests.
