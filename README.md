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
| Evaluation | Cross-phase CI-style gate complete | [`docs/evaluation/evaluation-engineering.md`](docs/evaluation/evaluation-engineering.md) |
| Safety and HITL | Local/scripted enforcement and approval baseline complete | [`docs/safety/safety-and-hitl.md`](docs/safety/safety-and-hitl.md) |
| Production engineering | Offline render, promotion and rollback baseline complete | [`docs/production/production-engineering.md`](docs/production/production-engineering.md) |
| Pattern catalog | Seven patterns normalized and mechanically validated | [`docs/patterns/pattern-catalog.md`](docs/patterns/pattern-catalog.md) |
| Agent Garden discoverability | Catalog/scaffold/runtime/governance ownership baseline complete | [`agent-garden/discoverability-contract.md`](agent-garden/discoverability-contract.md) |
| Executable Blueprint schema | Three architecture branches, semantic validation and v0.1 migration complete | [`agent-garden/blueprint-schema.md`](agent-garden/blueprint-schema.md) |
| MVP architecture | Six authority-separated components and lifecycle contract complete | [`agent-garden/architecture.md`](agent-garden/architecture.md) |
| Executable labs | 146 offline + 74 ADK runtime tests passing | [`labs/`](labs/) |
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
7. Run the cross-architecture evaluation gate in Lab 06.
8. Compare safety enforcement and human approval in Lab 07.
9. Render and break replaceable production envelopes in Lab 08.
10. Validate the normalized pattern catalog in Lab 09.
11. Reverse engineer catalog, scaffold, runtime and governance metadata in
    Lab 10.
12. Validate three materially different executable Blueprints and their shared
    schema in Lab 11.
13. Validate the six-component MVP architecture and lifecycle in Lab 12.
14. Use that architecture to implement the mini Agent Garden.

The detailed dependency order and phase exit criteria live in
[`docs/roadmap.md`](docs/roadmap.md).

## Prerequisites

| Module | Required |
|---|---|
| Documentation and source-reading exercises | Git, a text editor |
| Lab 01/02/03/04/05/06/07/08/09/10/11/12 deterministic tests | Python 3.10+ |
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
| `06-evaluation` | Grade Agent, Workflow, specialist, memory and RAG behavior with per-case blocking metrics and a real CI exit status | Offline metric tests use stdlib; trace generation reuses the pinned ADK environment |
| `07-safety-hitl` | Compare prompt-only, plugin and durable approval boundaries under unsafe I/O, rejection, expiry and replay | Offline approval tests use stdlib; scripted policy/confirmation traces reuse the pinned ADK environment |
| `08-production-engineering` | Render target-independent Agent/eval contracts with replaceable runtime, deployment, telemetry, promotion and rollback ownership | Stdlib-only policy, release and deterministic render tests; no cloud credentials required |
| `09-pattern-catalog` | Validate normalized pattern manifests, claim evidence, relation boundaries and invalid catalog cases | Stdlib-only schema and repository evidence checks; no ADK install required |
| `10-agent-garden-discovery` | Separate recipe, template and project metadata; validate stable identity, immutable source, compatibility, lifecycle and assurance | Stdlib-only catalog and source-ownership checks; no ADK install required |
| `11-blueprint-schema` | Validate single-Agent, Workflow/RAG and multi-agent/HITL Blueprints, semantic references and v0.1 migration | Stdlib-only schema, Git object and Python AST checks; no ADK install required |
| `12-mvp-architecture` | Validate component authority, artifact/storage/trust boundaries, release/rollback flow and three Blueprint walkthroughs | Stdlib-only architecture, repository reference and deterministic digest checks; no ADK install required |

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

Run only Lab 06 offline tests:

```bash
cd labs/06-evaluation
python3 -m unittest discover -s tests -v
```

Run only Lab 07 offline tests:

```bash
cd labs/07-safety-hitl
python3 -m unittest discover -s tests -v
```

Run only Lab 08 offline tests:

```bash
cd labs/08-production-engineering
python3 -m unittest discover -s tests -v
```

Run only Lab 09 offline tests:

```bash
cd labs/09-pattern-catalog
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

Run the cross-architecture evaluation gate:

```bash
make verify-evaluation
```

Run only the safety and HITL runtime gate:

```bash
make verify-safety-hitl
```

Run the production render and release gate:

```bash
make verify-production
```

Run the normalized pattern catalog gate:

```bash
make verify-pattern-catalog
```

Run the executable Blueprint gate:

```bash
make verify-blueprints
```

Run the MVP architecture gate:

```bash
make verify-mvp-architecture
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
