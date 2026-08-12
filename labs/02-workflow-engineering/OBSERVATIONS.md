# Lab 02 Observations

Pinned runtime: `google-adk 2.6.3` at
`a56f6e13ae38296b608808c7a3b37efe4b8c862e`.

## Happy Path

- Legacy and graph variants produced identical final state.
- Legacy yielded 34 Events and stored 35 including user input.
- Graph yielded 28 Events and stored 29 including user input.
- Graph fan-out used branches `facts@1` and `risks@1`.
- Graph review paths were `review@1` and `review@2`.

## Intentional Breaks

- Legacy `LoopAgent(max_iterations=2)` continued to an unsafe finalizer after
  failing approval.
- Graph review routed to `review_limit_exhausted`.
- Legacy transient child failure attempted once and propagated without a
  framework error Event.
- Graph transient node failure emitted one error Event and succeeded on attempt
  two through `RetryConfig`.
- Missing `draft` state named the parameter, function and node path.
- Dynamic output without delegation created two Events; `use_as_output=True`
  created one.

## Resume

- Both ledgers remained `["prepared"]`.
- Graph replay re-surfaced `prepare@1` output but did not execute the external
  effect twice.
- Graph resumed approval and finalized.
- Legacy Runner resumed the approval leaf and wrote approval state, but the
  parent sequence tail did not continue.

The in-memory Session service was retained across fresh Runner and root objects.
This is object-rehydration evidence, not durable process-recovery evidence.
