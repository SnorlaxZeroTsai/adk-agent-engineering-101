# Project State

Last updated: 2026-08-12

## Current Goal

Complete ADK foundations using the pinned ADK 2.0 runtime source, then validate
tool boundaries and execution semantics with small offline-first labs.

## Completed

- Phase 0 repository reconnaissance for `google/adk-samples` and
  `GoogleCloudPlatform/agent-starter-pack`.
- Additional current-state scan of `google/adk-python` and `google/agents-cli`
  because the primary repositories now point to those projects.
- Repository map, 15 representative study units and dependency-ordered roadmap.
- Initial project structure and reproducible upstream source lock.
- First foundations module and Agent basics lab offline baseline.
- Project verifier, contract inspector and all 13 Lab 01 tests pass.

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

## Architecture Decisions

- Write learning material in Traditional Chinese while preserving official API
  and symbol names in English.
- Pin every upstream conclusion to a commit and source path.
- Label observations as source fact, inference or open question.
- Keep upstream clones outside this repository; record only immutable commit
  metadata and source links.
- Teach current ADK 2.0 semantics first, then use 1.x samples comparatively.
- Keep labs offline-testable. Live model and cloud tests are separate gates.

## Unresolved Questions

- Which ADK 1.x composite-agent patterns should be migrated to the 2.0 Workflow
  runtime, and which remain useful as LLM delegation patterns?
- What is the stable replacement for direct `AgentTool` use now that ADK 2.0
  recommends `mode="single_turn"` sub-agents?
- How should trajectory evaluation differ between graph Workflow nodes and
  conversational agent transfers?
- Which recipe manifest fields are catalog metadata versus runtime-enforceable
  blueprint contracts?
- What minimum governance metadata is justified for the mini Agent Garden?

## Relevant Sources

- [`references/upstream-lock.yaml`](references/upstream-lock.yaml)
- [`references/source-index.md`](references/source-index.md)
- [`docs/repo-map.md`](docs/repo-map.md)
- [`docs/roadmap.md`](docs/roadmap.md)
- [`docs/foundations/agent.md`](docs/foundations/agent.md)

## Environment Notes

- Local Python: 3.10.12.
- `uv` and `google-adk` are not installed in the current environment.
- Offline stdlib checks and Lab 01 tests are available.
- Live ADK execution remains unverified until dependencies and credentials are
  configured.
- `make verify` currently passes: repository invariants plus 13 Lab 01 tests.
- Upstream clones used for Phase 0 are under `/tmp` and may disappear between
  sessions; re-clone at the pinned commits when needed.

## Next Actions

1. Finish `docs/foundations/tools.md` with FunctionTool, built-in tool, MCP,
   agent-as-tool, ToolContext and async/error contracts.
2. Finish `docs/foundations/execution-model.md` from Runner, InvocationContext,
   Session and Event source.
3. Extend Lab 01 with a fake-model Runner trace after installing ADK dependencies.
4. Add the deterministic workflow lab and compare ADK 1.x composite agents with
   ADK 2.0 Workflow.
5. Update this file, the roadmap and README at each major milestone.
