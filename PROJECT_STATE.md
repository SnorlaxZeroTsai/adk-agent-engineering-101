# Project State

Last updated: 2026-08-12

## Current Goal

Start Phase 12 by deriving the smallest MVP component model and ADR set from
the completed CatalogEntry, executable Blueprint, behavior-gate and release
contracts. Do not choose storage or distributed services before an observed
ownership boundary requires them.

## Completed

- Phase 0 repository reconnaissance for `google/adk-samples` and
  `GoogleCloudPlatform/agent-starter-pack`.
- Additional current-state scan of `google/adk-python` and `google/agents-cli`
  because the primary repositories now point to those projects.
- Repository map, 15 representative study units and dependency-ordered roadmap.
- Initial project structure and reproducible upstream source lock.
- First foundations module and Agent basics lab offline baseline.
- Project verifier, contract inspector and all 13 Lab 01 tests pass.
- Tool boundary and Runner/Session/Event execution-model modules.
- Pinned ADK 2.6.3 scripted runtime harness with 8 passing tests.
- Success, same-session continuation, missing-session, unhandled failure,
  recovered failure and callback failure traces.
- Phase 2 source comparison of deprecated composite Agents and graph
  `Workflow`.
- Lab 02 shared domain core plus legacy and graph adapters.
- Sequence, fan-out/join, routed loop, retry, missing-state, duplicate-output
  and fresh-object resume experiments.
- 7 Lab 02 offline tests and 12 ADK-backed Workflow tests.
- First pattern extracted: deterministic Workflow.
- Phase 3 source comparison of `chat`, `single_turn` and `task` Agent modes.
- Lab 03 typed case-triage capability across function, single-turn, transfer
  and task-delegation boundaries.
- Transfer continuation, task validation recovery and hard specialist failure
  experiments.
- Overlapping-responsibility and shared-state conflict experiments.
- 7 Lab 03 offline tests and 10 ADK-backed multi-agent tests.
- Second pattern extracted: bounded specialist.
- Phase 4 source comparison of transient model context, instruction/state
  assembly, state scopes, artifact services and memory services.
- Lab 04 common support dossier across transient context, Session state,
  explicit artifact loading and preloaded cross-session memory.
- Stale-state, 20 KB context, state-scope, artifact lifecycle, memory
  retention/deletion and intentional cross-user leakage experiments.
- 6 Lab 04 offline tests and 13 ADK-backed context/memory tests.
- Third pattern extracted: data lifecycle placement.
- Phase 5 source comparison of native `VertexAiSearchTool`, Discovery Engine
  fallback, managed connector ingestion and explicit Vector Search ingestion.
- Lab 05 versioned/ACL corpus across native managed Search and explicit
  FunctionTool retrieval.
- Retrieval recall/precision, answer, citation, ACL, stale-version and deletion
  gates over five shared query cases.
- Provenance-loss, unfiltered-search, stale-index and deletion-lag breakages.
- 10 Lab 05 offline tests and 10 ADK-backed RAG tests.
- Fourth pattern extracted: evidence-preserving RAG.
- Phase 6 source comparison of ADK eval cases/metrics/results and Agents CLI
  dataset/generate/grade/compare lifecycle.
- Lab 06 typed `EvalDataset`, verdict-free `TraceSet` and CI-consumable
  `SuiteReport`.
- Six cross-phase cases covering Agent, Workflow, specialist, memory, RAG and
  consequential-action behavior.
- Exact tool/argument, trajectory, state, output, policy, retrieval and
  model-request budget metrics.
- Six passing baselines and six deliberately broken variants.
- Baseline gate exits `0`; broken gate exits `1` with 28 blocking reasons.
- 11 Lab 06 offline tests and 6 ADK-backed cross-phase tests.
- Fifth pattern extracted: behavior contract gate.
- Phase 7 source comparison of App plugins, Agent callbacks, model/tool hooks,
  FunctionTool confirmation, Workflow `RequestInput` and credential requests.
- Lab 07 shared vendor payment across prompt-only, plugin and dynamic approval
  variants.
- User/model and tool input/output enforcement coverage experiments.
- Approval envelope with approver, action scope, request hash, policy version,
  decision and issue/expiry times.
- Fresh-object tool and Workflow resume, rejection, expiry, unauthorized
  approver, tampering and later-run replay experiments.
- 7 Lab 07 offline tests and 15 ADK-backed safety/HITL tests.
- Phase 6 gate extended to six baseline and six broken architecture cases.
- Sixth pattern extracted: durable approval boundary.
- Phase 8 source comparison of Starter Pack rendered-project ownership and
  current Agents CLI scaffold, deploy, metadata and observability lifecycle.
- Lab 08 target-independent Agent/behavior contracts rendered across local,
  Cloud Run and Agent Runtime production envelopes.
- Typed plain configuration, secret references, stateful services, identity,
  telemetry, deployment and immutable release evidence.
- Append-only promotion and previous-release history with target-specific
  rollback plans.
- Seven passing baseline scenarios and eight broken variants with 23 blocking
  failures.
- 18 Lab 08 dependency-free production-contract tests.
- Seventh pattern extracted: replaceable production envelope.
- Phase 9 canonical catalog index, JSON Schemas and seven structured manifests.
- Seven normalized Markdown cards synchronized with maturity, portability and
  claim IDs.
- 28 observable contracts and 28 failure modes, each linked to pinned source
  and executable lab evidence.
- Seven explicitly rejected decisions, 11 cross-pattern relations and five
  decision boundaries.
- Ten invalid catalog mutations covering evidence, source pinning, status,
  path, relation, duplication and version scope.
- 14 Lab 09 dependency-free tests with baseline exit `0` and broken exit `1`.
- All seven patterns promoted to locally `validated`; Bounded Specialist
  remains `version-specific`.
- Phase 10 field-level comparison of ADK recipe manifest, Starter Pack template
  config and Agents CLI project manifest.
- 33 source fields classified across catalog, scaffold, runtime and governance
  ownership.
- Four pinned consumer observations including current Agents CLI discovery of
  the frozen `python/agents` root.
- Non-executable CatalogEntry contract with nine required discovery facts.
- Stable Agent identity separated from implementation, template, project
  instance, Blueprint and release identities.
- Valid `cross-session-memory` entry with full-commit source, ADK 1.x
  compatibility, pinned remote-template locator and runnability assurance.
- 13 misleading catalog mutations covering identity, source, compatibility,
  owner, lifecycle, assurance and authority violations.
- 16 Lab 10 dependency-free tests with baseline exit `0`, broken exit `1` and
  deterministic 5,578-byte evidence bundle.
- Phase 11 example-first executable Blueprint contract.
- Three CatalogEntries and immutable implementations pinned to repository
  commit `9702a79d15f81a9a44a8d40af3ca038196746c46`.
- Single-Agent typed-tool, deterministic Workflow/RAG and
  multi-agent/durable-approval Blueprint examples.
- Draft 2020-12 schema with strict common top-level domains and three typed
  architecture branches.
- Git object, assurance digest, Python AST, graph, retrieval, delegation,
  state, policy, evaluation and lifecycle semantic validation.
- 38 local contract refs resolving to 26 unique Python symbols.
- 15 deliberate invalid Blueprint mutations with baseline exit `0` and broken
  exit `1`.
- Flat single-Agent v0.1 to v1.0 exact migration with Blueprint,
  CatalogEntry and Implementation identities preserved.
- 19 Lab 11 dependency-free tests and deterministic 4,383-byte evidence
  bundle.

## Important Findings

1. `adk-samples` is in a migration state:
   `core/<language>/<recipe>` and `contrib/<language>/<recipe>` are the active
   recipe model, while 40 legacy samples remain under frozen
   `<language>/agents` paths.
2. The repository mixes ADK 1.x and 2.0 samples. Version is part of the
   architecture evidence; examples cannot be combined blindly.
3. ADK Python 2.0 adds a graph `Workflow` runtime and Task API while retaining
   legacy composite agents. Workflow comparisons must state which runtime model
   is being discussed.
4. Agent Starter Pack is in maintenance mode. Its template composition remains
   valuable evidence, but active lifecycle tooling moved to `agents-cli`.
5. Google separates Agent logic from platform concerns through layered
   templates, deployment-target overlays, eval assets, manifests and CLI
   lifecycle commands.
6. Official samples contain demo limitations and implementation debt. They are
   evidence, not unquestionable reference architectures.
7. `FunctionTool` turns signature, type hints and the full docstring into the
   model-visible contract; runtime `ToolContext` is excluded.
8. A stateful tool mutation is first observable as a function-response event
   delta, then materialized by the Session service.
9. Unhandled tool and callback exceptions emit and persist error events before
   propagating to the Runner caller.
10. Conversation continuation on a Session is not interrupted-invocation
    resumption.
11. Legacy composite Agents are deprecated but still have resumable agent-state
    checkpoints. Migration must compare behavior rather than assume no legacy
    resume semantics exist.
12. `LoopAgent.max_iterations` is a technical bound, not a domain rejection or
    success outcome.
13. Graph `RetryConfig` provides node-local retry and an error Event per failed
    attempt, but retry count is not durable across resume.
14. Graph replay can re-surface a completed node's output without re-executing
    its external side effect.
15. In the pinned custom-Agent experiment, legacy Runner resumed the
    interrupted leaf but did not naturally continue the parent sequence tail.
16. Dynamic child output needs explicit `use_as_output=True` delegation to
    avoid duplicate logical result Events.
17. `chat`, `single_turn` and `task` represent different ownership lifecycles;
    they are not interchangeable Agent-as-tool wrappers.
18. Transfer gives the specialist the user reply and subsequent conversational
    turn; task delegation returns typed completion to the coordinator.
19. Task output schema failure can remain inside the child loop, but an
    unhandled child model failure propagates without automatic fallback.
20. Typed schemas do not resolve overlapping specialist charters or cross-field
    business invariants.
21. Two specialists writing one Session key produce silent last-writer-wins in
    the local runtime.
22. `RunConfig.model_input_context` is per invocation and model-visible, but it
    is not written to Session state or history.
23. State key prefixes define app, user, Session and temporary lifecycles;
    `temp:` deltas are visible during the invocation but trimmed before
    persistence.
24. Agent `state_schema` validates unprefixed state only. Keys containing a
    scope prefix bypass that schema and require separate validation.
25. Artifacts are versioned and Session-scoped by default; `user:` artifacts
    cross Sessions for one user and must be loaded before the model can see
    their payload.
26. Explicit artifact loading kept a 20 KB payload out of unrelated model
    requests, while transient context resent it on every invocation.
27. Memory requires explicit ingestion. Deleting the source Session did not
    remove retained memory, and the base memory contract has no portable
    deletion API.
28. Memory preload injects recall as dynamic instruction without copying the
    source datum into the new Session state.
29. Cross-user isolation is a memory-service responsibility. An adapter that
    ignored request identity returned Alice's secret to Bob despite a valid
    Agent and Runner configuration.
30. Native `VertexAiSearchTool` performs retrieval inside one Gemini request
    and surfaces provider grounding metadata rather than a local FunctionTool
    call/response.
31. With multiple tools and `bypass_multi_tools_limit=True`, ADK can replace
    native Vertex AI Search with `DiscoveryEngineSearchTool`, changing the
    execution and observability model.
32. Managed Search removes custom parsing/chunking code but retains connector,
    generated-resource, sync and deletion control-plane ownership.
33. The pinned Vector Search recipe owns parsing, chunk IDs, staging, schema
    and reconciliation while the service still generates embeddings.
34. Correct final text is insufficient RAG evidence. Provenance loss and stale
    versions both produced correct-looking answers that failed retrieval gates.
35. ACL filtering must happen before model-visible retrieval. Removing one
    native filter exposed an internal reset code to a public principal.
36. Stable create IDs and `AlreadyExists` handling do not reconcile obsolete
    chunks or source deletions.
37. The pinned managed and vector RAG sample evals are identical generic
    response-quality/turn-count checks with no enforced retrieval gate.
38. ADK `InvocationEvents` is a reduced projection containing author/content;
    it does not preserve state deltas, Workflow node paths, isolation scopes,
    errors or grounding metadata required by several architecture gates.
39. `TrajectoryEvaluator` compares exact tool names and arguments but averages
    per-invocation `0/1` scores into the case result.
40. `LocalEvalService` fails a case on a failed metric overall status, yet the
    metric may already have averaged invocation failures. Legacy
    `AgentEvaluator` also explicitly averages invocation scores.
41. Agents CLI correctly separates dataset, populated trace and grade-result
    stages, but partial trace generation can drop failed cases and still exit
    `0`.
42. `agents-cli eval compare` reports recursive JSON differences and deltas;
    it does not decide regression or provide a blocking release status.
43. Local Agents CLI custom metrics compile and execute Python with CLI process
    privileges, making eval configuration a trusted-code boundary.
44. The initial five-case broken suite passed its scripted judge mean at
    `4.2/5` while deterministic metrics correctly blocked all five cases.
45. App plugins are global across an Agent tree; model/tool plugins run before
    Agent callbacks, and the first non-None plugin result short-circuits later
    policy handlers.
46. `after_tool` can protect later model input but cannot undo an external
    effect. Consequential-action policy must run before tool execution and at
    the side-effect service.
47. In the pinned ADK 2 Agent path, `before_run_callback` was invoked but its
    returned content did not halt execution; the verified `before_model`
    replacement produced the hard stop.
48. `ToolConfirmation` transports confirmed, hint and payload but does not
    authenticate an approver or enforce scope, request integrity, expiry or
    idempotency.
49. The confirmation processor validates the original tool name, arguments,
    history and requirement before re-execution.
50. Replaying the same confirmation in a later run re-entered the tool.
    Action-ID idempotency in the external ledger, not confirmation dedup,
    prevented a second effect.
51. Workflow `RequestInput` is a node-level interrupt with payload and response
    schema; FunctionTool confirmation is a tool-call-level interrupt.
52. Credential requests require a function-call ID and are not substitutes for
    business approval.
53. The expanded broken suite passed its scripted judge mean at `13/3` while
    deterministic metrics blocked all six cases with 28 blocking failures.
54. Starter Pack and Agents CLI both layer shared, language, target and Agent
    templates, but rendered files become application-owned source after
    generation.
55. `agents-cli-manifest.yaml` records project and scaffold metadata; deploy
    flags, runtime sizing, secrets, identity and rollback remain separate
    authorities.
56. Agents CLI copies project `.env` values into runtime configuration while
    structured secret bindings use a different path. Output redaction does not
    turn plain configuration into a secret boundary.
57. Agent Runtime update preserves unspecified live plain environment values,
    which can retain out-of-band drift as well as intentional configuration.
58. No-content trace spans and full prompt-response completion uploads are
    independent telemetry paths with separate governance requirements.
59. `deployment_metadata.json` is mutable current/pending operation state, not
    an append-only record of source, artifact, behavior evidence, promotion and
    previous release.
60. Rollback capability is target-specific: Cloud Run shifts revision traffic,
    GKE rolls out a prior revision, and Agent Runtime requires restoring an
    immutable bundle and redeploying.
61. Lab 08 changed runtime, deployment, lifecycle and derived release artifacts
    across targets while keeping Agent and behavior contracts byte-equivalent.
62. Seven production baseline scenarios passed; eight broken variants produced
    23 blocking failures for secrets, telemetry, eval, artifact immutability,
    target drift, metadata and rollback history.
63. Pattern evidence maturity and implementation portability are independent.
    Bounded Specialist is locally validated while its current ADK mode surface
    remains version-specific.
64. A bottom-of-page source list does not identify which source and experiment
    support one observable contract or failure mode.
65. Every normalized claim now requires at least one full-commit GitHub source
    and one existing repository lab artifact.
66. The seven patterns contain 28 observable contracts, 28 failure modes and
    seven rejected decisions rather than only positive implementation advice.
67. Cross-pattern relations show that Behavior Contract Gate verifies five
    other patterns and Production Envelope depends on both behavior and data
    lifecycle contracts.
68. Five decision boundaries make control-versus-reasoning,
    placement-versus-retrieval, enforcement-versus-evaluation,
    resume-versus-idempotency and behavior-versus-deployment choices explicit.
69. Twelve deliberately invalid catalog mutations all failed by their expected
    issue code; baseline passed with zero issues.
70. ADK recipe, Starter template and Agents CLI project metadata provide only
    4, 3 and 1 of the nine required discoverability facts; no existing
    manifest owns the complete catalog contract.
71. Recipe directory, template folder and generated project name are three
    different implicit identities and cannot serve as one stable Agent ID.
72. Pinned Agents CLI ADK discovery still scans the repository's frozen
    `python/agents` root and does not consume current `core/`/`contrib/`
    manifests.
73. Repository-valid and active does not imply consumer-visible; producer and
    discovery consumer require one versioned catalog contract.
74. Template deployment targets and dependencies are scaffold capabilities,
    not runtime or production assurance.
75. Stable identity, lifecycle replacement, immutable source, compatibility,
    reuse locator and implementation-bound assurance require registry-owned
    metadata beyond the three upstream surfaces.
76. All 13 misleading catalog mutations failed, including project-name
    identity, mutable refs, frozen path, ADK 2.x overclaim, authority leakage
    and duplicate immutable source.

## Architecture Decisions

- Write learning material in Traditional Chinese while preserving official API
  and symbol names in English.
- Pin every upstream conclusion to a commit and source path.
- Label observations as source fact, inference or open question.
- Keep upstream clones outside this repository; record only immutable commit
  metadata and source links.
- Teach current ADK 2.0 semantics first, then use 1.x samples comparatively.
- Keep labs offline-testable. Live model and cloud tests are separate gates.
- Keep pure domain functions separate from ToolContext-aware wrappers.
- Assert yielded events, persisted events and materialized state independently.
- Use explicit error callbacks only for approved recovery policy.
- Keep deterministic domain rules independent of legacy composite and graph
  adapters.
- Treat loop exhaustion as an explicit route.
- Use typed join payloads when all parallel results are required.
- Keep harness metrics separate from business Session state.
- Assign one retry owner and require idempotency.
- Test resume with fresh runtime objects and an external side-effect ledger.
- Use node paths/run IDs as trajectory evidence.
- Require independent reasoning, isolation or conversation ownership before
  creating a specialist Agent.
- Use single-turn for bounded semantic Workflow nodes, transfer for
  specialist-owned conversation and task mode for coordinator-owned results.
- Disable parent/peer transfer on bounded task specialists.
- Validate domain invariants after typed specialist output.
- Namespace specialist state or merge it explicitly.
- Place data from an explicit writer, reader, scope, retention and deletion
  contract rather than from prompt convenience.
- Validate prefixed state before mutation because Agent `state_schema` does not
  cover scoped keys.
- Keep large payloads in artifacts and load them only for model requests that
  need their content.
- Treat memory ingestion, identity isolation and deletion propagation as
  explicit service policies, separate from Session lifecycle.
- Preserve document ID, version, chunk ID, URI and ACL metadata through every
  retrieval adapter.
- Apply trusted authorization filters before ranking and top-k.
- Evaluate expected retrieved identities separately from final response text.
- Fail RAG gates on stale/deleted hits even if the selected citation is current.
- Require citations to reference the exact evidence returned in the current
  invocation.
- Treat managed native Search and FunctionTool fallback as distinct runtime
  trajectories.
- Separate ingestion success from version/deletion reconciliation.
- Keep eval datasets, generated traces and grade results as separate types.
- Require generated case IDs to exactly match the input dataset.
- Preserve full runtime evidence before projecting it into evaluator-specific
  structures.
- Make deterministic safety, state, tool, retrieval and terminal-outcome
  metrics block on every applicable case.
- Treat `NOT_EVALUATED` as failure for a requested blocking metric.
- Keep judge metrics advisory until model, sampling, calibration and failure
  policy are explicit.
- Preserve per-case failures even when an aggregate threshold passes.
- Separate result comparison from release policy and expose a CI process
  status.
- Treat local custom metric functions as reviewed executable code.
- Put global invariants in App plugins and Agent-local adaptations in Agent
  callbacks.
- Enforce unsafe transitions at the last boundary that can still prevent them.
- Bind approval to approver identity, action type, action ID, full request hash,
  policy version, decision and expiry.
- Keep raw credentials out of approval payloads.
- Fail closed on rejected, expired, unauthorized, malformed or tampered
  approval.
- Use an external action ID as the side-effect idempotency key.
- Treat framework resume/dedup and business idempotency as separate contracts.
- Choose ToolConfirmation for one tool call and `RequestInput` for a
  deterministic Workflow node.
- Keep Agent source and behavior expectations independent from deployment
  target.
- Model scaffold metadata, runtime desired state and release evidence as
  different types with named owners.
- Keep secret references out of plain environment configuration and pin their
  provider versions.
- Block unmanaged live drift before merge-style updates; adopt or delete it
  explicitly.
- Require remote targets to name durable Session, artifact and memory services
  plus runtime identity.
- Govern trace content and full prompt-response capture independently.
- Promote the exact immutable artifact and behavior report tested in staging.
- Store release history append-only and treat current-resource metadata as a
  replaceable cache.
- Standardize release evidence while leaving rollback execution to the real
  target adapter.
- Use canonical JSON manifests as the machine authority for patterns and keep
  Markdown cards as synchronized human explanations.
- Separate pattern `status` from `portability`.
- Require every observable contract and failure mode to reference named pinned
  source and executable lab evidence.
- Require at least one counterexample and rejected decision per pattern.
- Store dependencies in relation edges and ambiguous choices in decision
  boundaries.
- Keep published JSON Schema required fields and the stdlib validator in
  test-enforced parity.
- Treat the pattern catalog as blueprint input, not runtime configuration.
- Keep Agent identity independent from display name, source path, template
  folder, generated project name and deployment resource.
- Store immutable source, language, framework compatibility, reuse locator and
  assurance on an Implementation beneath one CatalogEntry.
- Require deprecated or retired catalog entries to name a replacement.
- Reject active catalog entries that point to frozen source roots.
- Treat template capabilities as scaffold facts until runtime and behavior
  evidence prove them.
- Keep CatalogEntry explicitly free of model, tool, workflow, policy,
  evaluation, secret, deployment and release configuration.
- Derive the executable Blueprint schema from three materially different
  examples rather than unioning current manifest fields.
- Let CatalogEntry own stable identity and immutable implementation
  provenance; let Blueprint own executable composition.
- Keep only catalog reference, architecture, runtime, policy, evaluation,
  lifecycle, version and extensions as common Blueprint domains.
- Use a strict typed union for single-Agent, Workflow and multi-agent
  architecture payloads.
- Separate Garden IDs from runtime-owned snake_case names.
- Use JSON Schema for shape and Git/AST/graph/cross-domain validation for
  executable semantics.
- Require RAG provenance/grounding and consequential-action approval/safety as
  blocking contracts.
- Auto-migrate only shape changes that preserve identity, behavior and
  ownership; require a new Implementation or review for semantic changes.

## Unresolved Questions

- How should trajectory evaluation differ between graph Workflow nodes and
  conversational agent transfers?
- How should task delegation fallback and retry budgets interact with graph
  node retry?
- How should remote A2A specialists preserve the same typed isolation and
  completion contracts?
- How should stored Workflow Events migrate when a node is renamed, removed or
  split?
- Which durable Session service and idempotency contract are sufficient for
  actual process-loss recovery?
- How should partial streaming events be consolidated and evaluated?
- Which state scopes need optimistic concurrency in a durable Session service?
- Which managed memory backends provide enforceable TTL, user deletion and
  proof of deletion?
- How should artifact and memory deletion propagate to cached model context,
  indexes and evaluation fixtures?
- Which retrieval quality and citation metrics should block a RAG regression?
- How do live managed Search and Vector Search compare on relevance, latency,
  token usage and monetary cost for the same corpus?
- What deletion propagation bounds can each live backend enforce and prove?
- How should live judge sampling, confidence, drift and inter-rater agreement
  be calibrated before a probabilistic metric becomes blocking?
- Which latency, token and monetary-cost distributions should block a release?
- Which safety mechanism owns each model-input, model-output, tool-input and
  tool-output boundary?
- Which durable store and transaction/outbox design can coordinate an approval
  checkpoint with the irreversible effect?
- How should approval revocation and separation of duties survive resume?
- Which live policy service latency/failure modes require fail-closed versus
  degraded behavior?
- How should the release ledger be signed, retained and transactionally linked
  to platform deployment success?
- Which production identity and secret manager contracts should be portable
  across Cloud Run, Agent Runtime and GKE?
- How should database, Session, artifact, memory and index migrations constrain
  application rollback?
- Which health, behavior, latency and cost signals should trigger automatic
  traffic rollback?
- How should Terraform desired state and imperative Agents CLI deploy avoid
  dual ownership and undetected drift?
- Which minimum components are required to resolve Catalog identity, validate
  Blueprint composition, render projects, run behavior gates and retain
  release evidence?
- Which component owns registry indexing, trust policy and access control?
- Which MVP state belongs in Git, a local content-addressed cache or a durable
  service?
- Which architecture extensions require new typed schema branches, and which
  can remain external contract references?
- How should validator, scaffold renderer, evaluation adapter and release
  ledger communicate without sharing mutable internal models?
- What is the smallest upgrade plan that distinguishes Blueprint schema
  migration, Implementation change and Project Instance regeneration?

## Relevant Sources

- [`references/upstream-lock.yaml`](references/upstream-lock.yaml)
- [`references/source-index.md`](references/source-index.md)
- [`docs/repo-map.md`](docs/repo-map.md)
- [`docs/roadmap.md`](docs/roadmap.md)
- [`docs/foundations/agent.md`](docs/foundations/agent.md)
- [`docs/foundations/tools.md`](docs/foundations/tools.md)
- [`docs/foundations/execution-model.md`](docs/foundations/execution-model.md)
- [`docs/learning-notes/phase-1-foundations.md`](docs/learning-notes/phase-1-foundations.md)
- [`docs/workflows/deterministic-workflows.md`](docs/workflows/deterministic-workflows.md)
- [`docs/learning-notes/phase-2-workflows.md`](docs/learning-notes/phase-2-workflows.md)
- [`patterns/deterministic-workflow.md`](patterns/deterministic-workflow.md)
- [`docs/multi-agent/specialist-boundaries.md`](docs/multi-agent/specialist-boundaries.md)
- [`docs/learning-notes/phase-3-multi-agent.md`](docs/learning-notes/phase-3-multi-agent.md)
- [`patterns/bounded-specialist.md`](patterns/bounded-specialist.md)
- [`docs/context/data-lifecycle.md`](docs/context/data-lifecycle.md)
- [`docs/learning-notes/phase-4-context-memory.md`](docs/learning-notes/phase-4-context-memory.md)
- [`patterns/data-lifecycle-placement.md`](patterns/data-lifecycle-placement.md)
- [`docs/rag/rag-engineering.md`](docs/rag/rag-engineering.md)
- [`docs/learning-notes/phase-5-rag.md`](docs/learning-notes/phase-5-rag.md)
- [`patterns/evidence-preserving-rag.md`](patterns/evidence-preserving-rag.md)
- [`docs/evaluation/evaluation-engineering.md`](docs/evaluation/evaluation-engineering.md)
- [`docs/learning-notes/phase-6-evaluation.md`](docs/learning-notes/phase-6-evaluation.md)
- [`patterns/behavior-contract-gate.md`](patterns/behavior-contract-gate.md)
- [`docs/safety/safety-and-hitl.md`](docs/safety/safety-and-hitl.md)
- [`docs/learning-notes/phase-7-safety-hitl.md`](docs/learning-notes/phase-7-safety-hitl.md)
- [`patterns/durable-approval-boundary.md`](patterns/durable-approval-boundary.md)
- [`docs/production/production-engineering.md`](docs/production/production-engineering.md)
- [`docs/learning-notes/phase-8-production.md`](docs/learning-notes/phase-8-production.md)
- [`patterns/replaceable-production-envelope.md`](patterns/replaceable-production-envelope.md)
- [`docs/patterns/pattern-catalog.md`](docs/patterns/pattern-catalog.md)
- [`docs/learning-notes/phase-9-pattern-catalog.md`](docs/learning-notes/phase-9-pattern-catalog.md)
- [`patterns/catalog.json`](patterns/catalog.json)
- [`labs/09-pattern-catalog`](labs/09-pattern-catalog/)
- [`agent-garden/concepts.md`](agent-garden/concepts.md)
- [`agent-garden/discoverability-contract.md`](agent-garden/discoverability-contract.md)
- [`agent-garden/metadata-surfaces.json`](agent-garden/metadata-surfaces.json)
- [`agent-garden/catalog-entry.schema.json`](agent-garden/catalog-entry.schema.json)
- [`agent-garden/discovery-catalog.json`](agent-garden/discovery-catalog.json)
- [`docs/learning-notes/phase-10-agent-garden.md`](docs/learning-notes/phase-10-agent-garden.md)
- [`labs/10-agent-garden-discovery`](labs/10-agent-garden-discovery/)
- [`agent-garden/blueprint-schema.md`](agent-garden/blueprint-schema.md)
- [`agent-garden/blueprints`](agent-garden/blueprints/)
- [`docs/learning-notes/phase-11-blueprints.md`](docs/learning-notes/phase-11-blueprints.md)
- [`labs/11-blueprint-schema`](labs/11-blueprint-schema/)

## Environment Notes

- Local Python: 3.10.12.
- `uv` is not installed.
- Lab-local `.venv` contains editable `google-adk 2.6.3` from the exact pinned
  `/tmp/adk-python` commit.
- `make verify` passes: repository invariants plus 128 offline tests.
- `make verify-adk` passes: 74 ADK-backed tests plus seven trace renderers and
  baseline/broken evaluation exit checks.
- `make verify-workflows` passes: 12 ADK-backed tests plus a 79 KB JSON
  evidence bundle.
- `make verify-multi-agent` passes: 10 ADK-backed tests plus a 35,991-byte JSON
  evidence bundle.
- `make verify-context-memory` passes: 13 ADK-backed tests plus a deterministic
  28,792-byte JSON evidence bundle.
- `make verify-rag` passes: 10 ADK-backed tests plus a deterministic
  20,460-byte JSON evidence bundle.
- `make verify-evaluation` passes: 6 ADK-backed cross-phase tests, baseline
  exit `0`, expected broken exit `1` and a deterministic 90,166-byte evidence
  bundle.
- `make verify-safety-hitl` passes: 15 ADK-backed tests and a deterministic
  65,971-byte evidence bundle.
- `make verify-production` passes: 18 dependency-free tests, baseline exit `0`,
  expected broken exit `1` and a deterministic 43,765-byte evidence bundle.
- `make verify-pattern-catalog` passes: 14 dependency-free tests, baseline
  exit `0`, expected broken exit `1` and a deterministic 3,327-byte evidence
  bundle.
- `make verify-agent-garden-discovery` passes: 16 dependency-free tests,
  baseline exit `0`, expected broken exit `1` and a deterministic 5,578-byte
  evidence bundle.
- `make verify-blueprints` passes: 19 dependency-free tests, baseline exit
  `0`, expected broken exit `1` and a deterministic 4,383-byte evidence
  bundle.
- Live-model execution remains unverified until credentials are configured.
- Lab 02 recreates Runner/root objects but retains one
  `InMemorySessionService`; it does not prove durable process recovery.
- Upstream clones used for Phase 0 are under `/tmp` and may disappear between
  sessions; re-clone at the pinned commits when needed.

## Next Actions

1. Write ADRs for Catalog registry, Blueprint validator, scaffold renderer,
   evaluation adapter and release ledger ownership.
2. Draw the component/data-flow model from selection through validate,
   scaffold, test, promote and rollback.
3. Define which artifacts are immutable, content-addressed or mutable indexes.
4. Define trust, access-control and extension boundaries without selecting a
   distributed runtime prematurely.
5. Walk all three Phase 11 Blueprints through the proposed lifecycle and
   remove any component not required by all relevant paths.
6. Record the Phase 13 CLI surface only after component ownership is stable.
