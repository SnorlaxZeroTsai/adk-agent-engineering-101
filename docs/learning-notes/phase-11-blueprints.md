# Phase 11 Learning Note: Executable Blueprints

日期：2026-08-12

## 問題

1. CatalogEntry與Blueprint應如何引用而不複製authority？
2. Single Agent、Workflow/RAG與multi-agent/HITL有哪些真正共同fields？
3. 哪些invariants能由JSON Schema表達，哪些需要semantic validation？
4. Schema migration何時可自動化，何時需要new Implementation或human review？

## 初始假設

1. Architecture可以用一個generic `options` object。
2. 所有identifier都能共用kebab-case。
3. JSON Schema足以驗證executable contract。
4. Catalog source與Blueprint composition可以放在同一份metadata。

## Example-First Derivation

先固定三個existing runtime-tested implementations：

```text
Lab 01 -> order support single Agent
Lab 02 -> research Workflow
Lab 03 -> case triage multi-agent
```

Catalog snapshot固定於commit
`9702a79d15f81a9a44a8d40af3ca038196746c46`，assurance digest對應三個
runtime test files。

接著才加入Blueprint composition：

- Workflow綁定Lab 05 RAG contract；
- multi-agent綁定Lab 07 approval contract；
- all examples綁定Lab 06 behavior gate與Lab 08 production/rollback
  contracts。

Core provenance仍由Catalog implementation擁有，composition refs由Blueprint
擁有。

## Schema Result

Top-level共同domains為：

```text
schema_version
id
catalog_ref
architecture
runtime
policy
evaluation
lifecycle
extensions
```

Architecture使用single-Agent、Workflow與multi-agent strict `oneOf`。Runtime
則共同描述entrypoint、model slots、services、state與retrieval。

第一輪actual Draft 2020-12 validation抓到一個schema extraction bug：
Garden identity是kebab-case，但runtime metrics、action與Agent name是
snake_case。修正方式是分開`id`與`runtime_name`，不是改寫existing runtime
contracts。

## Semantic Validation

Published schema不能驗證：

- Catalog reference是否存在；
- Git commit/path/blob/digest是否存在；
- Python symbol是否存在；
- Workflow graph是否reachable；
- retrieval provenance與eval metric是否成對；
- task delegation mode、typed I/O與state writer是否一致；
- consequential action是否有approval replay key。

Lab 11因此使用stdlib schema subset、local Git objects與Python AST，並加入
architecture-specific validators。

## Deliberate Breakage

15個mutations分別破壞catalog、schema、entrypoint、tool approval、graph、
RAG、delegation、state namespace、approval與lifecycle contracts。所有cases
都由指定issue code攔下，broken CLI exit `1`。

## Migration

Flat v0.1 single-Agent fixture可deterministically轉成canonical v1.0 example，
且Blueprint、CatalogEntry與Implementation IDs完全不變。

這證明field relocation可自動化；它不證明architecture、state ownership或
policy semantic change可以自動migration。

## Results

```text
3 executable Blueprint examples
3 architecture branches
38 local refs / 26 unique refs
15 invalid cases detected
19 dependency-free tests
baseline exit 0
broken exit 1
4,383-byte deterministic evidence bundle
```

SHA-256：

```text
a66203d7207337512552d6f872a8918c142222d86f48d977e1202eaa2dc37234
```

## Architecture Decisions

- Catalog identity/provenance與Blueprint composition分開。
- Common top-level contract從examples交集推導。
- Architecture differences使用typed union。
- Runtime-owned names不共用Garden identity regex。
- JSON Schema與semantic validator各自負責可辯護的範圍。
- RAG、approval與behavior gate是typed blocking contracts。
- Auto-migration只處理不改變identity/behavior/ownership的shape change。

## Limits

- Examples使用一個repository與Python ADK 2.6.3 implementation family。
- Workflow/RAG與multi-agent/HITL是composition contract，未建立新monolithic
  implementation。
- Remote registry trust、ACL、scaffold rendering與upgrade execution屬於後續
  phases。
- Live model與cloud runtime仍未驗證。
