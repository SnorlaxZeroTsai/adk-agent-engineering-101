# Project State

Last updated: 2026-08-12

## Current Goal

Start Phase 4 by holding one support task constant and comparing prompt
context, typed Session state, artifacts and cross-session memory.

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

## Environment Notes

- Local Python: 3.10.12.
- `uv` is not installed.
- Lab-local `.venv` contains editable `google-adk 2.6.3` from the exact pinned
  `/tmp/adk-python` commit.
- `make verify` passes: repository invariants plus 27 offline tests.
- `make verify-adk` passes: 30 ADK-backed tests plus three trace renderers.
- `make verify-workflows` passes: 12 ADK-backed tests plus a 79 KB JSON
  evidence bundle.
- `make verify-multi-agent` passes: 10 ADK-backed tests plus a 35,991-byte JSON
  evidence bundle.
- Live-model execution remains unverified until credentials are configured.
- Lab 02 recreates Runner/root objects but retains one
  `InMemorySessionService`; it does not prove durable process recovery.
- Upstream clones used for Phase 0 are under `/tmp` and may disappear between
  sessions; re-clone at the pinned commits when needed.

## Next Actions

1. Inspect `State`, instruction/context providers, artifact services and memory
   APIs at the pinned runtime.
2. Define one datum set with explicit writer, reader, lifecycle and retention.
3. Implement prompt-only, Session-state, artifact and memory variants.
4. Inject stale state, oversized context, cross-user leakage and deletion/TTL
   failures.
5. Compare request contents, persisted deltas, artifact references and
   cross-session recall.
