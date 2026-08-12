# Lab 07 Observations

Observed with pinned `google-adk 2.6.3` and scripted models.

## Boundary Enforcement

| Variant | External payment effects | Observation |
|---|---:|---|
| Prompt-only confirmation | 1 | Model called the tool despite the instruction |
| Complete plugin | 0 | `before_tool` returned a policy result before execution |
| Output-only plugin | 1 | `after_tool` hid the result after execution |

Unsafe user input was replaced before request assembly and hard-stopped by
`before_model`. Unsafe tool output was absent from the second model request.
Unsafe model output was replaced before its Event was persisted.

The pinned ADK 2 Agent Runner called `before_run_callback`, but this execution
path ignored its returned early-exit content. A sample-style
`on_user_message -> before_run` halt therefore did not stop the model in the
first experiment. The lab retains that observation and enforces the hard stop
at `before_model`.

## Approval Lifecycle

- First dynamic tool call emitted the original function call, a synthetic
  `adk_request_confirmation` call and a placeholder function response.
- Fresh Agent and Runner objects resumed the same invocation over the same
  Session service.
- Valid approval executed one payment and persisted the complete approval
  decision.
- Explicit rejection, expired approval, unauthorized approver and mismatched
  request hash each executed zero payments.
- Replaying the same confirmation in a later run entered the tool again.
  The external ledger observed two execution attempts but retained one effect.

Workflow `RequestInput` paused a node-level graph and resumed downstream with
the same application validation and ledger contract.

## Credential Boundary

Runtime tests prove `request_credential` fails without a tool
`function_call_id` and records a credential request under that exact call ID.
The pinned `RemoteA2AAgent` additionally drops credential-shaped function
responses before forwarding; that remains source evidence because the lab
environment does not install the optional A2A client.

## Verification

- 7 dependency-free tests.
- 15 ADK-backed runtime tests.
- Two 65,971-byte evidence renders were byte-identical.
- SHA-256:
  `b8816d2ec4bd0ab44557a8deb0f0d1f67bd46382da876d0cb9c6a533d4776f61`.

## Limits

The Session service and ledger are in memory. Real approver authentication,
revocation, process-loss recovery, durable atomicity, streaming confirmation
and credential-provider integration remain production gates.
