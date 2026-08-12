# Mini Agent Garden MVP Architecture

Research snapshot: 2026-08-12.

## Question

> 哪些platform components已被Catalog、Blueprint、evaluation與production
> contracts反覆證明必要，又不需要過早引入distributed system？

## Component Model

MVP包含六個components：

| Component | Authority | Credential scope | Owned artifacts |
|---|---|---|---|
| Catalog Registry | Stable Agent discovery與Implementation selection | none | `catalog-index`, `implementation-selection` |
| Contract Validator | Catalog/Blueprint/source與cross-domain invariants | source-read | `validation-report` |
| Project Renderer | Pure, regenerable Project Instance rendering | none | `project-instance` |
| Deployment Controller | Build, stage, promote與target rollback | target-scoped | `release-candidate`, `deployment-status` |
| Behavior Gate | Execute exact candidate與blocking metrics | sandboxed-execution | `behavior-report` |
| Release Ledger | Append promotion evidence與plan rollback | ledger-write | `release-record`, `rollback-plan` |

CLI只負責呼叫components。它不新增Catalog、policy、deployment或release
authority。

## Why Six Components

初始候選責任看起來只有registry、validator、renderer、evaluation與release
ledger五類，但production evidence要求再拆一層：

- Deployment Controller需要target credentials並操作mutable control-plane
  status。
- Release Ledger只需要append-only evidence write，不應取得target
  credentials。
- Contract Validator解析trusted source與static contracts。
- Behavior Gate執行candidate與custom metric code，必須在sandbox boundary。

將這兩組責任合併，會讓mutable target status冒充release truth，或讓static
validation取得不必要的code-execution權限。

## Artifact And Storage Boundary

| Storage class | Write model | Artifacts |
|---|---|---|
| Version control | reviewed commit | Catalog index, Blueprint, Implementation source |
| Workspace | replaceable/regenerable | selection, Project Instance, Rollback Plan |
| Content-addressed store | digest-addressed | validation report, candidate, behavior report |
| Append-only ledger | append-only | Release Record |
| Target control plane | mutable operational cache | deployment status |
| External secret manager | external API | secret reference only |

No internal artifact permits secret material. Secret values never enter
Blueprint, Project Instance, evaluation evidence or Release Record.

## Release And Rollback

```text
Catalog Registry
  discover -> Implementation Selection
Contract Validator
  validate -> Validation Report
Project Renderer
  render -> Project Instance
Deployment Controller
  stage -> Release Candidate + Deployment Status
Behavior Gate
  evaluate -> Behavior Report
Deployment Controller
  promote -> Deployment Status
Release Ledger
  record -> Release Record
```

Rollback走不同authority path：

```text
Release Ledger: Release Record -> Rollback Plan
Deployment Controller: Rollback Plan + Secret Reference -> Deployment Status
```

Ledger決定哪個immutable release可回復；target adapter決定Cloud Run、Agent
Runtime或其他platform如何執行。

## Trust Boundaries

九個boundaries明確標記：

- Registry selection進入validation；
- Agent team提供Blueprint與Implementation source；
- validation report進入pure renderer；
- Project Instance進入credentialed deployment；
- secret reference進入deployment；
- candidate進入sandboxed evaluation；
- behavior report授權promotion；
- candidate/report/status進入append-only ledger；
- rollback plan回到credentialed deployment。

Passing validation不能授權promotion；passing behavior report也不能改寫Catalog
或Blueprint。

## Extension Boundaries

`architecture-kind`是typed union。新增architecture需要：

- Blueprint schema branch；
- semantic validator；
- lifecycle walkthrough與behavior evidence。

以下是external adapters：

- source resolver；
- scaffold renderer；
- runtime service binding；
- evaluation metric；
- deployment target；
- release store。

Adapter不得覆蓋Catalog identity、immutable source、state ownership、blocking
policy、secret policy或release evidence。

## Blueprint Walkthroughs

三份Phase 11 Blueprints使用相同platform lifecycle：

| Blueprint | Architecture | Target adapter | Architecture-specific checks |
|---|---|---|---|
| `order-support-read-only` | single Agent | Cloud Run | typed tool contracts |
| `research-workflow-rag` | Workflow/RAG | Agent Runtime | graph + retrieval provenance |
| `case-triage-with-approval` | multi-agent/HITL | Cloud Run | delegation + approval replay |

共用lifecycle不表示共用runtime implementation。Contract Validator與Behavior
Gate依Blueprint宣告選擇architecture-specific validators與blocking metrics。

## Deliberate Invalid Cases

Lab 12的15個mutations證明下列boundary會fail closed：

- duplicated artifact authority；
- credential scope escalation；
- secret material propagation；
- mutable candidate/report/release history；
- deployment cache冒充authority；
- untyped architecture plugin；
- adapter覆蓋behavior gate；
- promotion或record缺少evidence；
- walkthrough缺少architecture validator或blocking metric；
- ADR evidence遺失。

## ADRs

- [`0001-authority-separated-components.md`](adrs/0001-authority-separated-components.md)
- [`0002-git-first-artifacts.md`](adrs/0002-git-first-artifacts.md)
- [`0003-pure-project-renderer.md`](adrs/0003-pure-project-renderer.md)
- [`0004-evaluation-before-promotion.md`](adrs/0004-evaluation-before-promotion.md)
- [`0005-deployment-ledger-separation.md`](adrs/0005-deployment-ledger-separation.md)
- [`0006-typed-core-external-adapters.md`](adrs/0006-typed-core-external-adapters.md)

## Limits

- Storage classes是required semantics，不是production vendor selection。
- Walkthrough產生deterministic digests，沒有執行cloud deployment。
- Deployment success與Release Record尚未transactionally linked。
- Registry ACL、signed provenance、concurrent writers與durable job execution
  留給後續implementation。
- Phase 13 CLI必須呼叫這六個authority boundaries，不能用shared mutable
  internal model繞過它們。
