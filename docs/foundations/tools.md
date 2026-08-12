# Foundation: Tool Boundaries

Status: source contract and pinned-runtime experiments complete.

## Question

What does an ADK tool expose to the model, what may it access at runtime, and
where should errors, state and side effects be handled?

## Hypothesis

> A tool is an observable capability boundary. Its model-visible declaration
> should be narrow and semantic, while runtime-only context, credentials and
> persistence remain framework-injected.

This is stricter than "a Python function the model can call." The callable is
only one implementation form.

## Tool Families

| Family | Model-visible shape | Execution owner | Use when |
|---|---|---|---|
| Python callable / `FunctionTool` | Function declaration generated from name, docstring and type hints | Local ADK process | Domain operation is naturally a typed function |
| Custom `BaseTool` | Declaration or direct request mutation | Tool implementation | Capability needs custom declaration, auth or model-request behavior |
| `BaseToolset` | Dynamic set of tools | Toolset and external provider | Available capabilities depend on server, tenant or current context |
| Model built-in tool | Provider-native config, often no normal function declaration | Model provider | Provider performs search, code execution or grounding internally |
| Long-running tool | Normal function declaration plus deferred response semantics | Local/external worker and later response injection | Operation cannot finish in the current call |
| Single-turn sub-agent | Agent input/output schema exposed as a tool | ADK node runtime | Capability needs independent model reasoning but not a conversation transfer |

These families do not have interchangeable lifecycle or failure semantics.

## `FunctionTool` Pipeline

The pinned `FunctionTool` source performs this sequence:

1. Derive tool name from the callable and description from its docstring.
2. Build and cache a model declaration from the callable signature and type
   hints.
3. Exclude runtime-only context and `input_stream` from that declaration.
4. Convert JSON dictionaries into annotated Pydantic models when possible.
5. Filter unexpected arguments and inject `ToolContext` when the callable
   accepts it.
6. Return a structured framework error if required arguments are missing.
7. Request and evaluate confirmation when configured.
8. Invoke sync or async callables.
9. Mark a dictionary containing a truthy top-level `error` as a tool error for
   telemetry.

The declaration builder returns independent copies of a cached declaration, so
toolset prefixes and other consumers cannot mutate the shared cached object.

### What the Model Sees

For Lab 01, the actual ADK declaration for `estimate_shipping` contains:

```json
{
  "name": "estimate_shipping",
  "parametersJsonSchema": {
    "type": "object",
    "required": ["destination_zone", "weight_kg"],
    "properties": {
      "destination_zone": {
        "type": "string",
        "enum": ["local", "regional", "international"]
      },
      "weight_kg": {
        "type": "number"
      }
    }
  }
}
```

The complete docstring is also the description. The model does **not** see:

- the function body;
- `_SHIPPING_RATES`;
- injected `ToolContext`;
- service clients captured by the process;
- retries, transactions or authorization unless the description/schema says so.

Therefore parameter names and docstrings are executable interface design, not
cosmetic documentation.

## `ToolContext`

In the pinned source, `ToolContext` is an alias of the general mutable
`Context`. It exposes runtime services through a tool-specific call context.

| Capability | Observable result |
|---|---|
| `tool_context.state[key] = value` | Adds an `EventActions.state_delta` that the session service applies |
| artifact save/load/list | Delegates to the configured artifact service |
| memory search/write | Delegates to the configured memory service |
| credential load/save | Delegates to the credential service |
| `request_credential` | Adds a request keyed by function-call ID |
| `request_confirmation` | Adds a confirmation request keyed by function-call ID |
| `actions.skip_summarization` | Changes how the function response is processed |
| `actions.end_of_agent` or invocation termination controls | Alters execution, not domain data |

Runtime-only context is intentionally removed from the model declaration. A tool
that reads or writes context is no longer a pure function; its state contract
must be documented and tested separately.

Lab 01 keeps `get_order_status` pure and adds a runtime-only
`tracked_get_order_status` wrapper. The wrapper records `last_order_id` through
`ToolContext`; the emitted function-response event contains that state delta.

## Error Taxonomy

| Failure | Representation | Expected runtime behavior |
|---|---|---|
| Expected domain outcome | Structured tool result | Model can explain, ask for correction or choose another action |
| Missing model argument | Framework-generated `{"error": ...}` result | Model can retry with the required argument |
| Tool input rejected by business validation | Structured result with stable code | Deterministic tests and telemetry can classify it |
| Transient backend failure with approved recovery | Exception translated by `on_tool_error_callback` | Function-response event is emitted and the model may continue |
| Unhandled backend/programming failure | Exception | Error event is persisted/yielded, then exception propagates to caller |
| Unknown tool name | Tool lookup error, optionally recoverable by error callback | Never silently invoke a different capability |

The baseline result uses:

```json
{
  "ok": false,
  "error": {
    "code": "order_not_found",
    "message": "No order exists with ID Z999."
  }
}
```

Stable codes are for machines and evaluation; messages are for the model and
operators.

## Confirmation, Credentials and Side Effects

`FunctionTool(require_confirmation=...)` checks confirmation before invoking the
callable. Without a confirmation response, it records a request in event actions
and returns an error-like result telling the model that approval is required.

Design implications:

1. Confirmation belongs on the side-effecting operation, not only in prompt
   wording.
2. The function-call ID correlates request and later confirmation.
3. A confirmed retry must be idempotent or carry an idempotency key.
4. Credential negotiation and confirmation can pause a logical operation; the
   session service must survive that pause.
5. Read-only and mutating tools should not share ambiguous names.

## Sync, Async and Blocking Work

`FunctionTool` supports both sync and async callables. A sync callable may run
through a bound worker runner; otherwise it executes directly.

Rules:

- Use async for network and other naturally asynchronous I/O.
- Do not call `time.sleep` in an async callback or tool path.
- Apply explicit timeouts at the service boundary.
- Make retry ownership singular: tool client, callback or outer workflow, not
  all three.
- Do not retry non-idempotent mutations without an idempotency contract.
- Avoid import-time clients and network calls; they hide startup failures and
  make tests/configuration order-dependent.

## Built-In Tools

`GoogleSearchTool` demonstrates a tool that does not run local code and does not
need a normal function declaration. Its `process_llm_request` appends
provider-native Google Search configuration and rejects unsupported models.

Consequences:

- provider compatibility is part of the tool contract;
- local unit tests cannot prove provider-side behavior;
- combining built-ins with other tools may have provider-specific limits;
- a built-in tool's result may appear as grounding metadata rather than a
  normal local function response.

## MCP Toolsets

`McpToolset` opens or pools a connection to an MCP server, lists remote tools,
converts them to ADK tools, filters them and owns cleanup.

Source-derived concerns:

- stdio, SSE and streamable HTTP have different deployment boundaries;
- `tool_filter` limits model-visible capabilities;
- `tool_name_prefix` avoids collisions;
- header providers and credentials may be context/tenant-specific;
- tool-list caching is optional, TTL-based and identity-keyed;
- server tool ordering is normalized for stable context caching;
- cached lists do not observe server changes until expiry;
- `close()` releases sessions and clears the cache.

MCP reduces adapter code. It does not remove responsibility for trust,
authorization, schema review, latency, cleanup, version drift or confirmation.

## Agent as Tool

Direct `AgentTool` remains in source, but its own documentation discourages
using it for a normal inline specialist. Current guidance is:

```python
specialist = Agent(
    name="specialist",
    mode="single_turn",
    input_schema=...,
    output_schema=...,
)

coordinator = Agent(
    name="coordinator",
    sub_agents=[specialist],
)
```

The framework exposes the single-turn sub-agent as a tool and runs it in the
parent invocation/session. Direct `AgentTool` instead creates a nested Runner
with an in-memory child session, forwards selected state/artifacts and requires
explicit lifecycle cleanup.

Use an Agent rather than a function only when the capability needs independent
model reasoning, instruction, structured model output or node lifecycle.

## Intentional Breaks

Lab 01 keeps these counterexamples:

1. `handle_order_request(query: str)` hides all domain inputs in one string.
2. `get_order_status_or_raise` raises for an expected not-found outcome.
3. Runtime failure tests let an infrastructure exception escape without an
   error callback.
4. The recovery test translates the same exception into a stable tool result
   and proves the model can continue.

The recovery callback is not automatically "better." It is correct only when
continuing the conversation is an approved response to that backend failure.

## Checklist

- Can the capability be named as one action?
- Are required inputs explicit in the generated schema?
- Are enums and units represented structurally?
- Is the docstring sufficient for a model that cannot see implementation code?
- Is the tool read-only or side-effecting?
- Which state keys and services can it access?
- What is an expected domain error versus an exception?
- Who owns timeout, retry, idempotency and compensation?
- Does it require confirmation or credentials?
- Can two tenants observe different dynamic tools?
- Who closes toolset connections?
- What event/eval proves the right tool and arguments were used?

## Evidence and Limits

Verified against pinned ADK 2.6.3:

- generated Lab 01 function declarations;
- `ToolContext` exclusion from model schema;
- state delta on a function-response event;
- unhandled versus callback-recovered tool failure;
- sync deterministic behavior through existing offline tests.

Not yet verified:

- a real MCP server lifecycle;
- provider-side built-in search behavior;
- credential and confirmation resume across process loss;
- live-model tool-selection accuracy.

See [`references/source-index.md`](../../references/source-index.md#adk-runtime)
and [`labs/01-agent-basics`](../../labs/01-agent-basics/).
