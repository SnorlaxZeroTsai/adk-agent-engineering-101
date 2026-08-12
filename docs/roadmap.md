# Learning Roadmap

這份 roadmap 是 architecture dependency graph，不是 API chapter list。每個 phase
都必須完成：

```text
source -> design decision -> pattern -> experiment
       -> intentionally break -> observe -> document
```

Phase 0 固定 source snapshot；後續 phase 可以更新 upstream，但必須先記錄 diff，
不能悄悄改變既有結論。

## Learning Contract

每個 module 至少包含：

1. 固定 commit 與 source path。
2. 一個可被證偽的 hypothesis。
3. 最小可執行 baseline。
4. 一個 intentional break 或 boundary violation。
5. observable evidence：test、event trace、eval score、latency、cost 或 policy result。
6. source fact、inference、open question 的分離。
7. 更新 README、roadmap、learning note 與 `PROJECT_STATE.md`。
8. 一個 logical commit；large phase 可拆成 source note、lab、evaluation 三個 commits。

## Architecture Dependency Order

```text
Agent boundary
  -> Tool contract
  -> App / Runner / Session / Event
  -> deterministic Workflow
  -> state / context / artifacts
  -> long-term memory
  -> multi-agent delegation
  -> retrieval and RAG
  -> evaluation
  -> safety and HITL
  -> production lifecycle
  -> pattern catalog
  -> Agent Garden blueprint
  -> mini Agent Garden
```

The ordering is deliberate:

- Multi-agent design without tool and execution boundaries hides coupling.
- Memory without state/context ownership produces accidental data retention.
- RAG without evaluation only proves that a retriever can be called.
- Production templates before architecture understanding multiply an unknown
  design.
- A blueprint schema should be extracted from repeated implementations, not
  invented before them.

## Version Boundary

ADK 1.x and ADK 2.0 are separate evidence tracks:

- **ADK 2.0 current track:** authoritative `adk-python` runtime, graph
  `Workflow`, Task API, current `Agent` modes and event semantics.
- **ADK 1.x comparative track:** legacy `SequentialAgent`, `ParallelAgent`,
  `LoopAgent`, direct `AgentTool` and callback-heavy samples.
- A pattern is considered portable only after the same design intent is tested
  on both sides or explicitly marked version-specific.

No sample may be upgraded by only changing its dependency range. Migration must
compare behavior, event trace, state ownership, failure semantics and tests.

## Phase Plan

| Phase | Primary question | Required artifacts and experiment | Exit gate |
|---|---|---|---|
| 0. Repository reconnaissance | What evidence exists and how current is it? | Repository map, source lock, 15 study units, roadmap, project skeleton, reconnaissance note | Every conclusion has a source category; active/legacy and 1.x/2.0 boundaries are explicit |
| 1. ADK foundations | What is an Agent, Tool and runtime boundary? | `Agent`, tool and execution-model notes; small offline-first lab; event trace experiment | Can explain and test what model controls, what code controls and what persists |
| 2. Workflow engineering | When must control flow be deterministic? | Sequential, parallel, loop and ADK 2.0 graph Workflow labs | Equivalent tasks compared for trace, retry, failure and resumability |
| 3. Multi-agent systems | When is delegation better than a tool or workflow node? | Coordinator, transfer and single-turn specialist experiments | Responsibilities and state contracts remain explicit under failure |
| 4. State, context and memory | What belongs in prompt, session, artifact or long-term memory? | Context-budget and cross-session recall labs | Retention, isolation, compaction and deletion behavior are testable |
| 5. RAG engineering | Who owns ingestion, retrieval and citation quality? | Managed Search and explicit Vector Search comparison | Same corpus has retrieval, groundedness, latency and cost evidence |
| 6. Evaluation | What observable behavior defines success? | Dataset, trajectory, tool-argument, response, safety and regression evals | A deliberately broken Agent fails a CI-style gate |
| 7. Safety and HITL | Where can policy block, redact, confirm or resume? | Callback/plugin coverage matrix and approval lab | Model/tool I/O and credential boundaries have tested enforcement |
| 8. Production engineering | How does a working Agent become an operated service? | Starter Pack/Agents CLI render diff, deployment topology, telemetry and rollback notes | Environment/config/secrets/eval/deploy concerns are independently replaceable |
| 9. Pattern catalog | Which designs recur and under what forces? | Normalized pattern cards with counterexamples | Each pattern has context, forces, implementation, failure modes and evidence |
| 10. Agent Garden reverse engineering | What makes a sample discoverable and reusable? | Recipe and template contract comparison | Catalog metadata is distinguished from executable blueprint metadata |
| 11. Blueprint schema | What is the smallest enforceable reusable contract? | Versioned schema, examples and invalid cases | Schema validates architecture, runtime, policy, eval and lifecycle without encoding one app |
| 12. MVP architecture | What platform components are justified? | ADRs, component model, storage and extension boundaries | Every component traces to observed repeated need |
| 13. Mini Agent Garden | Can the abstractions create, validate and evolve real Agents? | CLI, registry, scaffold, validate, test and upgrade flow | At least three different blueprints scaffold and pass contract tests |

## Current Progress

| Module | Status | Evidence |
|---|---|---|
| Phase 0 | Complete | Repo map, source lock, 15 study units and reconnaissance note |
| Phase 1A Agent boundary | Complete for offline/scripted scope | Agent note and deterministic counterexamples |
| Phase 1B Tool boundary | Complete for local/source scope | Generated schemas, ToolContext state and failure recovery |
| Phase 1C Execution model | Local baseline complete | Success, continuation, missing-session and failure traces; invocation resumption deferred |
| Phase 2 Workflow engineering | Next | Legacy composite versus ADK 2.0 Workflow lab |

The Phase 1 live-model gate remains open, but it is not a dependency for
deterministic Workflow semantics.

## Near-Term Modules

### Phase 1A: Agent Boundary

Status: complete for offline and scripted-model scope.

Sources:

- `BaseAgent`, `LlmAgent`, `App`
- representative R01 and R02

Hypothesis:

> A useful Agent is a named event-producing decision boundary; business
> capabilities remain narrow deterministic tools, and application-wide services
> remain outside the Agent object.

Experiments:

- Build an order-support Agent with two structured tools.
- Inspect the source contract without importing ADK.
- Break it by replacing typed tools with one unstructured request handler.
- Break it by moving deterministic shipping rules into instruction text.
- Observe contract visibility and deterministic test coverage.

Exit evidence:

- `docs/foundations/agent.md`
- `labs/01-agent-basics`
- baseline and broken-case observations

### Phase 1B: Tool Boundary

Status: complete for FunctionTool and source-level tool-family scope. MCP,
built-in provider behavior and credential/confirmation recovery remain later
integration gates.

Sources:

- `FunctionTool`, built-in tools, MCP tooling, `ToolContext`
- R02, R06 and R07

Questions:

- What does the model actually see from a Python callable?
- Which errors should be returned as domain data versus raised as infrastructure
  failures?
- When may a tool read/write session state?
- When is a specialist an Agent, a tool, or a deterministic function?
- How do async behavior, confirmation and credentials affect the contract?

Required breakages:

- ambiguous parameter names;
- undocumented enum/domain constraints;
- raised domain error instead of structured result;
- synchronous blocking inside an async callback/tool path;
- hidden import-time network or configuration side effect.

### Phase 1C: Execution Model

Status: complete for non-streaming in-memory conversation behavior. Interrupted
invocation resumption remains a Workflow/HITL experiment.

Sources:

- `Runner`, `InvocationContext`, `Session`, `Event`

Experiments:

- Run with an in-memory session service and deterministic/fake model.
- Record emitted events, authors, actions, branch/node metadata and state deltas.
- Resume an invocation and verify which data survives.
- Inject a callback failure and a tool failure, then compare terminal events.

Exit gate:

> Given an observed event trace, explain which component produced every state
> transition and which service must persist it.

### Phase 2: Workflow Engineering

Comparative cases:

- R03: small ADK 1.x sequence.
- R05: sequence + loop + escalation.
- R04: private extension failure mode.
- R13: ADK 2.0 event-driven graph Workflow.

Experiments:

- Implement one research task with legacy composite agents and with 2.0
  `Workflow`.
- Hold prompts and tools constant.
- Compare deterministic path, fan-out, retry, termination, pause/resume and
  event observability.
- Force a child failure, missing state key, duplicate event and resume after
  process loss.

## Later Phase Design Questions

### Multi-Agent

- Does the specialist need independent model reasoning, identity and history?
- Can a normal function or Workflow node provide the same isolation?
- Who owns shared state and conflict resolution?
- Is transfer conversational, single-turn, remote A2A or deterministic routing?

### Context and Memory

- What is stable instruction versus volatile invocation context?
- Which state is user-, session-, app- or branch-scoped?
- When is an artifact preferable to prompt tokens?
- What is the write policy, recall metric, TTL and deletion path for memory?

### RAG

- Managed connector versus explicit ingestion ownership.
- Chunking and embedding versioning.
- Retrieval quality before generation quality.
- Citation fidelity, stale data, access control and deletion propagation.

### Evaluation

- Deterministic unit tests for tools and policy.
- Tool choice and argument accuracy.
- Trajectory/event sequence.
- Final response usefulness and groundedness.
- Safety, latency, token usage and monetary cost.
- Regression thresholds that block delivery.

### Safety and HITL

- Coverage matrix for model input/output and tool input/output.
- Deterministic rules versus LLM judge.
- Credential negotiation and least privilege.
- Approval persistence, expiry, replay and idempotency.
- Redaction before telemetry and memory writes.

### Production

- Configuration and secret boundaries.
- Session/memory/artifact service choices.
- Deployment target as an overlay.
- Trace schema, privacy, sampling and cost.
- CI/CD, migration, rollback and upgrade tests.
- Difference between generated convenience and enforceable governance.

## Pattern Catalog Contract

Each future pattern card under `patterns/` will use:

```yaml
name:
status: candidate | validated | version-specific | rejected
context:
forces:
decision:
implementation:
observable_contract:
failure_modes:
counterexample:
adk_versions:
source_evidence:
lab_evidence:
```

Candidate patterns are not promoted to `validated` from source reading alone.
They require at least one local implementation and one intentional break.

## Agent Garden Deliverable Sequence

1. Compare `adk-samples/manifest.yaml`, Starter Pack template config and
   `agents-cli-manifest.yaml`.
2. Identify catalog-only, scaffold-time, runtime and governance fields.
3. Write three materially different blueprint examples.
4. Design schema only after examples expose common fields.
5. Validate invalid blueprints and migration between schema versions.
6. Implement registry discovery, scaffold rendering and project validation.
7. Add eval-gate and upgrade commands.
8. Test whether a new architecture can be added without modifying core CLI
   logic.

## Roadmap Revisions

| Date | Previous assumption | Source-driven revision |
|---|---|---|
| 2026-08-12 | Agent Starter Pack is the current production baseline | Keep it as template-composition evidence; use Agents CLI for active lifecycle work |
| 2026-08-12 | `adk-samples` is one homogeneous gallery | Separate active recipes, frozen legacy samples, skills contract and transitional duplicates |
| 2026-08-12 | Workflow samples share one runtime model | Teach ADK 2.0 first and preserve an explicit ADK 1.x comparative track |
| 2026-08-12 | Existing manifest can seed the full blueprint directly | Treat manifest as minimal catalog/ownership metadata; derive runtime and governance fields experimentally |
| 2026-08-12 | Every yielded Event can be treated as message content | Error events may have no content; consumers must inspect event kind, error and action fields first |

## Milestone Tracking

Current milestone and continuation context live in
[`PROJECT_STATE.md`](../PROJECT_STATE.md). Phase completion requires:

```text
make verify
```

plus the phase-specific behavioral/evaluation gate. Passing structural checks
alone never proves an Agent design.
