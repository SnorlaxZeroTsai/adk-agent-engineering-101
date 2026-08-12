# Project State

Last updated: 2026-08-12

## Current Goal

Start Phase 6 by extracting a reusable evaluation contract from the completed
Agent, Workflow, multi-agent, context/memory and RAG labs.

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
- First candidate pattern: deterministic Workflow.
- Phase 3 source comparison of `chat`, `single_turn` and `task` Agent modes.
- Lab 03 typed case-triage capability across function, single-turn, transfer
  and task-delegation boundaries.
- Transfer continuation, task validation recovery and hard specialist failure
  experiments.
- Overlapping-responsibility and shared-state conflict experiments.
- 7 Lab 03 offline tests and 10 ADK-backed multi-agent tests.
- Second candidate pattern: bounded specialist.
- Phase 4 source comparison of transient model context, instruction/state
  assembly, state scopes, artifact services and memory services.
- Lab 04 common support dossier across transient context, Session state,
  explicit artifact loading and preloaded cross-session memory.
- Stale-state, 20 KB context, state-scope, artifact lifecycle, memory
  retention/deletion and intentional cross-user leakage experiments.
- 6 Lab 04 offline tests and 13 ADK-backed context/memory tests.
- Third candidate pattern: data lifecycle placement.
- Phase 5 source comparison of native `VertexAiSearchTool`, Discovery Engine
  fallback, managed connector ingestion and explicit Vector Search ingestion.
- Lab 05 versioned/ACL corpus across native managed Search and explicit
  FunctionTool retrieval.
- Retrieval recall/precision, answer, citation, ACL, stale-version and deletion
  gates over five shared query cases.
- Provenance-loss, unfiltered-search, stale-index and deletion-lag breakages.
- 10 Lab 05 offline tests and 10 ADK-backed RAG tests.
- Fourth candidate pattern: evidence-preserving RAG.

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
- Which recipe manifest fields are catalog metadata versus runtime-enforceable
  blueprint contracts?
- What minimum governance metadata is justified for the mini Agent Garden?
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
- Which deterministic and probabilistic eval thresholds should be release
  blockers rather than advisory signals?

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

## Environment Notes

- Local Python: 3.10.12.
- `uv` is not installed.
- Lab-local `.venv` contains editable `google-adk 2.6.3` from the exact pinned
  `/tmp/adk-python` commit.
- `make verify` passes: repository invariants plus 43 offline tests.
- `make verify-adk` passes: 53 ADK-backed tests plus five trace renderers.
- `make verify-workflows` passes: 12 ADK-backed tests plus a 79 KB JSON
  evidence bundle.
- `make verify-multi-agent` passes: 10 ADK-backed tests plus a 35,991-byte JSON
  evidence bundle.
- `make verify-context-memory` passes: 13 ADK-backed tests plus a deterministic
  28,792-byte JSON evidence bundle.
- `make verify-rag` passes: 10 ADK-backed tests plus a deterministic
  20,460-byte JSON evidence bundle.
- Live-model execution remains unverified until credentials are configured.
- Lab 02 recreates Runner/root objects but retains one
  `InMemorySessionService`; it does not prove durable process recovery.
- Upstream clones used for Phase 0 are under `/tmp` and may disappear between
  sessions; re-clone at the pinned commits when needed.

## Next Actions

1. Inspect ADK eval schemas, evaluators and `agents-cli` generate/grade/compare
   lifecycle at the pinned commits.
2. Normalize existing lab cases into a reusable typed eval-case/result model.
3. Separate deterministic contract metrics from LLM-judge quality metrics.
4. Add deliberately broken variants from Agent, Workflow, delegation, memory
   and RAG phases to a CI-style regression gate.
5. Produce per-dimension failure explanations and explicit blocking thresholds.
