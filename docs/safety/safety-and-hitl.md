# Safety and HITL: Enforcement Before Irreversible Effects

Research snapshot: 2026-08-12. Runtime conclusions are pinned to
`google/adk-python@a56f6e1`; recipe conclusions are pinned to
`google/adk-samples@4b5dd77`.

## Question

A prompt can ask a model to follow policy, wait for approval or avoid secrets.
That does not identify the boundary that can actually prevent an unsafe model
request, tool call, result disclosure or external side effect.

The engineering questions are:

> Which hook can still block each unsafe transition, and what authorization
> data must survive pause, resume and replay before a consequential action is
> allowed?

## Hypothesis

> Policy must execute before the unsafe transition it governs. Human approval
> is an application-owned authorization record transported by the Agent
> runtime, not a natural-language instruction and not merely a boolean.

## Enforcement Surfaces

### App Plugins and Agent Callbacks

`App.plugins` apply across the Agent tree. Agent callbacks belong to one Agent.
For model and tool hooks, the pinned runtime runs plugins before Agent
callbacks. Within plugins:

- registration order is execution order;
- the first non-`None` result short-circuits later plugins;
- a plugin exception becomes a `RuntimeError`;
- notification-only error callbacks continue after plugin failures.

This creates an ownership rule: global invariants belong in a plugin, while a
single Agent's local adaptation can remain an Agent callback. Plugin order is
policy composition, not incidental configuration.

### Coverage Matrix

| Boundary | Enforcing hook | What a non-`None` result does |
|---|---|---|
| User input | `on_user_message_callback` | Replaces input before Session append and model request assembly |
| Run/model entry | `before_model_callback` | Bypasses the model with a controlled response |
| Model output | `after_model_callback` | Replaces response before the Event is persisted |
| Tool input | `before_tool_callback` | Returns a function result without calling the tool |
| Tool output | `after_tool_callback` | Replaces the result before the next model request |
| Tool failure | `on_tool_error_callback` | Applies an explicit recovery result |
| Run/Event observation | `on_event`, error and after-run hooks | Observes or modifies supported lifecycle output |

An `after_tool` filter protects the model and later persistence from a bad
result. It cannot undo a network request, payment or deletion already performed
inside the tool. Consequential-action policy therefore belongs in
`before_tool` and in the side-effect service itself.

### Pinned `before_run` Divergence

The safety-plugin recipe uses this sequence:

```text
on_user_message -> set Session flag
before_run -> return a refusal and halt
```

In the pinned ADK 2 Runner path exercised by Lab 07,
`run_before_run_callback` is awaited during setup but its return value is not
used as an early-exit result. The first experiment therefore still called the
model.

Lab 07 retains that observation and performs the hard stop in
`before_model_callback`, whose replacement response is respected. This is a
source/runtime compatibility finding, not a recommendation to assume every
Runner path ignores `before_run`.

## Tool Confirmation

`FunctionTool` supports static confirmation through
`require_confirmation=True`. A tool can also request dynamic confirmation with
`ToolContext.request_confirmation(hint, payload)`.

The dynamic lifecycle observed in Lab 07 is:

```text
model execute_vendor_payment function call
  -> tool requests confirmation and returns placeholder
  -> synthetic adk_request_confirmation function call
  -> placeholder execute_vendor_payment function response
  -> invocation pauses

user confirmation function response
  -> confirmation processor validates original name/arguments/history
  -> original tool is re-executed with ToolConfirmation
  -> actual function response
  -> model final response
```

The confirmation processor checks:

- the original function call exists in history;
- tool name and arguments match;
- the tool is registered;
- static or dynamic confirmation was required.

`ToolConfirmation` itself contains only:

- `confirmed`;
- `hint`;
- arbitrary `payload`.

It does not authenticate an approver, bind authorization to a request digest,
enforce policy version, check expiry or provide side-effect idempotency.

## Approval Envelope

Lab 07 carries this application-owned authorization in the confirmation
payload:

```text
approval_id
action_id
action_type
request_hash
approver_id
decision
policy_version
issued_at_epoch
expires_at_epoch
```

The tool validates every field before calling the payment ledger. The request
hash covers all consequential arguments. `action_id` is also the external
ledger idempotency key.

This separates three concerns:

1. ADK pauses and resumes the tool call.
2. Application policy decides whether the response authorizes this exact
   action.
3. The side-effect system ensures retries cannot create a second effect.

## Replay Behavior

The pinned confirmation processor drops a consumed confirmation while
processing later model steps in the same run. It is not a durable cross-run
replay ledger.

Lab 07 resubmitted the same confirmation response in a later run:

- the tool was entered again;
- the payment ledger received a second attempt;
- the ledger retained exactly one external effect.

Framework pause/resume deduplication and business idempotency are different
contracts. A production action needs both.

## Workflow `RequestInput`

ADK 2 graph Workflow has a separate node-level HITL surface. Yielding
`RequestInput` creates an `adk_request_input` function call with:

- an interrupt ID;
- display message;
- optional payload;
- optional response schema.

On resume, the response becomes node output and downstream execution
continues. With `rerun_on_resume=True`, a node can instead inspect
`Context.resume_inputs`.

Choose the surface by ownership:

| Need | Surface |
|---|---|
| Confirm one model-selected tool call | `ToolConfirmation` |
| Pause deterministic business process between nodes | `RequestInput` |
| Obtain external credentials for one tool call | `request_credential` |

Both approval surfaces still require application identity, scope, expiry and
idempotency policy.

## Credential Boundary

`Context.request_credential` requires a `function_call_id` and stores the
request under that call. Callback contexts must use the credential service
instead of pretending to be a tool call.

The pinned `RemoteA2AAgent` also drops credential function responses and
credential-shaped `AuthConfig` payloads before remote forwarding. Live
credential acquisition was not exercised because it requires provider and
optional A2A integration setup.

Credential negotiation proves possession of a credential. It does not prove
human approval for a business action, and approval payloads must never carry
raw credentials.

## Lab 07 Evidence

| Experiment | External effects |
|---|---:|
| Prompt-only confirmation | 1 |
| Complete plugin with `before_tool` | 0 |
| Output-only plugin | 1 |
| Valid dynamic approval | 1 |
| Explicit rejection | 0 |
| Expired approval | 0 |
| Unauthorized approver | 0 |
| Mismatched request hash | 0 |
| Same confirmation replay | 1 effect, 2 ledger attempts |

Additional observations:

- unsafe user input reached zero model calls through `before_model`;
- unsafe tool output was absent from the second model request;
- unsafe model output was replaced before persistence;
- fresh Agent, Workflow and Runner objects resumed over one Session service;
- Workflow `RequestInput` completed the same validated payment contract;
- prompt-only safety failed the six-case release gate.

## Limits

- Session and ledger storage are in memory.
- Fresh objects do not prove recovery after process or storage failure.
- Approval UI authentication, revocation and two-person rules are not present.
- Session checkpoint and side-effect commit are not atomically coordinated.
- Live/streaming FunctionTool confirmation is unsupported in the pinned
  implementation.
- No live judge, Model Armor service or credential provider was called.

## Primary Sources

- ADK `BasePlugin`, `PluginManager`, Runner and LLM/tool flow hooks
- ADK `FunctionTool`, `ToolConfirmation` and confirmation request processor
- ADK `RequestInput` and Workflow HITL utilities/tests
- ADK `Context.request_credential` and `RemoteA2AAgent`
- `safety-plugins` recipe
- `ambient-expense-agent` recipe
- [`../../labs/07-safety-hitl`](../../labs/07-safety-hitl/)
