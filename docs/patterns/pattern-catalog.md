# Pattern Catalog: From Observations to Decision Contracts

Research snapshot: 2026-08-12.

## Question

前八個phases已產生七個candidate patterns，但格式、status語意與evidence
granularity不同。Phase 9要回答：

> 什麼條件讓一個pattern不只是sample摘要，而是可被工具檢查、可比較、
> 可拒絕錯誤使用方式的engineering decision contract？

## Hypothesis

> Pattern需要canonical structured manifest、human-facing explanation、
> claim-level source/lab evidence與cross-pattern decision boundaries。
> 只有Markdown template或source list不足以支援後續Agent Garden blueprint。

## Maturity and Portability

Roadmap原本把`validated`、`version-specific`放在同一個`status` enum。
實際整理後發現它們是不同維度：

| Field | Meaning | Values |
|---|---|---|
| `status` | evidence maturity | `candidate`, `validated`, `rejected` |
| `portability` | implementation scope | `portable`, `version-specific` |

例如Bounded Specialist已在pinned ADK 2.6.3通過完整local/runtime
experiments，所以maturity是`validated`；但`chat`、`single_turn`、`task`
與`FinishTaskTool`的具體implementation屬於current ADK version surface，
因此portability是`version-specific`。

`validated`只表示：

1. 有pinned primary source；
2. 有local executable implementation；
3. 有intentional break；
4. observable contract可被test。

它不表示live production、所有ADK version或所有provider都已驗證。

## Canonical Contract

Machine authority是：

- [`patterns/catalog.json`](../../patterns/catalog.json)
- [`patterns/schema/pattern.schema.json`](../../patterns/schema/pattern.schema.json)
- [`patterns/schema/catalog.schema.json`](../../patterns/schema/catalog.schema.json)
- `patterns/manifests/*.json`

每個manifest固定：

```text
identity + maturity + portability
  + context + forces + decision
  + implementation
  + observable contracts
  + failure modes
  + counterexamples
  + ADK version evidence
  + rejected decisions
```

Markdown card保留architecture explanation、使用時機與trade-off。Validator
要求H1、status、portability、required headings與claim IDs和manifest同步。

## Evidence Linkage

Bottom-of-page source list無法回答「哪個source支持哪個invariant」。
Phase 9因此要求每一筆：

- `observable_contract`
- `failure_modes`

都至少包含：

```text
source:<defined pinned source evidence ID>
lab:<existing executable evidence ID>
```

Source URL必須包含full 40-character commit SHA；lab path必須存在於repository。
這能阻擋：

- 使用floating `main` branch作證據；
- claim引用不存在的source ID；
- 只有source reading、沒有experiment；
- 只有test結果、沒有runtime contract來源。

## Catalog Result

| Pattern | Status | Portability | Phase |
|---|---|---|---|
| Deterministic Workflow | validated | portable | 2 |
| Bounded Specialist | validated | version-specific | 3 |
| Data Lifecycle Placement | validated | portable | 4 |
| Evidence-Preserving RAG | validated | portable | 5 |
| Behavior Contract Gate | validated | portable | 6 |
| Durable Approval Boundary | validated | portable | 7 |
| Replaceable Production Envelope | validated | portable | 8 |

Catalog summary：

- 7 patterns；
- 28 observable contracts；
- 28 failure modes；
- 7 rejected decisions；
- 11 directed relations；
- 5 decision boundaries。

## Decision Boundaries

### Control Owner

Deterministic Workflow與Bounded Specialist不是競爭的top-level architecture：

- fixed order、retry、termination由Workflow/code擁有；
- bounded semantic reasoning才交給specialist。

Rejected decision：讓LLM coordinator選擇已被business policy固定的route。

### Data Placement Versus Retrieval

Artifact、memory與RAG都能讓資料model-visible，但ownership不同：

- artifact處理versioned/on-demand payload；
- memory處理intentional cross-session recall；
- RAG處理ranked evidence、ACL與citation。

Rejected decision：所有large或cross-session data一律放vector index。

### Enforcement Versus Evaluation

Behavior Contract Gate偵測regression；Durable Approval Boundary在effect前阻擋。
Passing eval不是runtime authorization mechanism。

Rejected decision：用safety eval取代consequential tool call的pre-effect policy。

### Resume Versus Idempotency

Workflow/confirmation replay處理control state；external action ledger處理effect
dedup。兩者不能互相代替。

Rejected decision：假設resumed Session或consumed confirmation足以防止重複付款。

### Behavior Versus Deployment

Production Envelope依賴Behavior Contract Gate，但deployment target不能改變
被promotion的Agent behavior contract。

Rejected decision：在Agent business logic內加入target-specific behavior branch。

## Invalid Catalog

Lab 09注入12個錯誤：

1. claim缺lab evidence；
2. dangling evidence ID；
3. invalid maturity status；
4. floating source branch；
5. full-length commit不存在於upstream lock；
6. GitHub repository不存在於upstream lock；
7. missing counterexample；
8. missing lab path；
9. no rejected decision；
10. unknown relation target；
11. duplicate catalog entry；
12. version-specific pattern沒有validated version。

每個case都被expected issue code阻擋；broken CLI exit `1`。

## Decision Rules

1. Structured manifest是machine authority，Markdown是human explanation。
2. Maturity與portability分開。
3. Pattern claim必須同時有source fact與executable observation。
4. Failure mode不是附註；它是catalog contract的一部分。
5. 每個pattern至少有一個counterexample與一個rejected decision。
6. Relations表達dependency；decision boundaries表達容易混淆的選擇。
7. Schema與stdlib validator required fields必須由test保持一致。
8. Catalog只能作為blueprint input，不能直接當runtime configuration。

## Evidence and Limits

Lab 09提供：

- 14 dependency-free tests；
- baseline exit `0`；
- broken exit `1`；
- deterministic 3,327-byte evidence bundle；
- SHA-256
  `4bf1fea24ebc3ce4a06c2423da64ab017be11cba911d6452f4875730b92d91a9`。

Catalog尚未證明：

- live production portability；
- pattern completeness；
- source claim的semantic interpretation必然正確；
- manifest可以直接轉成executable Agent Garden blueprint。

最後一點是Phase 10到Phase 12要驗證的核心邊界。
