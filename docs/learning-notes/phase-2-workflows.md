# Phase 2 Learning Note: Deterministic Workflow Engineering

Date: 2026-08-12

## Questions

1. What do legacy composite Agents and graph `Workflow` actually control?
2. How do sequence, fan-out, loops and joins appear in Events?
3. Who owns retries, exhaustion and output deduplication?
4. What survives a fresh Runner/root-object resume?

## Hypotheses

1. Equivalent deterministic business rules can produce the same result through
   both runtimes, but their control and observability contracts differ.
2. A loop bound is not a success condition.
3. Node-local retry is safer than opaque whole-pipeline retry when exception and
   idempotency policies are explicit.
4. Graph replay can avoid re-executing completed side effects while still
   re-surfacing their output Events.
5. Legacy composite resume cannot be assumed equivalent to graph rehydration.

All five are supported within the local limits below.

## Primary Sources

Pinned runtime:

```text
google/adk-python
a56f6e13ae38296b608808c7a3b37efe4b8c862e
google-adk 2.6.3
```

Studied symbols:

- `SequentialAgent`, `ParallelAgent`, `LoopAgent`;
- `Workflow`, `Graph`, `BaseNode`, `FunctionNode`, `JoinNode`;
- `NodeRunner`, `NodeState`, `RetryConfig`;
- replay and rehydration utilities;
- R03, R04, R05 and R13 sample implementations.

Exact links are in
[`references/source-index.md`](../../references/source-index.md).

## Experiment Design

One pure domain core supplies:

- topic normalization;
- deterministic facts and risks;
- draft composition;
- review and revision;
- approval-enforced finalization.

Two adapters wrap those rules:

```text
legacy:
SequentialAgent -> ParallelAgent -> LoopAgent

current:
Workflow -> fan-out -> JoinNode -> routed loop
```

No LLM or cloud service participates. This isolates runtime control semantics
from model quality.

## Results

### Equivalent Happy Path

Both variants reached the same final approved brief:

- two reviews;
- one revision;
- identical final state.

Trace size:

| Runtime | Yielded | Stored including user input |
|---|---:|---:|
| Legacy | 34 | 35 |
| Graph | 28 | 29 |

The graph trace additionally exposed branch and run identity:

```text
facts@1
risks@1
review@1 -> route=revise
review@2 -> route=approved
```

### Loop-Limit Break

With `required_reviews=99` and a limit of two:

- the unsafe legacy pipeline fell through and wrote
  `status=unsafe_unapproved`;
- the graph routed to `status=rejected`,
  `reason=review_limit_exhausted`.

Lesson:

> A technical iteration cap must have a domain-visible exhausted outcome.

### Retry

The same transient exception produced:

```text
legacy: 1 attempt -> exception, no error Event
graph:  1 failed attempt Event -> local retry -> success on attempt 2
```

The graph error Event named:

```text
graph_retry_pipeline@1/flaky_fetch@1
```

Retry attempt count was kept as harness metric, not injected into Session state.

### Missing State

The graph emitted a `ValueError` Event and propagated the exception when a
required function parameter was absent. The message named parameter, function
and state source. This is more actionable than a downstream `KeyError`, but it
does not eliminate the need for data-flow tests.

### Duplicate Output

Returning a dynamic child's output from its parent produced two Events.
`use_as_output=True` reduced them to one and recorded all ancestor owners in
`output_for`.

### Resume

The external prepare ledger stayed at one entry in both variants.

Graph:

- re-surfaced prior prepare output;
- did not repeat prepare code;
- resumed approval;
- ran finalization.

Legacy:

- resumed the interrupted approval leaf;
- wrote approval state;
- did not continue the parent sequence tail.

The experiment used fresh Runner and root objects, but retained the same
in-memory service. It proves event-driven object rehydration, not durable
database recovery.

## Source-to-Experiment Corrections

Initial assumption:

> Legacy composite Agents have no resumability.

Correction:

Their source contains agent-state checkpoints and resume indices. The real
difference observed is not "resume versus no resume"; it is graph-owned
rehydration versus legacy Runner/leaf routing and composite continuation
behavior.

Initial assumption:

> Replayed output means a completed node ran twice.

Correction:

The graph resume trace yielded `prepare@1` output again while the external
ledger remained unchanged. Replay and execution must be measured separately.

## Architecture Decisions

- Keep deterministic domain functions independent of either ADK runtime.
- Treat legacy composites as migration evidence, not new-project defaults.
- Require explicit rejection/exhaustion routes.
- Use typed join payloads for required fan-in.
- Keep retry scope local and exception-specific.
- Keep retry counters out of business Session state unless they are a real
  domain or operational contract.
- Delegate dynamic output ownership explicitly.
- Use node paths and run IDs as trajectory evidence.
- Test resume with fresh runtime objects and an external side-effect ledger.
- Require idempotency even when replay skips completed nodes.

## Verification

Commands:

```bash
make verify
make verify-workflows
```

Current results:

- 20 dependency-free tests across Labs 01 and 02;
- 12 ADK-backed Workflow tests;
- all comparison traces render as JSON without model or cloud credentials.

## Limits

- `InMemorySessionService` is retained across the simulated restart.
- The legacy resume result uses deterministic custom `BaseAgent` leaves, not a
  real provider-backed `LlmAgent`.
- Retry delays are zero and no quota-consuming external service is called.
- Parallel nodes do not make real model calls, so latency/cost trade-offs remain
  unmeasured.
- Task API, streaming and graph schema migration remain open.

## Roadmap Effect

Phase 2 local exit gate is satisfied for deterministic runtime semantics.

Phase 3 can now compare:

- deterministic function or graph node;
- specialist as single-turn Agent;
- conversational transfer;
- coordinator-selected delegation.

The next experiment must hold the specialist capability constant and vary only
the delegation boundary.
