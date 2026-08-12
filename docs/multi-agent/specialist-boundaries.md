# Multi-Agent Specialist Boundaries

Status: pinned ADK 2.6.3 source analysis and local scripted runtime experiments
complete.

## Question

When does a capability justify an independent Agent instead of a deterministic
function or Workflow node, and which ADK delegation lifecycle matches that
responsibility?

## Hypothesis

A specialist should be an Agent only when it needs at least one of:

- independent semantic reasoning;
- its own instruction and tool boundary;
- isolated task context;
- conversational identity across user turns;
- a typed delegation contract with coordinator-owned synthesis.

Deterministic policy remains a function or Workflow node. Agent identity does
not make a business rule safer.

## Version Boundary

At the pinned commit, `LlmAgent.mode` exposes three distinct lifecycles:

| Mode | Intended relationship |
|---|---|
| `chat` | Standard conversational Agent reachable through transfer |
| `single_turn` | Complete one bounded task without chatting |
| `task` | Complete delegated work and signal typed completion |

The default depends on placement: a sub-agent defaults to chat, while an
`LlmAgent` used as a Workflow node defaults to single-turn.

Direct `AgentTool` still exists, but its source discourages new inline use. A
`single_turn` sub-agent is automatically exposed through
`_SingleTurnAgentTool`; a task sub-agent is exposed through `_TaskAgentTool`.

## Four Execution Boundaries

### Deterministic Function Node

```text
START -> deterministic_triage -> state/output
```

Use when the capability is a reviewable rule. No model chooses or performs the
decision.

### Single-Turn Agent Node

```text
START -> LlmAgent(mode="single_turn") -> state/output
```

The Workflow wrapper:

- defaults `include_contents` to `none` unless explicitly set;
- appends only the node input into a copied Session view;
- keeps branch/isolation metadata;
- performs one bounded Agent run.

This is a semantic node, not a conversational owner.

### Conversational Transfer

```text
coordinator --transfer_to_agent--> chat specialist
user follow-up ------------------> same specialist
```

The transfer tool is model-visible only for eligible chat targets. Task and
single-turn children are excluded from transfer targets.

Transfer changes the active conversational Agent. The specialist answers the
user directly and remains active on the next turn unless its transfer settings
return control elsewhere.

### Task Delegation

```text
coordinator FC -> task specialist
                   -> finish_task FC/FR
coordinator <- synthesized specialist FR
coordinator -> user-facing synthesis
```

The coordinator sees a tool declaration derived from the task specialist's
input schema. The wrapper:

1. intercepts the task function call;
2. runs the child through `ctx.run_node()` with the function-call ID as stable
   run ID and isolation scope;
3. waits for a successful `finish_task` function response;
4. synthesizes a child-result function response for the coordinator;
5. re-enters the coordinator model loop.

This is coordinator-owned task completion, not conversational handoff.

## Source Facts

### Automatic Wrapping

During `LlmAgent.model_post_init()`:

- a task Agent gets `FinishTaskTool`;
- a single-turn sub-agent becomes `_SingleTurnAgentTool`;
- a task sub-agent becomes `_TaskAgentTool`;
- a chat sub-agent remains a transfer target.

Task Agent tools defer their normal function response. The chat Workflow wrapper
dispatches the child and synthesizes the response after completion.

### Structured Completion

`FinishTaskTool` builds its parameters from the child's output schema. Invalid
arguments return an error dictionary rather than successful completion, so the
child model can call `finish_task` again.

The task wrapper promotes arguments only after the success function response.
Intermediate child text is not the task result.

### Isolation

Task delegation uses:

```text
run_id = function_call.id
isolation_scope = function_call.id
```

The synthesized result is intentionally visible to the coordinator's scope,
not the child's scope. Upstream tests also verify that foreign isolation scopes
do not enter the child request.

### Current Limitation

The pinned E2E suite marks nested task delegation as an expected failure:
chat-mode coordinator dispatch logic handles task function calls, while the
task-mode wrapper currently focuses on `finish_task`.

Do not design recursive task hierarchies from the API shape alone.

## Lab 03 Design

One dependency-free function defines a case-triage contract:

```text
input:
  case_id, amount_usd, days_open, chargeback_signal, customer_tier

output:
  case_id, risk_level, owner, reasons
```

The same fixed case and canonical output are used in all four variants.
Scripted models remove provider variation while preserving real ADK requests,
tool declarations, wrappers, Events and Session state.

## Baseline Results

| Boundary | Model requests | Yielded Events | Stored Events | User reply owner |
|---|---:|---:|---:|---|
| Function node | 0 | 1 | 2 | Workflow |
| Single-turn node | 1 | 1 | 2 | Workflow node |
| Chat transfer | 2 | 3 | 4 | Specialist |
| Task delegation | 3 | 5 | 6 | Coordinator |

All four stored the same typed result.

Request count is not a token, latency or monetary measurement. It shows the
minimum reasoning boundaries introduced by each architecture in this
experiment.

## Event Trajectories

Transfer:

```text
coordinator: transfer_to_agent FC
coordinator: transfer_to_agent FR + transfer action
specialist: final message
```

Task:

```text
coordinator: specialist FC
specialist: finish_task FC
specialist: finish_task FR + state delta
user: synthesized specialist FR
coordinator: final message
```

Final text alone hides both delegation type and state owner. Trajectory
evaluation must distinguish these paths.

## Conversational Ownership

The transfer experiment added a second user turn.

Observed:

- coordinator requests remained at one;
- specialist requests increased from one to two;
- the second turn emitted one specialist Event;
- the specialist's second request contained prior result text and the new
  follow-up.

Transfer is appropriate when the specialist should continue the conversation.
It is excessive when the coordinator only needs one typed result.

## Failure Recovery

### Contract Failure

The task child first called `finish_task` with invalid enum values.

Observed:

- validation produced an error function response;
- child request count increased from one to two;
- the corrected call completed;
- the coordinator then received the synthesized result and answered.

This recovery is local because the child still owns the output contract.

### Hard Failure

The task child's model raised:

```text
RuntimeError: specialist model unavailable
```

Observed:

- one error Event used the child node path and task isolation scope;
- the original exception reached the Runner caller;
- the coordinator made only its initial delegation request;
- no fallback specialist ran;
- no result state was written.

Delegation is not a fallback policy. Retry, alternate routing and user-visible
degradation need explicit ownership.

## Overlapping Responsibility

Two task specialists were given identical descriptions and parameter schemas.
Both declarations appeared in the coordinator request.

The scripted coordinator selected B. A received zero requests. B returned a
schema-valid output with a domain-wrong owner.

This demonstrates two separate contracts:

- schema validation protects shape and allowed primitive values;
- responsibility boundaries and cross-field business invariants require
  distinct descriptions, deterministic policy or post-delegation validation.

Adding more Agents without mutually exclusive charters moves architecture
ambiguity into the model.

## Shared-State Conflict

Two task specialists wrote different values to `triage_result`.

Observed:

```text
write 1: owner = risk_operations
write 2: owner = priority_support
stored:  owner = priority_support
```

No error Event or merge decision represented the overwrite.

Use one of:

- one writer per state key;
- namespaced specialist outputs;
- an explicit typed join/merge node;
- optimistic concurrency in a durable state service.

Do not use shared Session state as an implicit blackboard unless conflict
semantics are deliberate.

## Decision Guide

Use a function or deterministic node when:

- policy is fully expressible and testable in code;
- no independent model reasoning is needed;
- the same input must always produce the same decision.

Use a single-turn Agent when:

- one bounded semantic transformation needs a model;
- conversation history should be excluded or tightly scoped;
- a Workflow owns ordering and downstream processing.

Use conversational transfer when:

- the specialist should answer the user directly;
- follow-up turns belong to the specialist;
- its identity, tools and history are part of the experience.

Use task delegation when:

- the coordinator must select a specialist;
- the specialist needs isolated multi-step work;
- typed completion must return to coordinator-owned synthesis;
- delegation and completion Events must be auditable.

## Engineering Checklist

- Define mutually exclusive specialist responsibilities.
- Use input and output schemas, then add domain invariant validation.
- Decide who owns the user-facing reply.
- Decide who owns retry and fallback.
- Keep task isolation scopes visible in traces.
- Disable transfers that would escape a bounded task.
- Give each specialist its own state namespace or explicit merge contract.
- Count model calls and measure real tokens/latency before production.
- Test same-session continuation separately from task resume.
- Check pinned limitations before building nested delegation.
