# Repository Map

本文件回答三個問題：

1. 官方 repository 中實際存在什麼，而不是 README 宣稱什麼。
2. 哪些 source 適合學 Agent architecture，哪些適合學 recipe 與 production
   productization。
3. 應按什麼 dependency order 讀取 15 個代表 study units。

Research snapshot 為 2026-08-12；所有結論固定在
[`references/upstream-lock.yaml`](../references/upstream-lock.yaml) 的 commit。

## Evidence Rules

- **Source fact**：可由固定 commit 的 code、manifest、policy 或 test 直接確認。
- **Inference**：從多個 source facts 推導的 engineering interpretation。
- **Open**：需要 runtime experiment、cloud resource 或 maintainer clarification。
- README 只用來理解 intent；若 README、dependency pin、code 與 test 不一致，
  以可執行 source 和 observed behavior 為準，並記錄差異。

## Source Landscape

| Repository | Pinned role | Current-state finding | How this project uses it |
|---|---|---|---|
| `google/adk-samples` | Agent recipes and legacy samples | Active recipe roots與 frozen legacy roots 並存；sample 橫跨 ADK 1.x 與 ADK 2.0 | Architecture cases、recipe contract、failure modes |
| `GoogleCloudPlatform/agent-starter-pack` | Production template engine | 已進入 maintenance mode，只接受 critical fixes | 研究 layered template composition、deployment、CI/CD、observability |
| `google/adk-python` | Runtime implementation | ADK 2.0 加入 graph `Workflow`/Task API，且有 breaking changes | 判定 `Agent`、`Runner`、`Session`、`Event`、`Tool` 的 authoritative semantics |
| `google/agents-cli` | Current project lifecycle | 接手 scaffold、eval、deploy、publish、observe lifecycle | 研究目前的 production workflow，不把 maintenance-mode CLI 當新產品基線 |

這四個 repository 不是同一層 abstraction：

```text
adk-python
  runtime contracts and execution semantics
        |
        v
adk-samples
  architecture examples + reusable recipe contract
        |
        v
agent-starter-pack --------> agents-cli
  historical template        current lifecycle tooling
  composition evidence
```

## `adk-samples` Topology

### Active Recipe Model

`.github/policy.yml` 定義目前可接受變更的三種 root：

```text
core/<language>/<recipe>       curated, maintainers own quality bar
contrib/<language>/<recipe>    community contribution surface
skills/<vertical>/<solution>   focused installable solution contract
```

Source facts：

- 每個 recipe 都必須有 `manifest.yaml` 與 `README.md`。
- `core/` 額外要求 `AGENTS.md`。
- Python recipe 額外要求 `pyproject.toml`、`uv.lock`、`.env.example` 與
  `tests/test_runnability.py`。
- `core` default cap 是 500 files/50 MB；`contrib` 與 `skills` default cap
  是 70 files/2 MB。
- `skills/` policy 已定義 `SKILL.md`、`EVAL.yaml` 與 `scripts/` contract，
  但此 snapshot 尚無實際 solution，只有 placeholder。

Active Python recipes 共 11 個：

| Tier | Recipes |
|---|---|
| `core/python` | `ambient-expense-agent`, `cross-session-memory`, `deep-search`, `genmedia-for-commerce`, `long-horizon-harness`, `oauth-user-consent-flow`, `rag-agent-search`, `rag-vector-search`, `safety-plugins` |
| `contrib/python` | `financial-advisor`, `market-research-agent` |

`core/rag-agent-search` 和 `core/rag-vector-search` 另有 transitional duplicate；
依 policy 的 canonical layout 是 `core/python/<recipe>`。兩組檔案並不完全相同，
因此不能把 duplicate path 當成 alias。

### Frozen Legacy Collection

下列 root 在 policy 中為 frozen；新增或修改會被 CI 拒絕，migration、delete 與
具 override label 的變更除外：

```text
python/agents
go/agents
java/agents
kotlin/agents
typescript/agents
```

這些路徑仍有 40 個 samples，對 architecture study 很有價值，但不代表目前的
contribution contract。

| Language | Count | Legacy samples |
|---|---:|---|
| Python | 34 | `academic-research`, `adk-ae-oauth`, `agent-observability-bq`, `agent-skills-tutorial`, `ambient-expense-agent`, `brand-aligned-presentations`, `brand-search-optimization`, `customer-service`, `cyber-guardian-agent`, `data-science`, `deep-search`, `economic-research-agent`, `financial-advisor`, `fomc-research`, `genmedia-for-commerce`, `global-kyc-agent`, `high-volume-document-analyzer`, `image-scoring`, `invoice-processing`, `llm-auditor`, `marketing-agency`, `memory-bank`, `multiformat-hybrid-rag`, `nurse-handover`, `on-brand-genmedia`, `personalized-shopping`, `safety-plugins`, `sdlc-task-planner`, `sdlc-technical-designer`, `sdlc-user-story-refiner`, `small-business-loan-agent`, `software-bug-assistant`, `travel-concierge`, `youtube-analyst` |
| Go | 2 | `financial-advisor`, `llm-auditor` |
| Java | 2 | `software-bug-assistant`, `time-series-forecasting` |
| Kotlin | 1 | `llm-auditor` |
| TypeScript | 1 | `customer_service` |

### Manifest Contract

`manifest-schema.json` requires:

```text
type, status, language, description, ownership
```

It optionally records:

```text
deployable, large, architecture.agent, architecture.stateful,
architecture.datasources, dependencies.libraries, dependencies.services,
license, tags
```

**Inference:** this is a catalog, ownership and validation contract, not yet a
complete runtime blueprint. It cannot express tool schemas, state ownership,
policy hooks, evaluation gates, secrets, SLOs, cost limits or upgrade behavior.
Those missing concerns will be tested before the mini Agent Garden schema is
designed.

## Repeated Architecture Families

The directories are organized by contribution lifecycle, not by architecture.
Reading the source produces these recurring families:

| Family | Characteristic decision | Representative evidence |
|---|---|---|
| Single LLM Agent | Model chooses among narrow tools inside one responsibility boundary | `customer-service`, Starter Pack `adk` |
| Deterministic composition | Code fixes ordering, fan-out or loop termination | `llm-auditor`, `deep-search` |
| Coordinator/specialists | A coordinator delegates bounded work to specialist agents | `financial-advisor`, `data-science` |
| State and memory | Session state supports current work; memory crosses sessions | `cross-session-memory`, `memory-bank` |
| Retrieval | Managed search or explicit vector pipeline grounds responses | `rag-agent-search`, `rag-vector-search` |
| Safety and policy | Callbacks/plugins inspect or block model and tool boundaries | `safety-plugins`, `customer-service` |
| Human-in-the-loop | Runtime pauses for user input or approval | `oauth-user-consent-flow`, `ambient-expense-agent`, `long-horizon-harness` |
| Observability/evaluation | Events, traces and domain metrics become operational evidence | `agent-observability-bq`, Starter Pack evalsets |
| Production packaging | Agent overlay is composed with language, deployment and shared layers | Agent Starter Pack, Agents CLI |

## Fifteen Representative Study Units

Selection criteria:

- cover the smallest useful Agent through long-horizon and production concerns;
- include successful patterns and brittle implementation choices;
- preserve ADK version and active/legacy status;
- avoid selecting multiple samples that teach the same primary decision.

The table rows are stable IDs used by roadmap and future case studies.

| ID | Source path | Status/version boundary | Primary lesson | What to challenge |
|---|---|---|---|---|
| R01 | `agent-starter-pack/agent_starter_pack/agents/adk` | Maintenance-mode template; ADK 1.x lineage | Minimal ReAct-style Agent plus `App`, tests and template metadata | How much generated production structure is useful before domain behavior exists? |
| R02 | `adk-samples/python/agents/customer-service` | Frozen legacy; ADK 1.x | One Agent, many tools, callback policy and session-state initialization | Mocked writes, blocking rate-limit callback and weak persistence boundaries |
| R03 | `adk-samples/python/agents/llm-auditor` | Frozen legacy; ADK 1.x | Small `SequentialAgent` critic-to-reviser pipeline | Whether both stages need LLM autonomy and how failure propagates |
| R04 | `adk-samples/python/agents/global-kyc-agent` | Frozen legacy; ADK 1.x private internals | Routing plus nested sequential/parallel work | Monkey-patched `_run_async_impl` and private helpers as an upgrade failure mode |
| R05 | `adk-samples/core/python/deep-search` | Active core; mainly ADK 1.x composite APIs | Planning, sequential research, iterative refinement, state and escalation | Sparse behavioral eval and migration path to ADK 2.0 `Workflow` |
| R06 | `adk-samples/contrib/python/financial-advisor` | Active contrib; ADK 1.x-style `AgentTool` | Coordinator with bounded financial specialists | Direct `AgentTool` deprecation direction and whether delegation actually executes as described |
| R07 | `adk-samples/python/agents/data-science` | Frozen legacy; ADK 1.x | Specialist wrappers, `ToolContext` handoff, databases and MCP | Import-time configuration, telemetry side effects and state coupling |
| R08 | `adk-samples/core/python/cross-session-memory` | Active core; ADK 1.x | Preload memory and commit session history through a callback | Local in-memory service is not durable cross-session memory; missing recall E2E gate |
| R09 | `adk-samples/core/python/rag-agent-search` | Active core; ADK 2.x | Thin Agent over managed Vertex AI Search and GCS connector | Custom eval score exists without a hard minimum gate |
| R10 | `adk-samples/core/python/rag-vector-search` | Active core; ADK 2.x | Explicit ingestion, embeddings and Vector Search lifecycle | Extra operational ownership versus managed search |
| R11 | `adk-samples/core/python/safety-plugins` | Active core; ADK 1.x | Application-wide LLM judge and Model Armor plugins | Documented coverage differs from code; tests do not exercise enforcement |
| R12 | `adk-samples/core/python/oauth-user-consent-flow` | Active core; ADK 1.x | Credential negotiation, user consent pause and resumed tool call | Cached credential lifetime, packaging leftovers and failure recovery |
| R13 | `adk-samples/core/python/ambient-expense-agent` | Active core; ADK 2.0 Workflow | Event-driven Pub/Sub intake, deterministic threshold and approval request | In-memory sessions can lose approvals; threshold duplicated across boundaries |
| R14 | `adk-samples/core/python/long-horizon-harness` | Active core; ADK 2.5 range | Environment interfaces, guardrails, secrets, resumability and self-improving memory | Which interfaces are essential versus harness-specific complexity |
| R15 | `adk-samples/python/agents/agent-observability-bq` | Frozen legacy; ADK 1.x | BigQuery toolset plus application analytics plugin | Telemetry schema, privacy, cost and whether observations produce actionable gates |

### Dependency-Ordered Reading Path

The ID order is intentionally not the table order alone. Use this sequence:

```text
R01 minimal boundary
  -> R02 tool and callback pressure
  -> R03 deterministic sequence
  -> R05 loop, state and escalation
  -> R04 private-runtime failure mode
  -> R06 coordinator/specialists
  -> R07 stateful specialist and MCP integration
  -> R08 memory across sessions
  -> R09 managed retrieval
  -> R10 explicit retrieval pipeline
  -> R12 credential-driven HITL
  -> R13 event-driven Workflow HITL
  -> R11 global safety policy
  -> R15 observability
  -> R14 long-horizon integration
```

R04 is read after a clean deterministic example so the private-extension risk is
visible. R11 is delayed until tool, model and application boundaries are known;
otherwise "safety plugin" becomes a label without a coverage model.

## Starter Pack Product Map

The Starter Pack source separates four independently changing dimensions:

```text
_shared base
    + language base (python/go/java/typescript)
    + deployment target (agent_engine/cloud_run/gke)
    + agent overlay or remote template
    -> rendered project
```

`process_template` performs this composition before Cookiecutter rendering.
The agent overlays in the pinned snapshot are:

```text
adk, adk_a2a, adk_go, adk_java, adk_live, adk_ts, agentic_rag, langgraph
```

The template configuration records description, example question, data-ingestion
and session requirements, supported deployment targets, extra dependencies,
tags and frontend choices. Generated projects add:

- agent source and unit tests;
- evalsets, integration tests and load tests;
- Terraform and deployment-target resources;
- Cloud Build/GitHub Actions automation;
- telemetry, secrets and environment configuration;
- optional frontend and data ingestion.

**Inference:** the valuable abstraction is orthogonal composition, not the
number of generated files. Agent architecture, language/runtime, deployment
target and organizational delivery policy should not be one monolithic template.

## Current Lifecycle Map

Because Starter Pack is in maintenance mode, current lifecycle study continues
in `google/agents-cli`:

| Lifecycle | Evidence in `agents-cli` |
|---|---|
| Create/adopt | `scaffold`, `setup`, manifest-driven `ProjectConfig` |
| Develop | `run`, `dev`, install/lint/playground commands |
| Evaluate | generate, grade, compare, analyze, optimize, synthesize |
| Ship | `infra`, `deploy`, `publish` |
| Agent-assisted work | bundled skills for ADK, workflow, eval, deploy, publish and observability |

`agents-cli-manifest.yaml` is lifecycle metadata. It should not be assumed to be
the final reusable Agent blueprint schema; that claim remains an experiment for
the Agent Garden phase.

## Architecture Classification

| Level | Questions the source must answer | Study units |
|---|---|---|
| Foundational | What is the Agent boundary? What is deterministic? What data crosses a tool boundary? | R01-R03 |
| Intermediate | How do loops, state, delegation, databases and memory compose? | R04-R08 |
| Advanced | Who owns retrieval, credentials, event-driven work, safety and long-running recovery? | R09-R14 |
| Production | How are traces, evaluation, templates, deployment and lifecycle governance enforced? | R15 plus Starter Pack/Agents CLI |

## Findings That Changed the Plan

1. **README-only assumption:** `adk-samples` is a uniform sample gallery.
   **Source correction:** it is an active recipe system plus a larger frozen
   legacy collection and transitional duplicate paths.
2. **Version assumption:** samples can be compared as one ADK execution model.
   **Source correction:** ADK 1.x composite-agent patterns and ADK 2.0 graph
   `Workflow` coexist and require explicit migration framing.
3. **Production assumption:** Agent Starter Pack is the current generator.
   **Source correction:** it is maintenance-only; `agents-cli` owns active
   lifecycle development.
4. **Manifest assumption:** recipe metadata is already a reusable blueprint.
   **Source correction:** the schema is deliberately small and omits runtime,
   policy, eval and SLO contracts.
5. **Sample-quality assumption:** official means production-safe.
   **Source correction:** private API patches, blocking callbacks, mocked
   persistence, weak eval gates and documentation drift are present.

## Open Verification Work

- Run selected ADK 1.x samples against their exact lockfiles and classify actual
  breakage under ADK 2.0.
- Build equivalent 1.x composite-agent and 2.0 `Workflow` traces, then compare
  event, branch, resumability and eval semantics.
- Verify Agent-as-tool replacement behavior with `mode="single_turn"`
  sub-agents.
- Measure managed Search versus explicit Vector Search using the same corpus and
  retrieval evalset.
- Test safety-plugin coverage at model input/output and tool input/output
  boundaries.
- Render equivalent projects with Starter Pack and Agents CLI, then diff the
  lifecycle contracts rather than only generated file count.

Primary source links for each runtime and repository concern are indexed in
[`references/source-index.md`](../references/source-index.md).
