# Deterministic Workflow Engineering

Status: pinned ADK 2.6.3 source analysis and local runtime experiments complete.

## Question

When should ordering, fan-out, retry, loop termination and resume remain code
controlled rather than delegated to an LLM?

## Hypothesis

Use a deterministic Workflow when a transition can be expressed as an
observable invariant:

- step B must follow step A;
- both analyses must complete before synthesis;
- a retry is legal only for named transient failures;
- a loop must approve or take an explicit exhaustion path;
- a human response must resume the interrupted node;
- one output event must represent one logical result.

An LLM may still execute a node. It should not own graph invariants merely
because the node happens to involve language.

## Version Boundary

At the pinned `google/adk-python` commit:

- `SequentialAgent`, `ParallelAgent` and `LoopAgent` are deprecated in favor of
  `Workflow`;
- all three legacy classes still execute and contain resumable agent-state
  logic;
- `Workflow` is a `BaseNode` graph runtime, not a renamed composite Agent;
- the deprecation text states that `Workflow` cannot yet be used as an
  `LlmAgent` sub-agent.

Therefore migration is architectural. Replacing a class name without comparing
events, branches, failure ownership and resume behavior is not a valid upgrade.

## Two Control Models

### Legacy Composite Tree

```text
SequentialAgent
  -> child Agent
  -> ParallelAgent
       -> child Agent A
       -> child Agent B
  -> LoopAgent
       -> reviewer
       -> exit checker
       -> reviser
  -> final child Agent
```

The container calls child `BaseAgent.run_async()` generators. Coordination is
expressed by nesting Agent objects.

### Graph Workflow

```text
START -> intake -> [facts, risks] -> JoinNode -> compose -> review
                                                        | approved -> finalize
                                                        | revise   -> revise -> review
                                                        | exhausted -> reject
```

The graph compiles edges into nodes and triggers. Each run gets a node path such
as:

```text
graph_research_pipeline@1/review@2
```

The path identifies workflow, node and run ID without relying on prose or Agent
author alone.

## Source Facts

### Sequential

`SequentialAgent` persists `current_sub_agent` when resumability is enabled. On
resume it starts from that child rather than index zero. If a named child was
removed, it logs a warning and restarts from the beginning.

### Parallel

`ParallelAgent` copies the invocation context and assigns an isolated branch to
each child. Child generators run concurrently, while each child's own events
remain ordered. A sibling exception cancels the composite run.

### Loop

`LoopAgent` persists `current_sub_agent` and `times_looped`. It exits when:

- a child Event has `actions.escalate`;
- `max_iterations` is reached;
- the invocation pauses.

Reaching `max_iterations` does not itself produce a domain rejection result.
The next parent step can still execute unless application logic checks the
invariant.

### Graph Construction

The graph validator rejects:

- duplicate node names and duplicate edges;
- missing or unreachable `START`;
- incoming edges to `START`;
- unconditional cycles;
- incompatible static input/output schemas;
- non-`START` incoming edges to chat-mode Agents.

Conditional routed cycles are allowed because they have an explicit decision
edge.

### Graph Execution

`Workflow` uses a trigger buffer and one `NodeRunner` per scheduled node.
Completion can:

- emit output;
- emit a route;
- trigger one or more successors;
- wait for all predecessors through `JoinNode`;
- enter `WAITING` on an interrupt;
- enter `FAILED` on an exception.

The mutable orchestration loop state is not durable. Resume reconstructs child
executions, outputs, routes, interrupts, branches and ordering from Session
Events.

### Retry

`BaseNode.retry_config` supports:

- maximum attempts;
- initial/max delay;
- exponential backoff;
- jitter;
- exception-name allowlists.

Each failed attempt emits an error Event. The pinned source explicitly warns
that retry count is not persisted across resume. A retried operation therefore
still needs idempotency and a durable attempt policy when crossing process
boundaries.

### Output Ownership

A dynamic child called through `ctx.run_node()` emits its own output. If the
parent simply returns the same value, two output Events exist. Passing
`use_as_output=True` delegates output ownership and extends
`node_info.output_for` through the ancestor chain.

## Lab 02 Baseline

Both implementations call the same pure functions:

- normalize topic;
- collect facts and risks;
- compose;
- review;
- revise;
- finalize.

They produce the same final state after two reviews and one revision.

| Evidence | Legacy composite | Graph Workflow |
|---|---:|---:|
| Yielded Events | 34 | 28 |
| Stored Events including user input | 35 | 29 |
| Review executions | 2 | 2 |
| Revisions | 1 | 1 |
| Final result | Same approved brief | Same approved brief |

The count difference is not a quality score. Legacy resumability adds container
and child agent-state Events; graph resumability adds node-status checkpoints.
Consumers should classify Events rather than compare raw volume.

## Fan-Out and Join

The graph trace assigns:

```text
facts@1
risks@1
```

as separate branches, then emits one `analysis_join@1` output containing both
predecessor outputs. The next node starts only after both predecessors are
`COMPLETED`.

The legacy `ParallelAgent` also isolates child branches, but the following
compose Agent reads agreed Session state keys. There is no typed join payload.
This makes state-key ownership part of the hidden integration contract.

Decision:

> Prefer an explicit join payload when downstream correctness depends on a
> complete set of parallel results. Use shared state only when its ownership,
> conflict policy and missing-key behavior are independently enforced.

## Loop Exhaustion

Intentional break:

- require 99 reviews;
- permit only two iterations;
- let an unsafe legacy finalizer ignore approval.

Observed:

| Runtime | Result |
|---|---|
| Legacy `LoopAgent` | Stops at `max_iterations`, then parent sequence finalizes an unapproved draft |
| Graph `Workflow` | Review node routes `exhausted` to an explicit rejection terminal |

`max_iterations` is a safety bound, not a successful business outcome.

## Failure and Retry

A transient child failure produced:

| Evidence | Legacy composite | Graph Workflow |
|---|---|---|
| Attempts | 1 | 2 |
| Framework retry | None | `RetryConfig(max_attempts=2)` |
| Error Event | None from the direct child failure | One node-path error Event |
| Terminal exception | Propagated | Recovered |
| Downstream execution | No | Successful terminal output |

This does not mean every graph node should retry. Retry belongs at the narrowest
layer that knows:

- whether the operation is idempotent;
- which exceptions are transient;
- whether an attempt consumed quota or caused a side effect;
- whether the caller has an outer retry budget.

## Missing State

A `FunctionNode` requiring `draft: str` ran without that state key.

Observed:

```text
ValueError:
Missing value for parameter "draft" of function "consume_draft".
It was not found in state and has no default value.
```

The error Event carried:

```text
missing_state_pipeline@1/consume_draft@1
```

Typed schemas validate declared keys and values, but declaration does not make
an optional value exist. Required data flow still needs a predecessor/output
contract.

## Duplicate Output

Without delegation:

```text
duplicate_output_pipeline@1/parent@1/child_output@1
duplicate_output_pipeline@1/parent@1
```

Both emitted `shared-output`.

With `use_as_output=True`, only the child Event remained and its `output_for`
listed child, parent and Workflow paths. Event consumers can then count one
logical result without custom deduplication.

## Resume Comparison

Both experiments:

1. performed an externally visible `prepare` effect;
2. paused on `approve-brief-1`;
3. discarded the Runner and root object;
4. created fresh objects over the same `InMemorySessionService`;
5. submitted the matching function response.

### Graph Observation

- external ledger remained `["prepared"]`;
- the completed `prepare@1` output was re-surfaced during replay;
- `prepare` code did not execute again;
- `approval@1` reused its run ID;
- `finalize_approval@1` completed.

Replay evidence must not be mistaken for a repeated side effect.

### Legacy Observation

- external ledger also remained `["prepared"]`;
- Runner routed the function response directly to the interrupted leaf Agent;
- approval state was written;
- the parent `SequentialAgent` tail did not naturally continue;
- no final result was written.

This is a pinned-runtime observation for this deterministic custom-Agent case.
It aligns with upstream runner tests that mark some legacy composite resume
paths as expected failures during the V2 transition. It is not a claim that no
legacy Agent can ever resume.

## Sample Evidence

| Study unit | Design evidence | Engineering challenge |
|---|---|---|
| R03 `llm-auditor` | Small critic then reviser sequence | Both nodes are Agents even though ordering is deterministic |
| R05 `deep-search` | Sequence plus bounded refinement loop and escalation checker | Loop success and max-iteration exhaustion need separate outcomes |
| R04 `global-kyc-agent` | Nested parallel/sequential composition | Monkey-patches private `_run_async_impl` and helper functions |
| R13 `ambient-expense-agent` | Graph routing plus human approval | In-memory approval state is not durable production recovery |

R04 is a migration warning: if a sample must replace private scheduler methods
to alter final-event behavior, the extension point is not stable enough for a
reusable blueprint.

## Decision Guide

Use code/Workflow control for:

- regulatory or monetary gates;
- fixed prerequisite order;
- complete fan-in requirements;
- bounded retries and timeouts;
- explicit loop exhaustion;
- HITL pause/resume;
- idempotency and output ownership.

Use an LLM decision inside a node for:

- interpreting ambiguous user intent;
- drafting or classifying unstructured content;
- choosing among semantically equivalent strategies;
- proposing a route that deterministic policy then validates.

Do not use an LLM router merely to reproduce an `if`, ordered list or bounded
loop.

## Migration Checklist

- Inventory every legacy composite and child Agent.
- Classify each child as model reasoning, deterministic function or external
  effect.
- Make shared state keys explicit and typed.
- Replace parallel shared-state fan-in with a join contract where practical.
- Define success, rejection and exhaustion as different routes.
- Assign one retry owner and an idempotency key.
- Verify Event paths and output ownership.
- Test pause/resume with fresh runtime objects.
- Test graph changes against historical replay.
- Remove private runtime monkey patches before calling migration complete.

## Evidence Limits

Verified locally:

- deterministic sequence, fan-out/join and routed loop;
- legacy composite behavior on Python 3.10;
- graph validation;
- retry and terminal failure;
- missing state;
- duplicate output delegation;
- fresh-object Session replay and HITL resume.

Not yet verified:

- durable Session service after actual process loss;
- retry persistence across process boundaries;
- graph migration after node rename/removal;
- real LLM nodes, streaming and Task API;
- distributed side-effect idempotency;
- latency or cost under parallel model calls.
