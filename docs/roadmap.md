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
  -> multi-agent delegation
  -> state / context / artifacts
  -> long-term memory
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
| 5. RAG engineering | Who owns ingestion, retrieval and citation quality? | Managed Search and explicit Vector Search comparison | Same corpus has retrieval, groundedness and ownership evidence; live latency/cost is a separate gate |
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
| Phase 2 Workflow engineering | Local/runtime baseline complete | Equivalent business rules, routed loop, retry, failure, output and resume traces |
| Phase 3 Multi-agent systems | Local/scripted baseline complete | Function, single-turn, transfer and task lifecycles under failure and conflict |
| Phase 4 State, context and memory | Local/scripted baseline complete | Transient context, state scopes, artifact versions and memory isolation/deletion traces |
| Phase 5 RAG engineering | Local/scripted baseline complete | Same-corpus retrieval, citation, ACL, version and deletion evidence |
| Phase 6 Evaluation | Local/scripted gate complete | Six cross-phase cases, per-dimension failures and enforceable baseline/broken exit status |
| Phase 7 Safety and HITL | Local/scripted baseline complete | Enforcement coverage, confirmation lifecycle, approval envelope and replay-safe side effect |
| Phase 8 Production engineering | Offline baseline complete | Replaceable target renders, config/secret/telemetry policy, release promotion and rollback evidence |
| Phase 9 Pattern catalog | Complete | Seven normalized manifests, claim evidence, relations, decision boundaries and invalid-case gate |
| Phase 10 Agent Garden reverse engineering | Complete | Three metadata contracts, 33 field rows, nine discovery facts and 13 misleading-entry gates |
| Phase 11 Blueprint schema | Complete | Three architecture branches, 15 invalid cases and identity-preserving v0.1 migration |
| Phase 12 MVP architecture | Complete | Six components, 12 artifacts, six storage classes, nine trust boundaries and three lifecycle walkthroughs |
| Phase 13 Mini Agent Garden | Next | Implement discover, scaffold, validate, test and upgrade over the validated authority boundaries |

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

Status: complete for deterministic local/runtime scope. Durable Session
recovery, Task API, streaming and real model-node cost remain later gates.

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
- Force a child failure, missing state key, duplicate event and resume with
  fresh runtime objects; reserve actual process-loss proof for a durable
  Session service gate.

Observed:

- equivalent legacy and graph paths produced the same approved brief;
- graph fan-out and join exposed branch/run identity;
- explicit graph exhaustion prevented unsafe fall-through after a loop limit;
- graph node retry emitted an error Event and recovered on attempt two;
- `use_as_output=True` removed a duplicate dynamic output;
- fresh graph objects resumed and continued downstream without repeating an
  external effect;
- the pinned legacy custom-Agent resume reached the interrupted leaf but not
  the parent sequence tail.

Evidence:

- `docs/workflows/deterministic-workflows.md`
- `docs/learning-notes/phase-2-workflows.md`
- `labs/02-workflow-engineering`
- `patterns/deterministic-workflow.md`

### Phase 3: Multi-Agent Systems

Status: complete for local scripted-model scope. Live-model routing quality,
remote A2A and durable task execution remain later integration gates.

Hypothesis:

> A specialist should be an Agent only when it needs an independent reasoning,
> isolation or conversational boundary; deterministic capabilities remain
> functions or Workflow nodes.

Comparative experiment:

- hold one specialist capability constant;
- implement it as a function, a `single_turn` Agent node, conversational
  transfer and coordinator-selected task delegate;
- compare schema, context isolation, state ownership, event trajectory,
  failure propagation and model-call cost;
- break responsibility boundaries through overlapping tools and shared-state
  writes.

Observed:

- all four boundaries stored the same typed case-triage decision;
- model request counts were 0, 1, 2 and 3 respectively;
- transfer kept the specialist active on the next user turn;
- task delegation isolated the child by function-call ID and returned a
  synthesized function response to the coordinator;
- invalid `finish_task` output remained in the child loop and recovered;
- a hard child model failure propagated without automatic fallback;
- indistinguishable specialist declarations permitted a domain-wrong choice;
- two specialists writing one state key produced silent last-writer-wins.

Evidence:

- `docs/multi-agent/specialist-boundaries.md`
- `docs/learning-notes/phase-3-multi-agent.md`
- `labs/03-multi-agent`
- `patterns/bounded-specialist.md`

### Phase 4: State, Context and Memory

Status: complete for in-memory scripted scope. Durable backends, managed Memory
Bank retention and concurrent state updates remain later integration gates.

Hypothesis:

> Data should be placed according to lifecycle and ownership: current model
> input in prompt context, invocation/session facts in typed state, large
> payloads in artifacts and intentionally retained cross-session knowledge in
> memory.

Comparative experiment:

- hold one user-support task constant;
- vary prompt context, Session state, artifact and memory placement;
- measure request contents, state deltas, artifact references and cross-session
  recall;
- break isolation with stale state, oversized context, foreign-user memory and
  deletion/TTL gaps;
- define explicit writer, reader, retention and conflict policy for each datum.

Observed:

- transient context, state and preloaded memory each used one model request;
- explicit artifact loading used two model requests and exposed the payload
  only to the request that needed it;
- a 20 KB transient payload was resent on every turn, while the artifact
  payload appeared in only one of three model requests;
- state prefixes produced invocation, session, user and app lifecycles, while
  `temp:` state was removed before persistence;
- prefixed state keys bypassed the Agent's `state_schema`;
- artifact versions, Session/user namespaces and deletion were observable;
- memory required explicit ingestion, survived source-Session deletion and had
  backend-specific TTL/deletion behavior;
- an intentionally broken memory adapter leaked Alice's retained data to Bob,
  proving identity scoping belongs at the service boundary.

Evidence:

- `docs/context/data-lifecycle.md`
- `docs/learning-notes/phase-4-context-memory.md`
- `labs/04-context-and-memory`
- `patterns/data-lifecycle-placement.md`

### Phase 5: RAG Engineering

Status: complete for deterministic local/scripted scope. Live managed Search,
Vector Search relevance, latency, token usage, monetary cost and deletion
propagation remain credentialed integration gates.

Hypothesis:

> Retrieval architecture should be chosen from ingestion ownership, access
> control, deletion and evaluation requirements; generation quality cannot
> compensate for retrieval misses or unsupported citations.

Comparative experiment:

- hold one versioned corpus and question set constant;
- compare managed Search with explicit Vector Search ingestion and retrieval;
- record chunk/document identity, retrieval relevance, groundedness, citation
  fidelity, latency and measured cost;
- inject stale documents, access-controlled documents, deletion lag and
  retrieval misses;
- identify who owns parsing, chunking, embedding versions, index updates and
  deletion propagation in each architecture.

Observed:

- all five baseline cases passed retrieval, answer, citation, ACL, stale and
  deletion gates on both paths;
- native Search used one model request, one grounded Event and two stored
  Events per case;
- explicit retrieval used two model requests, a FunctionTool round trip and
  four stored Events per case;
- dropping source ID/version/URI preserved the correct answer but reduced
  citation recall to zero;
- retaining Atlas v1 produced one stale hit even though the final answer used
  current v2;
- removing the native principal filter exposed one internal source to a public
  user;
- failing to reconcile deletion resurfaced the retired `ORBIT15` promotion;
- both pinned sample evals use generic response quality and turn count rather
  than retrieval-specific gates.

Evidence:

- `docs/rag/rag-engineering.md`
- `docs/learning-notes/phase-5-rag.md`
- `labs/05-rag-engineering`
- `patterns/evidence-preserving-rag.md`

### Phase 6: Evaluation

Status: complete for deterministic local/scripted scope. Live judges, statistical
calibration, latency/token/cost telemetry and durable result storage remain
later integration gates.

Hypothesis:

> Evaluation should model an Agent as an observable trajectory with typed
> outcomes. Deterministic contract metrics and probabilistic quality judges
> need separate thresholds, ownership and failure explanations.

Experiment:

- normalize the completed architecture labs into one eval-case contract;
- score tool choice/arguments, trajectory, state, retrieval/citation, final
  response, safety and model-request budgets independently;
- reserve latency, token and monetary-cost metrics for instrumented live
  integration;
- keep deterministic assertions separate from LLM-judge metrics;
- deliberately break one case in each completed architecture phase;
- produce a CI-style report that blocks the broken variants while preserving
  explainable per-dimension failures.

Observed:

- dataset, trace and grade result remain different typed stages;
- all six baseline architecture cases passed;
- all six deliberate breakages failed with owning metric and evidence;
- exact tool name/order/arguments, node/Event trajectory, nested state,
  policy, retrieval/citation and request budgets are independent blockers;
- the broken suite's scripted response-quality mean was `13/3` and passed,
  while deterministic contracts correctly failed the release;
- baseline CLI exited `0` and broken CLI exited `1`;
- two 90,166-byte evidence renders were byte-identical;
- partial trace generation and result comparison were shown to require
  separate dataset-completeness and release-policy gates.

Evidence:

- `docs/evaluation/evaluation-engineering.md`
- `docs/learning-notes/phase-6-evaluation.md`
- `labs/06-evaluation`
- `patterns/behavior-contract-gate.md`

### Phase 7: Safety and HITL

Status: complete for deterministic local/scripted scope. Durable storage,
authenticated approval UI, revocation, atomic checkpoint/effect commit,
streaming confirmation and live policy services remain production gates.

Hypothesis:

> Safety policy must be enforced at the boundary where unsafe data or action
> can still be blocked. Human approval is a durable state transition with
> identity, expiry and idempotency, not an instruction asking the model to wait.

Experiment:

- map callbacks, plugins, tool confirmation and policy services to model
  input/output and tool input/output coverage;
- hold one consequential action constant across prompt-only, callback/plugin
  and tool-confirmation variants;
- inject unsafe model input/output, unsafe tool arguments/results and approval
  replay;
- persist approver identity, decision, scope, expiry and action idempotency;
- resume with fresh runtime objects and prove rejected/expired approval cannot
  execute the side effect.

Observed:

- prompt-only confirmation executed the payment once;
- complete plugin enforcement blocked at `before_tool` with zero effects;
- output-only enforcement hid the result after one effect already occurred;
- unsafe user/tool/model data was stopped or replaced at the owning boundary;
- the pinned ADK 2 path ignored `before_run` return content, so hard input
  blocking moved to the verified `before_model` boundary;
- valid dynamic confirmation resumed with fresh Agent/Runner objects;
- rejected, expired, unauthorized and tampered approvals produced zero effects;
- later-run confirmation replay re-entered the tool, while the external ledger
  retained one effect through action-ID idempotency;
- Workflow `RequestInput` completed the same approval contract at node scope;
- credential requests were confined to a specific function-call ID;
- the prompt-only variant failed the six-case release gate.

Evidence:

- `docs/safety/safety-and-hitl.md`
- `docs/learning-notes/phase-7-safety-hitl.md`
- `labs/07-safety-hitl`
- `patterns/durable-approval-boundary.md`

### Phase 8: Production Engineering

Status: complete for dependency-free render, policy and release evidence.
Real cloud deploy, migration and rollback remain integration gates.

Hypothesis:

> Production readiness is a replaceable set of lifecycle, deployment,
> configuration, secret, telemetry and rollback contracts around the Agent,
> not a property conferred by one generated template.

Comparative experiment:

- compare Starter Pack rendered-project ownership with current Agents CLI
  scaffold, deploy, metadata and observability surfaces;
- hold Agent source and the Phase 6 behavior report constant while rendering
  local, Cloud Run and Agent Runtime targets;
- separate Agent contract, behavior evidence, runtime config, secret
  references, deployment spec, lifecycle manifest and release candidate;
- inject configuration, deploy, telemetry and rollback failures;
- record immutable artifacts, promotion evidence and previous releases;
- generate target-native rollback plans from one shared evidence contract.

Observed:

- target changes left Agent and behavior-gate artifacts byte-equivalent;
- only runtime, deployment, lifecycle and derived release artifacts changed;
- plain `.env` propagation and merge-style updates require explicit secret and
  drift policy;
- trace no-content settings did not govern a separate full-completion upload;
- current-resource metadata lacked artifact, eval, promotion and rollback
  history;
- Cloud Run used revision traffic shifting, while Agent Runtime required
  restore-and-redeploy orchestration;
- seven baseline scenarios passed;
- all eight deliberate breakages failed with 23 blocking reasons;
- baseline exited `0`, broken exited `1`.

Evidence:

- `docs/production/production-engineering.md`
- `docs/learning-notes/phase-8-production.md`
- `labs/08-production-engineering`
- `patterns/replaceable-production-envelope.md`
- 18 dependency-free tests
- deterministic 43,765-byte evidence bundle

### Phase 9: Pattern Catalog

Status: complete.

Hypothesis:

> A reusable pattern is a normalized decision contract with observable
> invariants and counterexamples, not a renamed sample implementation.

Experiment:

- normalize the seven candidate files to the roadmap pattern schema;
- separate evidence maturity from implementation portability;
- cross-link each invariant to source and lab evidence;
- identify overlaps, contradictions and missing counterexamples;
- validate the catalog mechanically before using it as Agent Garden input.

Observed:

- all seven patterns reached `validated` maturity from pinned source, local
  implementation and intentional breakage;
- six decision contracts are portable and Bounded Specialist remains
  version-specific to the current ADK mode surface;
- 28 observable contracts and 28 failure modes each have source and lab refs;
- seven rejected decisions make counter-position explicit;
- 11 relations and five decision boundaries expose cross-pattern dependencies;
- all 12 invalid catalog mutations failed by their expected issue code;
- baseline exited `0`, broken exited `1`.

Evidence:

- `docs/patterns/pattern-catalog.md`
- `docs/learning-notes/phase-9-pattern-catalog.md`
- `patterns/catalog.json`
- `patterns/manifests`
- `labs/09-pattern-catalog`
- 14 dependency-free tests
- deterministic 3,327-byte evidence bundle

### Phase 10: Agent Garden Reverse Engineering

Status: complete.

Hypothesis:

> A reusable Agent Garden needs separate contracts for catalog discovery,
> scaffold rendering, runtime execution and governance; no existing manifest
> owns all four.

Experiment:

- compare ADK recipe manifests, Starter Pack template config and Agents CLI
  project manifest field by field;
- classify fields as catalog-only, scaffold-time, runtime or governance;
- trace validation, discovery, ownership, version and upgrade behavior;
- create valid and deliberately misleading entries for the same Agent;
- define the minimum discoverability contract without designing the complete
  executable blueprint early.

Observed:

- the three source contracts contain 33 field rows across catalog, scaffold,
  runtime and governance ownership;
- recipe, template and project surfaces provide only 4, 3 and 1 of the nine
  required discovery facts;
- recipe path, template folder and generated project name are all implicit
  identities with different lifecycle owners;
- current Agents CLI ADK discovery scans frozen `python/agents` rather than
  the active `core/` and `contrib/` recipe manifests;
- the registry-composed entry covers stable identity, display, lifecycle,
  ownership, classification, immutable source, compatibility, reuse and
  assurance without executable Blueprint fields;
- all 13 misleading entries failed by their expected issue code;
- baseline exited `0`, broken exited `1`.

Evidence:

- `agent-garden/concepts.md`
- `agent-garden/discoverability-contract.md`
- `agent-garden/metadata-surfaces.json`
- `agent-garden/catalog-entry.schema.json`
- `agent-garden/discovery-catalog.json`
- `docs/learning-notes/phase-10-agent-garden.md`
- `labs/10-agent-garden-discovery`
- 16 dependency-free tests
- deterministic 5,578-byte evidence bundle

### Phase 11: Blueprint Schema

Status: complete.

Hypothesis:

> An executable Blueprint should reference a stable CatalogEntry and describe
> only architecture/runtime/policy/eval/lifecycle contracts shared by
> materially different Agents; a union of existing manifest fields will encode
> accidental tooling details.

Experiment:

- write a single-Agent typed-tool blueprint example;
- write a deterministic Workflow plus RAG blueprint example;
- write a multi-agent specialist plus durable-approval blueprint example;
- identify common required fields and architecture-specific extension points;
- define a versioned schema only after all three examples are executable;
- add invalid examples for authority duplication, missing behavior gates,
  unsafe state ownership and incompatible lifecycle combinations;
- validate schema migration without changing CatalogEntry identity.

Observed:

- three Blueprint examples reference immutable Catalog implementations rather
  than duplicating display, owner, source or compatibility authority;
- common top-level fields are limited to identity/reference, architecture,
  runtime, policy, evaluation, lifecycle, schema version and extensions;
- architecture is a strict single-Agent, Workflow or multi-agent union;
- the Workflow example composes explicit RAG provenance and grounding
  contracts without changing its core implementation provenance;
- the multi-agent example composes typed task delegation with durable approval
  and replay contracts;
- 38 local references resolve to 26 unique Python symbols, and all three
  implementation entrypoints resolve inside commit `9702a79`;
- all 15 invalid combinations failed by their expected issue code;
- flat single-Agent v0.1 migrates exactly to canonical v1.0 while preserving
  Blueprint, CatalogEntry and Implementation identities;
- baseline exits `0`, broken exits `1`.

Evidence:

- `agent-garden/blueprint-schema.md`
- `agent-garden/blueprints`
- `docs/learning-notes/phase-11-blueprints.md`
- `labs/11-blueprint-schema`
- 19 dependency-free tests
- deterministic 4,383-byte evidence bundle

### Phase 12: MVP Architecture

Status: complete for dependency-free component and lifecycle scope. Cloud
deployment, signed release history and transactional promotion remain later
integration gates.

Hypothesis:

> The MVP should contain only components required to resolve Catalog identity,
> validate Blueprint composition, render a project, run behavior gates and
> retain release evidence; every additional service needs repeated evidence.

Experiment:

- derive component boundaries from Phase 10 Catalog, Phase 11 Blueprint and
  Phase 8 release contracts;
- write ADRs for registry, validator, scaffold renderer, evaluation adapter
  and release ledger ownership;
- define storage and trust boundaries without choosing a distributed system
  prematurely;
- map extension points to typed architecture unions or external contract refs;
- prove that single-Agent, Workflow/RAG and multi-agent/HITL use the same
  platform lifecycle without sharing one runtime implementation.

Observed:

- six components were required: Catalog Registry, Contract Validator, Project
  Renderer, Deployment Controller, Behavior Gate and Release Ledger;
- Deployment Controller and Release Ledger require different credentials,
  mutability and accountable owners;
- Contract Validator and Behavior Gate require different source-read versus
  sandboxed-execution trust boundaries;
- 12 artifacts map to version control, workspace, content-addressed store,
  append-only ledger, target control plane or external secret manager;
- nine trust boundaries and seven extension points preserve authority across
  selection, validation, rendering, deployment, evaluation and rollback;
- all three Phase 11 Blueprints completed the same seven-stage release path
  while retaining architecture-specific validators and blocking metrics;
- all 15 invalid component/lifecycle mutations failed by their expected issue
  code;
- baseline exits `0`, broken exits `1`.

Evidence:

- `agent-garden/architecture.md`
- `agent-garden/mvp-architecture.json`
- `agent-garden/mvp-architecture.schema.json`
- `agent-garden/adrs`
- `docs/learning-notes/phase-12-mvp-architecture.md`
- `labs/12-mvp-architecture`
- 18 dependency-free tests
- deterministic 17,713-byte evidence bundle

### Phase 13: Mini Agent Garden

Status: next.

Hypothesis:

> A thin CLI can discover, scaffold, validate, test and upgrade three different
> Blueprint architectures by exchanging the Phase 12 typed artifacts; it must
> not become a new Catalog, policy, deployment or release authority.

Next experiment:

- implement local Catalog discovery and immutable Implementation selection;
- render Project Instances for all three Phase 11 Blueprints;
- expose schema and semantic validation without duplicating validator rules in
  command handlers;
- run behavior gates and retain digest-bound reports;
- distinguish Blueprint schema migration, Implementation change and Project
  Instance regeneration during upgrade;
- add a new architecture extension only through a typed contract and prove
  whether core CLI dispatch needs modification.

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

Each pattern card under `patterns/` has a canonical JSON manifest:

```text
name:
status: candidate | validated | rejected
portability: portable | version-specific
context:
forces:
decision:
implementation:
observable_contract:
failure_modes:
counterexamples:
adk_versions:
source_evidence:
lab_evidence:
rejected_decisions:
```

Each observable contract and failure mode references at least one pinned source
and one executable lab artifact. Candidate patterns are not promoted to
`validated` from source reading alone.

## Agent Garden Deliverable Sequence

1. Compare `adk-samples/manifest.yaml`, Starter Pack template config and
   `agents-cli-manifest.yaml`. Complete in Phase 10.
2. Identify catalog-only, scaffold-time, runtime and governance fields.
   Complete in Phase 10.
3. Write three materially different blueprint examples. Complete in Phase 11.
4. Design schema only after examples expose common fields. Complete in Phase
   11.
5. Validate invalid blueprints and migration between schema versions.
   Complete in Phase 11.
6. Derive authority-separated components, storage, trust and extension
   boundaries. Complete in Phase 12.
7. Implement registry discovery, scaffold rendering and project validation.
8. Add eval-gate and upgrade commands.
9. Test whether a new architecture can be added without modifying core CLI
   logic.

## Roadmap Revisions

| Date | Previous assumption | Source-driven revision |
|---|---|---|
| 2026-08-12 | Agent Starter Pack is the current production baseline | Keep it as template-composition evidence; use Agents CLI for active lifecycle work |
| 2026-08-12 | `adk-samples` is one homogeneous gallery | Separate active recipes, frozen legacy samples, skills contract and transitional duplicates |
| 2026-08-12 | Workflow samples share one runtime model | Teach ADK 2.0 first and preserve an explicit ADK 1.x comparative track |
| 2026-08-12 | Existing manifest can seed the full blueprint directly | Treat manifest as minimal catalog/ownership metadata; derive runtime and governance fields experimentally |
| 2026-08-12 | Every yielded Event can be treated as message content | Error events may have no content; consumers must inspect event kind, error and action fields first |
| 2026-08-12 | Legacy composites have no resume semantics | They persist agent-state checkpoints; the migration issue is different replay/routing and parent-continuation behavior |
| 2026-08-12 | Replayed output proves a side effect ran twice | Graph replay can re-surface prior output while an external side-effect ledger remains unchanged |
| 2026-08-12 | `max_iterations` is a failed/successful outcome | It is only a technical bound; exhaustion needs an explicit domain route |
| 2026-08-12 | One aggregate quality score can serve as a release gate | Preserve per-case deterministic blockers; the six-case broken suite passed its `13/3` scripted judge threshold while failing architecture contracts |
| 2026-08-12 | A project manifest and successful deploy identify a recoverable release | Keep scaffold metadata, desired runtime config and append-only release evidence as separate contracts |
| 2026-08-12 | One rollback abstraction can hide target differences | Standardize immutable evidence, then use Cloud Run traffic shift, GKE rollout undo or Agent Runtime restore-and-redeploy |
| 2026-08-12 | Pattern maturity and version scope fit one status enum | Separate `status` from `portability`; Bounded Specialist is validated and version-specific at the same time |
| 2026-08-12 | A source list at the bottom of a card is sufficient evidence | Link every observable contract and failure mode to named pinned source and executable lab evidence |
| 2026-08-12 | A repository-valid recipe is automatically visible to scaffold consumers | Current Agents CLI still scans the frozen legacy root; give discovery a versioned catalog contract |
| 2026-08-12 | Recipe, template and project manifest fields can be unioned into one Blueprint | Separate stable catalog identity from scaffold/project metadata, then derive executable schema from three different examples |
| 2026-08-12 | One generic architecture options map can cover every Agent | Use a strict single-Agent, Workflow or multi-agent union and keep cross-cutting runtime/policy/eval/lifecycle fields common |
| 2026-08-12 | JSON Schema alone proves a Blueprint is executable | Add Git object, assurance digest, Python AST, graph, state, retrieval, policy and lifecycle semantic validation |
| 2026-08-12 | One credentialed deployment service can also own release history | Separate mutable target control in Deployment Controller from append-only promotion and rollback truth in Release Ledger |

## Milestone Tracking

Current milestone and continuation context live in
[`PROJECT_STATE.md`](../PROJECT_STATE.md). Phase completion requires:

```text
make verify
```

plus the phase-specific behavioral/evaluation gate. Passing structural checks
alone never proves an Agent design.
