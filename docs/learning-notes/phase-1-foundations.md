# Phase 1 Learning Note: Agent, Tool and Runtime Boundaries

Date: 2026-08-12

## Questions

1. What should an Agent own?
2. What does a tool actually expose to the model?
3. Which runtime object commits state and event history?
4. How do successful and failed invocations become observable?

## Hypotheses

1. Agent instructions should own semantic decisions, while deterministic
   business rules remain typed tools.
2. A Python function signature and docstring become part of the model contract.
3. Tool state mutation should appear as an event delta before it appears as
   persisted Session state.
4. Tool and callback exceptions should not silently become normal model text.
5. A same-session second turn is continuation, not workflow resumption.

All five are supported by source and local runtime evidence, with the limits
listed below.

## Source Method

The study used `google/adk-python` at:

```text
a56f6e13ae38296b608808c7a3b37efe4b8c862e
google-adk 2.6.3
```

Primary symbols:

- `BaseAgent`, `LlmAgent`, `App`;
- `BaseTool`, `FunctionTool`, `ToolContext`, `AgentTool`, `McpToolset`;
- `Runner`, `InvocationContext`, `Session`, `State`, `Event`, `EventActions`;
- `InMemorySessionService`.

The exact links live in
[`references/source-index.md`](../../references/source-index.md).

## Experiments

### 1. Offline Agent Boundary

Baseline:

- two read-only tools with explicit domain parameters;
- structured success and domain-error results;
- shipping rules kept in deterministic code;
- Agent instruction forbids unsupported mutations.

Breaks:

- replace both tools with `handle_order_request(query: str)`;
- raise `KeyError` for a normal not-found result.

Observed:

- the catch-all tool hides order ID, zone and weight from the schema;
- the raising variant removes the stable domain-error contract;
- 13 stdlib tests isolate deterministic behavior without importing ADK.

### 2. Generated Tool Declaration

Using the pinned `FunctionTool`, the shipping function generated:

- required `destination_zone` and `weight_kg`;
- a string enum for the three zones;
- a numeric weight;
- the complete function docstring as tool description.

A runtime-only `ToolContext` parameter was omitted from the model declaration.

### 3. Successful Runner Trace

A `ScriptedModel` emitted a fixed function call and final response. No network
or cloud credentials were involved.

Observed persisted sequence:

```text
user message
model function call
tool function response + state delta
model final message
```

The function call and response shared a stable call ID. The function-response
event carried:

```json
{"last_order_id": "A100"}
```

The Session subsequently materialized the same state.

### 4. Session Continuation

A second invocation reused the same session ID.

Observed:

- the third model request included prior user, call, response and final-message
  history;
- `last_order_id` remained in Session state;
- the Session contained six events after two invocations.

This proves conversation continuation for the in-memory service. It does not
prove checkpoint/resume of one interrupted invocation.

### 5. Tool Failure

Without recovery:

```text
user -> function_call -> error Event -> RuntimeError to caller
```

With `on_tool_error_callback`:

```text
user -> function_call -> structured function_response -> final model message
```

The callback is therefore a recovery policy, not only a logging hook.

### 6. Callback Failure

A `before_agent_callback` raised before any model request.

Observed:

- the user event was already persisted;
- an error event with `error_code="RuntimeError"` was persisted;
- zero model requests were made;
- the original exception propagated to the caller.

## Intentional Break That Found a Harness Bug

The first event summarizer assumed every Event had `content.parts`. Failure
events legally have `content=None`, so two runtime tests failed with an
`AttributeError` in the test harness.

Correction:

```text
classify error independently
check content before reading parts
```

Lesson:

> Event consumers must be schema-aware. Treating an event stream as a stream of
> chat messages destroys failure and workflow semantics.

## Architecture Decisions

- Keep pure domain functions separate from stateful ToolContext wrappers.
- Test the generated tool declaration, not only the Python signature.
- Use `App` as the explicit root configuration for Runner experiments.
- Create sessions explicitly; do not enable silent auto-creation in the
  baseline.
- Assert both yielded and persisted events.
- Correlate function calls and responses by ID.
- Keep expected domain errors as data.
- Allow exception recovery only through an explicit callback policy.
- Preserve a separate live-model gate; deterministic scripted responses cannot
  evaluate semantic tool choice.
- Pin runtime experiments to the same source commit used by the documents.

## Evidence

Commands:

```bash
make verify
make verify-adk
```

Current results:

- 13 offline tests pass;
- 8 ADK-backed runtime tests pass;
- success, continuation, unhandled failure, recovered failure and callback
  failure traces render without cloud access.

## Limitations

- `ScriptedModel` controls tool selection; it does not measure whether a real
  model selects the correct tool.
- `InMemorySessionService` does not prove concurrency or durable recovery.
- No partial streaming trace has been tested.
- No artifact, memory, credential or confirmation round trip has been tested.
- No latency, token or monetary cost evidence exists.
- MCP and provider built-in tools were source-studied but not executed.

## Roadmap Effect

Phase 1's local exit gate is satisfied: model-controlled, code-controlled and
persisted responsibilities can be explained from an event trace.

Phase 2 now compares:

- legacy deterministic composite Agents;
- ADK 2.0 graph `Workflow`;
- failure, parallelism, loop termination and resumability semantics.

See:

- [`../foundations/agent.md`](../foundations/agent.md)
- [`../foundations/tools.md`](../foundations/tools.md)
- [`../foundations/execution-model.md`](../foundations/execution-model.md)
- [`../../labs/01-agent-basics`](../../labs/01-agent-basics/)
