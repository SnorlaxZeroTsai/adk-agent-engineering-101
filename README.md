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
| Workflow engineering | Deterministic local/runtime baseline complete | [`docs/workflows/deterministic-workflows.md`](docs/workflows/deterministic-workflows.md) |
| Multi-agent systems | Local/scripted specialist baseline complete | [`docs/multi-agent/specialist-boundaries.md`](docs/multi-agent/specialist-boundaries.md) |
| State, context and memory | Local/scripted lifecycle baseline complete | [`docs/context/data-lifecycle.md`](docs/context/data-lifecycle.md) |
| RAG engineering | Local/scripted retrieval and citation baseline complete | [`docs/rag/rag-engineering.md`](docs/rag/rag-engineering.md) |
| Executable labs | 43 offline + 53 ADK runtime tests passing | [`labs/`](labs/) |
| Pattern catalog | Four candidates extracted | [`patterns/`](patterns/) |
| Mini Agent Garden | Planned | [`mini-agent-garden/README.md`](mini-agent-garden/README.md) |

Research snapshot: 2026-08-12. Exact upstream commits are pinned in
[`references/upstream-lock.yaml`](references/upstream-lock.yaml).

## Recommended Learning Order

1. Read [`docs/repo-map.md`](docs/repo-map.md) to understand the source landscape
   and the ADK 1.x versus 2.0 boundary.
2. Study Agent, Tool and execution-model foundations, then run Lab 01.
3. Run the legacy composite versus graph Workflow comparison in Lab 02.
4. Compare specialist execution boundaries in Lab 03.
5. Compare transient context, state, artifacts and memory in Lab 04.
6. Compare managed Search and explicit vector retrieval in Lab 05.
7. Add evaluation and safety.
8. Study production packaging only after the Agent architecture is understood.
9. Use the accumulated evidence to design and implement the mini Agent Garden.

The detailed dependency order and phase exit criteria live in
[`docs/roadmap.md`](docs/roadmap.md).

## Prerequisites

| Module | Required |
|---|---|
| Documentation and source-reading exercises | Git, a text editor |
| Lab 01/02/03/04/05 deterministic tests | Python 3.10+ |
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
| `02-workflow-engineering` | Compare legacy sequence/parallel/loop with graph Workflow, retry, output and resume | Offline domain tests use stdlib; runtime comparison reuses the pinned ADK environment |
| `03-multi-agent` | Compare function, single-turn, transfer and task specialist boundaries under failure and conflict | Offline domain tests use stdlib; scripted comparison reuses the pinned ADK environment |
| `04-context-and-memory` | Compare transient model context, state scopes, artifact versions and memory retention under isolation/deletion failures | Offline domain tests use stdlib; scripted comparison reuses the pinned ADK environment |
| `05-rag-engineering` | Compare native managed Search and explicit vector retrieval under provenance, ACL, version and deletion failures | Offline retrieval tests use stdlib; scripted ADK comparison reuses the pinned environment |

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

Run only Lab 02 offline tests:

```bash
cd labs/02-workflow-engineering
python3 -m unittest discover -s tests -v
```

Run only Lab 03 offline tests:

```bash
cd labs/03-multi-agent
python3 -m unittest discover -s tests -v
```

Run only Lab 04 offline tests:

```bash
cd labs/04-context-and-memory
python3 -m unittest discover -s tests -v
```

Run only Lab 05 offline tests:

```bash
cd labs/05-rag-engineering
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

Run only the Workflow runtime gate:

```bash
make verify-workflows
```

Run only the multi-agent runtime gate:

```bash
make verify-multi-agent
```

Run only the context and memory runtime gate:

```bash
make verify-context-memory
```

Run only the RAG runtime gate:

```bash
make verify-rag
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
