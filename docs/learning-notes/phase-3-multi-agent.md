# Phase 3 Learning Note: Multi-Agent Specialist Boundaries

Date: 2026-08-12

## Questions

1. When is an Agent a justified specialist rather than a function?
2. How do single-turn, transfer and task delegation differ in ownership?
3. What happens when specialist output fails validation or execution?
4. What protects responsibility and shared-state boundaries?

## Hypotheses

1. A deterministic capability does not improve by becoming an Agent.
2. Single-turn, transfer and task delegation are distinct lifecycles rather
   than interchangeable wrappers.
3. Typed task output can recover locally from schema failure.
4. Delegation does not automatically provide fallback.
5. Schemas do not resolve overlapping charters or shared-state conflicts.

All five are supported within the scripted local scope.

## Primary Sources

Pinned runtime:

```text
google/adk-python
a56f6e13ae38296b608808c7a3b37efe4b8c862e
google-adk 2.6.3
```

Studied symbols:

- `LlmAgent.mode` and `model_post_init`;
- transfer request processing and target selection;
- `AgentTool`, `_SingleTurnAgentTool`, `_TaskAgentTool`;
- `run_llm_agent_as_node`;
- `FinishTaskTool`;
- Task API and Agent-transfer E2E tests;
- R06 financial-advisor specialist composition.

Exact links are in
[`references/source-index.md`](../../references/source-index.md).

## Experiment Design

The fixed case:

```text
CASE-100
amount_usd = 1500
days_open = 10
chargeback_signal = true
customer_tier = standard
```

Canonical result:

```text
risk_level = high
owner = risk_operations
reasons = chargeback_signal, high_value, stale_case
```

The pure function supplies the ground truth. Scripted Agents emit that same
typed result through single-turn, transfer and task lifecycles.

## Results

| Boundary | Model calls | Yielded | Stored | Result owner |
|---|---:|---:|---:|---|
| Function node | 0 | 1 | 2 | Workflow |
| Single-turn node | 1 | 1 | 2 | Workflow node |
| Transfer | 2 | 3 | 4 | Specialist |
| Task delegation | 3 | 5 | 6 | Coordinator |

The cost column is request count only.

### Transfer Continuation

Two turns produced:

```text
coordinator requests: 1
specialist requests: 2
turn event counts: [3, 1]
```

The second request retained prior specialist output and the follow-up user
message. Conversation ownership moved with transfer.

### Task Validation Recovery

The child first returned invalid `risk_level` and `owner` enums.

```text
child requests: 2
coordinator requests: 2
yielded Events: 7
terminal error: none
```

The first `finish_task` response carried validation details. The corrected call
completed and wrote the canonical state.

### Hard Failure

The child model raised before completion.

```text
model requests: 2 total
yielded Events: delegation FC, child-path error
terminal error: RuntimeError
fallback: none
```

### Overlapping Responsibility

Two specialists had equal descriptions and schemas. Both appeared in the
coordinator's tool map. The coordinator selected only B, which returned a
schema-valid but domain-wrong owner.

### Shared-State Conflict

Two sequential task specialists wrote the same key. Both state deltas were
observable, but final Session state silently retained the second.

## Source-to-Experiment Corrections

Initial assumption:

> Agent-as-tool is one stable architecture.

Correction:

The pinned source distinguishes direct `AgentTool`, automatic single-turn
wrapping and deferred task delegation. Direct `AgentTool` is discouraged for
new inline composition.

Initial assumption:

> Structured output makes specialist selection safe.

Correction:

It validates the selected child's output shape. It does not prove that the
right child was selected or that fields satisfy domain relationships.

Initial assumption:

> A task Agent failure returns control to the coordinator for fallback.

Correction:

Schema failure can remain inside the child loop, but an unhandled model failure
propagated and stopped the coordinator. Fallback must be explicit.

## Architecture Decisions

- Keep deterministic routing rules outside model-selected delegation.
- Require independent reasoning, isolation or conversation ownership before
  creating a specialist Agent.
- Use single-turn Agents as bounded semantic Workflow nodes.
- Use transfer only when the specialist should own future user turns.
- Use task mode for typed coordinator-owned delegation.
- Disable parent/peer transfer on bounded task specialists.
- Add post-output domain invariant validation.
- Give each specialist a unique state namespace.
- Evaluate trajectory and Agent author, not only final answer.
- Treat request count as a proxy until real token, latency and cost telemetry
  exists.

## Verification

Commands:

```bash
make verify
make verify-multi-agent
```

Current Lab 03 results:

- 7 dependency-free domain tests;
- 10 ADK-backed specialist lifecycle tests;
- 35,991-byte deterministic JSON evidence bundle.

## Limits

- No live model routing or response quality measurement.
- No token, latency or monetary telemetry.
- No concurrent shared-state writes.
- No durable task service or process-loss recovery.
- No remote A2A specialist.
- No nested task hierarchy; the pinned upstream case is expected to fail.
- No context cache configuration comparison across transferred Agents.

## Roadmap Effect

Phase 3 local exit gate is satisfied:

- responsibilities and delegation lifecycles are explicit;
- failure, overlap and state-conflict behavior are tested;
- function and Workflow alternatives remain visible.

Phase 4 can now classify data ownership across prompt context, Session state,
artifacts and long-term memory. It must preserve the specialist isolation rules
observed here.
