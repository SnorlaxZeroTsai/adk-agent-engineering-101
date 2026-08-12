# ADK Agent Engineering 101

這是一個 learning-by-building repository。目標不是記住 Google ADK API，
而是從官方 source code 反推 Agent Engineering 的設計判斷：

- 何時使用單一 Agent、deterministic workflow、multi-agent 或 agentic RAG。
- instruction、tool、state、memory、runtime 與 policy 應如何分工。
- Agent 如何從 sample 變成可重用 recipe、template 與 production asset。
- internal Agent Garden 需要哪些 abstraction，以及哪些 abstraction 太早建立。

## Current Status

| Area | Status | Evidence |
|---|---|---|
| Phase 0 repository reconnaissance | Complete | [`docs/repo-map.md`](docs/repo-map.md) |
| Learning roadmap | Complete, expected to evolve | [`docs/roadmap.md`](docs/roadmap.md) |
| ADK foundations: Agent boundary | Scripted runtime complete; live model pending | [`docs/foundations/agent.md`](docs/foundations/agent.md) |
| ADK foundations: Tool boundary | Complete for local/runtime scope | [`docs/foundations/tools.md`](docs/foundations/tools.md) |
| ADK foundations: Execution model | Complete for in-memory scripted scope | [`docs/foundations/execution-model.md`](docs/foundations/execution-model.md) |
| First executable lab | 13 offline + 8 ADK runtime tests passing | [`labs/01-agent-basics/`](labs/01-agent-basics/) |
| Pattern catalog | Planned | [`patterns/README.md`](patterns/README.md) |
| Mini Agent Garden | Planned | [`mini-agent-garden/README.md`](mini-agent-garden/README.md) |

Research snapshot: 2026-08-12. Exact upstream commits are pinned in
[`references/upstream-lock.yaml`](references/upstream-lock.yaml).

## Recommended Learning Order

1. Read [`docs/repo-map.md`](docs/repo-map.md) to understand the source landscape
   and the ADK 1.x versus 2.0 boundary.
2. Study Agent, Tool and execution-model foundations, then run Lab 01.
3. Compare deterministic workflow with LLM-driven routing.
4. Add state, memory, multi-agent decomposition, RAG, evaluation and safety.
5. Study production packaging only after the Agent architecture is understood.
6. Use the accumulated evidence to design and implement the mini Agent Garden.

The detailed dependency order and phase exit criteria live in
[`docs/roadmap.md`](docs/roadmap.md).

## Prerequisites

| Module | Required |
|---|---|
| Documentation and source-reading exercises | Git, a text editor |
| Lab 01 deterministic tests | Python 3.10+ |
| Scripted ADK runtime tests | Python 3.10+, Git and network access for one-time bootstrap |
| Live-model lab execution | Python 3.10+, `uv` or venv, Gemini API key or Google Cloud ADC |
| Deployment modules | Google Cloud project, `gcloud`, Terraform |

Cloud credentials are not required for offline or scripted-model tests.

## Important Modules

- **Foundations:** the boundary between Agent, Tool, App, Runner, Session and Event.
- **Workflow:** which control decisions must remain deterministic.
- **Context engineering:** what belongs in prompt context, session state, artifacts
  or long-term memory.
- **Evaluation:** final response quality is only one dimension; tool selection,
  arguments, trajectory, cost and safety also matter.
- **Production:** templates, configuration, deployment and observability are
  platform engineering, not substitutes for good Agent architecture.

## Labs

| Lab | Learning objective | Runtime requirement |
|---|---|---|
| `01-agent-basics` | Build a small Agent, inspect generated tool schema, trace Runner events/state and compare failure recovery | Offline tests use stdlib; scripted runtime needs pinned ADK; live run needs credentials |

## Run

Run all dependency-free checks:

```bash
make verify
```

Run only Lab 01 offline tests:

```bash
cd labs/01-agent-basics
python3 -m unittest discover -s tests -v
```

Inspect the lab's Agent and tool contract without importing ADK:

```bash
cd labs/01-agent-basics
python3 scripts/inspect_contract.py
```

Bootstrap and verify the deterministic ADK runtime:

```bash
make bootstrap-adk
make verify-adk
```

After configuring credentials, run the interactive Agent:

```bash
cd labs/01-agent-basics
uv sync --dev
uv run adk run agent_basics
```

## Repository Layout

```text
docs/               Research notes and architecture modules
patterns/           Normalized pattern catalog
labs/               Executable learning experiments
case-studies/       Deep source studies of representative samples
agent-garden/       Product model and blueprint design
mini-agent-garden/  Prototype implementation
references/         Pinned upstream sources and evidence index
```

Read [`PROJECT_STATE.md`](PROJECT_STATE.md) before continuing work in a new
session.
