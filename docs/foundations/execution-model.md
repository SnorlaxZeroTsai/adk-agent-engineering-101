# Foundation: Runner, Session and Event

Status: pinned-runtime success, continuation and failure traces complete.

## Question

Which object owns execution, what is persisted, and what evidence explains every
state transition in an ADK invocation?

## Runtime Vocabulary

The pinned `InvocationContext` source defines the hierarchy:

```text
invocation
  starts with one user message and ends with a final response
  may contain multiple agent calls

agent call
  one execution of an Agent
  may contain multiple LLM steps

LLM step
  one model call
  may emit tool calls and tool responses
  a tool result summarized by another model call creates another step
```

This matters for limits and telemetry. "One user turn" is not equivalent to
"one model call."

## Ownership Map

| Object | Owns | Does not own |
|---|---|---|
| `App` | Root Agent/node, plugins, compaction, cache and resumability config | Session storage implementation |
| `Runner` | Invocation orchestration, event processing, service wiring | Durable storage itself |
| `InvocationContext` | One invocation's IDs, current session, services, limits, branch/node state and event queue | Cross-process durability |
| `Context` / `ToolContext` | Delta-aware state and actions for the current node/tool | Committing storage independently |
| `Session` | Current persisted state plus ordered event history | Long-term memory semantics |
| `Event` | One observable message, action, output, error or workflow fact | Entire current state |
| Session service | Create/get/list/delete sessions and append events/state | Model reasoning |
| Artifact service | Versioned large/binary outputs | Conversation ordering |
| Memory service | Cross-session recall/write behavior | Current session event log |
| Credential service | Credential persistence and retrieval | User approval policy |

`Runner(app=..., session_service=...)` is the recommended construction path.
Legacy `app_name + agent` input is normalized into an `App`.

## Normal Invocation Sequence

For a chat Agent with one local tool:

```text
caller
  |
  | Runner.run_async(user, session, new_message)
  v
load existing Session
  |
append user Event
  |
build LlmRequest from visible session events + instruction + tools
  |
model emits function_call Event
  |
ADK invokes tool with ToolContext
  |
tool result + state_delta become function_response Event
  |
session service applies state delta and appends event
  |
next LlmRequest includes call + response
  |
model emits final text Event
  |
session service appends event; caller receives stream
```

The runtime's shared event queue has one Runner consumer. Non-partial events
wait until the Runner processes/persists them; partial streaming events can flow
without that persistence barrier.

## Lab 01 Observed Trace

Pinned ADK 2.6.3 with a deterministic `ScriptedModel` produced:

| Order | Author | Kind | Important data |
|---:|---|---|---|
| 1 | `user` | message | `status A100` |
| 2 | `order_trace_agent` | function call | `tracked_get_order_status(order_id="A100")` |
| 3 | `order_trace_agent` | function response | structured order result and `state_delta.last_order_id` |
| 4 | `order_trace_agent` | final message | `Order A100 is processing.` |

All four yielded non-partial events were stored in the Session. The persisted
state contains `last_order_id: A100`. The scripted model received two requests:

1. user content plus the tool declaration;
2. user content, model function call and matching function response.

The generated function-call ID is the correlation key between call and response.

## Session Is State Plus Evidence

`Session` contains:

```text
id, app_name, user_id, state, events, last_update_time
```

State represents the latest materialized values. Events explain how those values
changed. Keeping only state loses audit and trajectory evidence; keeping only
events forces replay for every read.

The session service applies `EventActions.state_delta` when appending an event.
In-memory service behavior is useful for tests but explicitly not safe for
multi-threaded production.

## State Scopes

ADK recognizes key prefixes:

| Key form | Intended lifetime |
|---|---|
| `key` | Current session |
| `user:key` | Same user across sessions in one app |
| `app:key` | All users/sessions in one app |
| `temp:key` | Current invocation only; removed before persistence |

`Context.state` writes both the live value and pending event delta. With a
declared state schema, unprefixed keys and values are validated; prefixed keys
bypass that schema in the pinned implementation.

Design rules:

- use the narrowest lifetime;
- do not put secrets in conversational state;
- treat user/app scope as shared mutable data;
- do not expect `temp:` state after the invocation;
- define conflict and migration behavior for durable implementations.

## Continuation Versus Resumption

These are different:

- **Conversation continuation:** a new invocation uses the same session ID and
  sees prior persisted events/state.
- **Invocation resumption:** the same invocation ID resumes interrupted
  workflow/node execution under configured resumability.

Lab 01 verifies continuation. It does not yet claim process-loss workflow
resumption. That belongs to the Workflow/HITL modules.

## Missing Sessions

By default, `Runner` does not silently create a missing session. It raises
`SessionNotFoundError`. `auto_create_session=True` changes this behavior.

Explicit creation is the safer default when:

- initial state must be validated;
- tenant/user authorization precedes session creation;
- an unknown ID may indicate a client bug;
- accidental typo-created sessions would fragment history.

## Event Contract

An `Event` can carry:

- model/user `content`;
- `function_call` or `function_response` parts;
- `actions.state_delta`, artifact delta, transfer, escalation, confirmation or
  credential requests;
- workflow `output` and `node_info`;
- `branch` and internal isolation metadata;
- model/provider error code and message;
- usage, grounding and custom metadata.

Do not infer a final response from `author` alone. Inspect content, calls,
responses, partial status, error fields and workflow metadata.

## Failure Semantics

### Unhandled Tool Failure

Observed:

```text
user event
function-call event
error event(error_code="RuntimeError")
RuntimeError propagates from Runner iteration
```

The error event is persisted before propagation. The caller still needs an
exception boundary; consuming the event stream is not sufficient.

### Recovered Tool Failure

With `on_tool_error_callback`, the same backend exception is translated to a
structured function response. The next model step runs and produces a final
message. The trace is:

```text
user -> function_call -> function_response(error result) -> final message
```

### Callback Failure

A raised `before_agent_callback` similarly produces a persisted error event and
then propagates the original exception. Agent error plugin callbacks are
notification-only and best-effort; they do not replace the exception.

Implication:

> Error events provide observability. Error callbacks define approved recovery.
> Neither eliminates the caller's responsibility to handle terminal failure.

## Partial Events

The Runner persists non-partial events. Partial streaming events are yielded but
not appended as independent durable history entries. A final consolidated event
is the persistence boundary.

Consumers must not:

- count partial chunks as completed turns;
- apply state deltas twice;
- assume every yielded event is durable;
- stop iteration early without understanding cancellation/cleanup effects.

## Execution Checklist

- Is the `App` explicit and are plugins app-scoped?
- Which concrete session/artifact/memory/credential services are wired?
- Is session creation explicit?
- How many model calls may one invocation perform?
- Which events are partial versus persisted?
- What state delta belongs to each function response?
- Can call/response IDs be correlated?
- What happens when the consumer stops early?
- Which exception types escape iteration?
- Which errors are recoverable by policy?
- Is conversation continuation being confused with invocation resumption?
- Can the trace be evaluated without parsing final prose?

## Evidence and Limits

Verified:

- actual Runner event ordering and persistence;
- actual FunctionTool state delta propagation;
- same-session continuation;
- missing-session failure;
- unhandled, recovered and callback failure traces.

Not yet verified:

- partial SSE consolidation;
- durable database-backed concurrency;
- workflow checkpoint/resume after process loss;
- artifacts, memory and credentials in the same trace;
- live-model usage/cost metadata.

Run:

```bash
make verify-adk
```

See [`references/source-index.md`](../../references/source-index.md#adk-runtime)
and [`labs/01-agent-basics`](../../labs/01-agent-basics/).
