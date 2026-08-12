# Evaluation Engineering: From Scores to Release Decisions

Research snapshot: 2026-08-12. ADK runtime conclusions are pinned to
`google/adk-python@a56f6e1`; lifecycle-tooling conclusions are pinned to
`google/agents-cli@5a306f8`.

## Question

An Agent can produce a fluent answer while calling the wrong tool, passing the
wrong arguments, leaking another user's memory, silently overwriting shared
state or citing evidence that no longer has identity.

The engineering question is:

> Which observable behaviors define success, how are they represented without
> losing evidence, and which failures must block delivery?

## Hypothesis

> A release gate should evaluate typed behavior per case before aggregating
> scores. Deterministic architecture contracts and probabilistic quality judges
> need separate provenance, thresholds and blocking policy.

## ADK Evaluation Model

### Dataset and Invocation

`EvalSet` groups `EvalCase` objects. Each case supplies exactly one of:

- a static `conversation`;
- a `conversation_scenario` driven by a user simulator.

A case can also initialize a Session, attach rubrics and name an expected final
Session state. Each `Invocation` stores user content, final response and
intermediate data.

ADK supports two intermediate-data forms:

- ordered tool uses, tool responses and intermediate sub-agent responses;
- `InvocationEvents`, a simplified Event projection.

The projection retains only `author` and `content`. It does not retain the full
runtime Event's state delta, route, node path, branch, isolation scope, error
fields or grounding metadata. Evaluation that needs those fields must preserve
them separately before reducing a trace to `InvocationEvents`.

### Metrics

The pinned runtime includes metrics for:

- exact/in-order/any-order tool trajectories;
- response match and response quality;
- safety and hallucination;
- rubric-based response and tool use;
- multi-turn task, trajectory and tool-use quality;
- custom metric functions.

`TrajectoryEvaluator` compares both tool name and exact argument mapping. It
scores each invocation as `0` or `1`, then averages the invocation scores for
the case.

This distinction matters. `LocalEvalService` marks a case failed when one of
its metric-level overall statuses fails, but an evaluator can already have
averaged multiple invocation results into that overall status. A threshold
below `1` can therefore allow one critical invocation failure to be offset by
other passing invocations.

The legacy `AgentEvaluator` performs another explicit mean across invocation
scores before comparing to a threshold. Neither average is a substitute for a
per-case policy such as "every authorization check must pass."

### Result Status

`EvalCaseResult` retains:

- final case status;
- overall result for each metric;
- each metric result per invocation;
- generated Session ID and Session details.

`LocalEvalService` ignores `NOT_EVALUATED` metrics while combining overall
metric statuses. Lab 06 is intentionally stricter: a blocking metric requested
by a case must produce a passing result. Missing evidence is not success.

## Agents CLI Lifecycle

The pinned Agents CLI names three separate artifact stages:

```text
tests/eval/datasets
  -> artifacts/traces
  -> artifacts/grade_results
```

Although the stages share a provider SDK container, the populated fields and
ownership differ.

### Generate

`eval generate` runs each case against `/run_sse`, captures Agent events and
tool calls, and supports either a single prompt or an N+1 continued
conversation.

Generation has a partial-success contract:

- all cases succeed: artifact written, exit `0`;
- some cases succeed: only successes are written, exit `0`;
- zero cases succeed: no artifact, exit nonzero.

This is useful for collecting partial evidence, but it is not a completeness
gate. A release pipeline must compare generated case IDs with the input
dataset, or failed cases can disappear before grading.

### Grade

`eval grade` consumes populated traces and runs predefined or custom metrics.
It can:

- call provider evaluation services;
- run local custom Python metrics in process;
- submit remote code-execution metrics to a Vertex sandbox;
- write JSON and HTML grade artifacts.

Local custom metric source is compiled with `exec` and runs with the CLI
process privileges. Eval configuration is therefore executable code and needs
the same review, provenance and dependency controls as application code.

### Compare

`eval compare` recursively diffs two JSON documents and reports numeric deltas.
It does not classify a delta as a regression, apply thresholds or return a
blocking status.

A diff answers "what changed?" A release policy must separately answer "is
this change acceptable?"

## Lab 06 Contract

Lab 06 keeps the lifecycle explicit:

```text
EvalDataset
  -> Agent/Workflow execution
  -> TraceSet
  -> metric evaluators
  -> SuiteReport
  -> process exit 0 or 1
```

### Stage 1: EvalDataset

Each `EvalCaseSpec` defines:

- stable case and architecture-phase identity;
- enabled metrics;
- exact tool names, order and arguments;
- expected Event or Workflow-node trajectory;
- required and forbidden state paths;
- required and forbidden output fragments;
- forbidden model-input fragments;
- model-request budget;
- whether retrieval must be fully grounded.

### Stage 2: TraceSet

`ObservedRun` normalizes runtime evidence without a verdict:

- final observable output;
- ordered tool calls;
- trajectory;
- materialized state;
- model-visible input;
- error type and message;
- policy violations;
- retrieval/citation evidence;
- model-request count;
- explicitly labeled judge scores.

An observation has no `passed` field. This keeps generation independent from
grading and makes the same trace reusable under a changed policy.

### Stage 3: SuiteReport

The report retains:

- every per-case metric result;
- threshold, kind and blocking policy;
- failure reasons and relevant evidence;
- suite-level aggregation;
- one final release verdict;
- a process exit code.

## Metric Policy

| Metric | Evidence | Local policy |
|---|---|---|
| Runtime success | propagated exception and error Event | blocking, every case |
| Tool contract | exact ordered name and arguments | blocking, every applicable case |
| Trajectory | Event kinds or semantic Workflow stages | blocking, every applicable case |
| State contract | nested required values and forbidden paths | blocking, every applicable case |
| Output contract | required and forbidden deterministic fragments | blocking, every applicable case |
| Policy safety | explicit violations and forbidden model-visible data | blocking, every applicable case |
| Retrieval grounding | recall, citations, ACL, stale/deleted hits | blocking, every applicable case |
| Efficiency budget | model request count | blocking, every applicable case |
| Scripted response quality | local stand-in score from 1 to 5 | advisory, mean |

The scripted quality score is not presented as an LLM judge result. Its purpose
is to prove policy behavior: even a high quality score cannot override a
deterministic failure.

Latency, tokens and monetary cost are represented as future metric families,
not invented from local character counts.

## Cross-Architecture Dataset

| Case | Baseline | Broken variant | Primary blocking dimension |
|---|---|---|---|
| Agent tool round trip | order lookup, state delta, final answer | unhandled backend exception | runtime/tool/trajectory/state |
| Workflow exhaustion | graph routes to explicit rejection | legacy loop falls through to unsafe finalization | terminal output/trajectory/state |
| Bounded specialist | one task specialist owns typed result | two specialists overwrite one state key | tool/trajectory/state/cost |
| Memory isolation | Alice memory visible only to Alice | adapter returns Alice secret to Bob | policy safety |
| RAG grounding | result retains source ID/version/citation | provenance stripped before generation | output/retrieval/citation |
| Consequential action | scoped approval precedes one payment | prompt-only instruction executes without approval | trajectory/state/output/policy |

The baseline and broken trace sets contain the same six case IDs. A broken
case cannot disappear during collection.

## Results

### Baseline

All six cases passed every blocking metric. The release CLI returned status
`0`.

### Deliberate Breakage

All six cases failed:

| Case | Failed metric families |
|---|---|
| Agent | runtime, output, tool, trajectory, state |
| Workflow | output, trajectory, state |
| Multi-agent | output, efficiency, tool, trajectory, state |
| Memory | policy safety |
| RAG | output, retrieval grounding |
| Safety/HITL | output, trajectory, state, policy safety |

The report contained 20 per-case deterministic failures and eight failed
blocking aggregates, for 28 explicit blocking reasons.

The five broken variants that still produced fluent output each received a
scripted quality score of `5/5`. The failed Agent run received `1/5`. Their
mean was `13/3`, above the advisory threshold, so the judge aggregate passed
while the release correctly failed.

This is the required Phase 6 counterexample:

```text
judge aggregate: PASS
deterministic contract: FAIL
release: FAIL
process exit: 1
```

## Aggregation Rules

Use aggregation according to loss tolerance.

### `all_cases`

Use for:

- authorization and secret isolation;
- required tool side effects;
- state-machine terminal outcomes;
- data deletion and stale-version checks;
- required citations;
- schema and runtime completion.

One failure blocks the suite.

### `min`

Use when every score must exceed a numeric floor, but the metric naturally
returns a continuous score.

### `mean`

Use only when compensation across samples is intentional, such as:

- exploratory response quality;
- population-level style or preference metrics;
- noisy judge reporting with a separate critical-case gate.

Lab 06 includes a two-case counterexample where a mean of `0.5` meets the
aggregate threshold while one case scores `0`. The suite still fails because
the per-case blocking result is preserved.

## Failure Explanations

A CI gate should not return only a score. Each failed metric names:

- case;
- metric;
- expected contract;
- observed evidence;
- reason;
- threshold and blocking policy.

Examples:

```text
memory-user-isolation:policy_safety:
  runtime reported policy violation 'cross_user_memory_exposure'

rag-source-grounding:retrieval_grounding:
  citation recall is 0.000, expected 1
```

These messages identify the owning subsystem. They do not ask a developer to
infer an ACL or provenance failure from a generic quality number.

## CI Semantics

The executable contract is:

```bash
python scripts/run_eval_gate.py --variant baseline  # exit 0
python scripts/run_eval_gate.py --variant broken    # exit 1
```

`make verify-evaluation` asserts both outcomes. It also runs offline engine
tests, ADK-backed cross-phase tests and the deterministic evidence renderer.

The complete 90,166-byte evidence bundle rendered byte-for-byte identically in
two runs.

## Decision Rules

1. Preserve dataset, trace and grade artifacts as different types.
2. Require generated case IDs to match the input dataset.
3. Store enough runtime evidence for the metric being claimed.
4. Make deterministic invariants blocking by default.
5. Treat `NOT_EVALUATED` as failure for a required blocking metric.
6. Keep judge provenance, model, samples and threshold explicit.
7. Do not let an aggregate pass erase a failed critical case.
8. Separate comparison/reporting from release policy.
9. Run local custom metric code only from trusted reviewed sources.
10. Return a process status that CI can enforce.

## Limits

- The quality judge is scripted and deterministic.
- No live judge model, inter-rater study or confidence interval was measured.
- No latency, token or monetary-cost telemetry was collected.
- Streaming and partial Event aggregation remain untested.
- The normalized contract is local project code, not an ADK extension API.
- Durable trace storage, dataset version migration and production dashboards
  remain later production-engineering gates.
