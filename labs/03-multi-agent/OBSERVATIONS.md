# Lab 03 Observations

Pinned runtime: `google-adk 2.6.3` at
`a56f6e13ae38296b608808c7a3b37efe4b8c862e`.

## Baselines

All variants stored the same typed triage decision.

| Boundary | Model requests | Yielded Events | Stored Events |
|---|---:|---:|---:|
| Function node | 0 | 1 | 2 |
| `single_turn` node | 1 | 1 | 2 |
| Chat transfer | 2 | 3 | 4 |
| Task delegation | 3 | 5 | 6 |

These are scripted request counts, not token or monetary measurements.

## Ownership

- The deterministic node owns the rule and writes the result directly.
- The single-turn node receives only its bounded input.
- Transfer gives the specialist the reply and the following user turn.
- Task delegation gives the child an isolation scope keyed by function-call ID,
  returns a synthesized function response to the coordinator and lets the
  coordinator answer the user.

The transfer continuation used one coordinator request and two specialist
requests. Turn two produced only one specialist Event.

## Failure

An invalid task output used unsupported enum values. `FinishTaskTool` returned
a validation-error function response, the child made a second model request and
the corrected output completed normally.

A `RuntimeError` from the child model produced one error Event at the child node
path, propagated to the Runner caller and stopped the coordinator before its
second response. No fallback is implied by task delegation.

## Responsibility Overlap

Two task specialists had identical descriptions and parameter schemas. Both
were model-visible. The scripted coordinator selected B, while A was never
called. B returned a schema-valid but domain-wrong owner.

Typed I/O rejects malformed values. It does not resolve overlapping ownership
or enforce cross-field business policy.

## Shared State

Two task specialists wrote `triage_result` sequentially:

```text
risk_operations -> priority_support
```

The Session retained the second value. No warning or error Event represented
the overwrite. Shared keys therefore require one writer, namespacing or an
explicit merge node.

## Limits

- Scripted models remove routing uncertainty and do not measure answer quality.
- Request count is only a cost proxy.
- `InMemorySessionService` does not prove distributed isolation.
- Remote A2A, streaming, concurrent delegation and durable task recovery remain
  untested.
- The task-mode nested-delegation case is an expected failure in the pinned
  upstream E2E suite and is not exercised as a supported hierarchy here.
