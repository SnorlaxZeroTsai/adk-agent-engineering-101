# Agent Garden Blueprint Contract

Research snapshot: 2026-08-12.

## Question

> 什麼是能同時描述single Agent、deterministic Workflow/RAG與
> multi-agent/HITL，又不把某一個app或scaffold tool硬編進platform的最小
> executable contract？

## Catalog Boundary

Blueprint只引用：

```text
catalog_ref.entry_id
catalog_ref.implementation_id
```

下列authority仍由CatalogEntry/Implementation擁有，Blueprint不得複製：

- display name、summary與classification；
- owner與lifecycle replacement；
- language與framework compatibility；
- immutable repository、revision與implementation root；
- reuse locator與assurance digest。

Blueprint擁有的是一次可驗證composition：entrypoint、architecture、
runtime bindings、policy、evaluation與lifecycle contracts。

## Derivation From Examples

Schema不是從recipe/template/project manifests做field union，而是先建立三個
materially different examples：

| Blueprint | Core implementation | Architecture-specific payload |
|---|---|---|
| `order-support-read-only` | Lab 01 | root Agent、model slot、typed tools與effect |
| `research-workflow-rag` | Lab 02 | nodes、edges、terminals、bounded loop與RAG binding |
| `case-triage-with-approval` | Lab 03 | coordinator、typed specialist、delegation與shared-state writer |

三者共同暴露八個domains：

```text
catalog_ref
architecture
runtime
policy
evaluation
lifecycle
schema_version
extensions
```

`id`是Blueprint identity，也屬於共同top-level contract。

## Architecture Union

`architecture`是strict `oneOf`：

### Single Agent

- root Agent與model slot；
- tools必須有handler、input/output contracts與read/write effect；
- write tool必須有approval action、typed approval contract與replay key。

### Workflow

- entry node、nodes、edges與terminal nodes；
- graph必須從entry reachable；
- loop必須有technical bound、terminal exhaustion node與實際route；
- retrieval node必須解析一個runtime retrieval contract。

### Multi-Agent

- coordinator與specialists有獨立IDs、model slots與state namespaces；
- task specialist必須有typed input/output；
- delegation mode必須與target lifecycle一致；
- shared state只有named writer與explicit merge policy。

新增architecture kind需要新增typed schema branch與validator，不能把
unstructured app config塞進`extensions`規避核心invariants。

## Common Runtime Contract

`runtime`描述：

- Implementation-relative entrypoint；
- replaceable model slots，不把model name藏在prompt或Agent code；
- Session/artifact/memory service binding與durability；
- state key、owner、scope、schema與conflict policy；
- retrieval adapter、provenance、authorization stage與deletion policy。

Entrypoint在Catalog implementation的immutable Git revision中解析；其他
`path.py#Symbol` refs在version-controlled Blueprint repository中以AST解析。

## Policy, Evaluation And Lifecycle

Policy、evaluation與lifecycle不是optional annotations：

- every Blueprint有enforcement refs；
- consequential actions有typed approval、replay key與blocking
  `policy_safety` metric；
- RAG有完整provenance與blocking `retrieval_grounding` metric；
- all Blueprints有runtime、trajectory、state與output blockers；
- production profile與rollback contract必須解析；
- upgrade policy區分compatible schema change與new implementation。

## Semantic Validation

JSON Schema只負責shape。Lab 11另外驗證：

1. CatalogEntry與Implementation存在；
2. source revision/path與assurance blob/digest在local Git object database存在；
3. entrypoint在pinned implementation內有top-level Python symbol；
4. 38個local refs都能解析file與AST symbol；
5. Workflow reachability、terminal與loop exhaustion；
6. retrieval provenance、ACL-before-ranking與grounding gate；
7. specialist typed I/O、delegation mode與shared-state single writer；
8. approval、credential、evaluation與rollback bindings。

這些checks刻意不由JSON Schema表達，因為它們需要graph、Git、AST與跨domain
reference resolution。

## Migration

Lab 11包含flat single-Agent v0.1 fixture與deterministic v1.0 migrator。

可自動migration的條件：

- Blueprint ID不變；
- CatalogEntry與Implementation IDs不變；
- behavior、policy與lifecycle refs沒有semantic變更；
- transformation只重組fields到新的typed domains。

需要new Implementation或human review的變更：

- implementation source/revision改變；
- architecture kind或entrypoint behavior改變；
- state owner、approval scope或retrieval authorization改變；
- blocking metric、production或rollback semantics弱化。

## Deliberate Invalid Cases

15個mutations涵蓋：

- unknown CatalogEntry/Implementation；
- duplicated catalog authority；
- missing eval gate或pinned entrypoint；
- write tool without approval；
- dangling Workflow edge與invalid exhaustion；
- missing RAG provenance或grounding gate；
- unknown coordinator、untyped task specialist與duplicate namespace；
- missing approval replay key；
- missing lifecycle contract。

Baseline exit `0`，broken exit `1`。

## Limits

- Catalog snapshot固定本repository三個local implementations，尚未驗證remote
  artifact registry或cross-repository trust。
- Model slots只驗證contract與ownership，未執行live models。
- v0.1 migrator只支援single-Agent；Workflow與multi-agent migrations需要
  node/agent identity mapping。
- Blueprint解析現有runtime-tested labs，但Lab 11本身不deploy service。
- Access control、registry storage與scaffold rendering屬於Phase 12/13。
