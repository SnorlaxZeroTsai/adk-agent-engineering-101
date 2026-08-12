# Phase 6 Learning Note: Evaluation

日期：2026-08-12

## 問題

1. ADK 的 dataset、trace、metric result 各自保留哪些 evidence？
2. tool trajectory 是否真的檢查 arguments？
3. 單一 critical case 能否被平均分數掩蓋？
4. Agents CLI 的 generate、grade、compare 各自負責什麼？
5. 如何讓 intentionally broken Agent 在 CI 中確實回傳失敗？

## 初始假設

1. dataset、runtime trace 與 grade result 應為不同 lifecycle stages。
2. deterministic contract 與 LLM judge 不應共享同一 blocking policy。
3. safety、ACL、state terminal outcome 等 critical metrics 必須逐 case
   通過，不能只看平均。
4. comparison command 不等於 release gate。

## Primary Sources

ADK：

- `evaluation/eval_case.py`
- `evaluation/eval_set.py`
- `evaluation/eval_metrics.py`
- `evaluation/eval_result.py`
- `evaluation/local_eval_service.py`
- `evaluation/trajectory_evaluator.py`
- `evaluation/agent_evaluator.py`
- `evaluation/metric_evaluator_registry.py`
- `evaluation/custom_metric_evaluator.py`

Agents CLI：

- `eval/_paths.py`
- `eval/cmd_generate.py`
- `eval/cmd_grade.py`
- `eval/cmd_compare.py`
- `eval/cmd_run.py`
- `eval/eval_utils.py`

所有 paths 都由 `references/upstream-lock.yaml` 固定 commit。

## Source Findings

### ADK EvalCase 保留對話與部分 intermediate evidence

`EvalCase` 可使用 static conversation 或 conversation scenario，並可提供
Session 初始 state、rubrics 與預期 final state。

`IntermediateData` 可保留 ordered tool uses/responses；但
`InvocationEvents` 只投影 `author` 與 `content`，不包含完整 Event 的
state delta、node path、route、branch、error 或 grounding metadata。

因此 trajectory evaluator 能證明 tool name/arguments，卻不自動證明：

- Workflow 是否走到安全 terminal node；
- specialist 是否覆寫別人的 state；
- memory 是否把 foreign-user data 放進 model input；
- RAG citation 是否對應 current/authorized source。

### Tool trajectory 會比對 exact arguments

`TrajectoryEvaluator` 的 `EXACT`、`IN_ORDER`、`ANY_ORDER` 都同時比對 tool
name 與 arguments。這是可直接使用的 contract。

但它先對每個 invocation 給 `0/1`，再取平均成 case overall score。
threshold 若低於 `1`，critical invocation failure 仍可能被其他 invocation
補回。

### Status aggregation 有兩層

`LocalEvalService` 會在任一 metric overall status failed 時讓 case failed。
然而 metric overall status 本身可能已是 invocation average。

legacy `AgentEvaluator` 另外明確使用 `statistics.mean` 聚合 scores。
所以「case final status 會 fail」不代表「每個 invocation 都必須 pass」。

### Agents CLI 正確分離 lifecycle

`_paths.py` 把 lifecycle 固定成：

```text
dataset -> populated traces -> grade results
```

這個分層值得保留。

但 `eval generate` 在部分 cases 失敗時會：

- 只寫成功 cases；
- 記錄 failures；
- 仍 exit `0`。

若 pipeline 不比對 input/output case IDs，失敗 case 會在 grade 前消失。

### Grade 的 custom metric 是 code execution boundary

local custom function 透過 `compile` + `exec` 執行，擁有 CLI process
權限。remote custom metric 則交給 Vertex sandbox。

Eval config 因此不是純資料。它需要 source review、pinning 與 least
privilege。

### Compare 不做 release decision

`eval compare` 回傳 recursive JSON diff 與 numeric delta，但不判斷
regression、threshold 或 blocking exit。

## Experiment

Lab 06 建立三個純 typed stages：

1. `EvalDataset`
2. `TraceSet`
3. `SuiteReport`

Dataset最初各取前五個 phases的一個observable contract，Phase 7再加入
consequential-action approval：

- Agent tool round trip；
- Workflow loop exhaustion；
- bounded task specialist；
- memory user isolation；
- RAG source grounding。
- safety/HITL approval與side-effect policy。

每案都有 baseline 與 deliberate break，而且兩個 trace sets 必須包含相同
case IDs。

## Metrics

Blocking deterministic metrics：

- runtime success；
- exact tool name/order/arguments；
- Event 或 Workflow stage trajectory；
- nested state 與 forbidden paths；
- deterministic output contract；
- policy/secret isolation；
- retrieval/citation/ACL/version/deletion；
- model request budget。

Advisory metric：

- `scripted_response_quality`，明確標記為 local stand-in，不冒充 live
  LLM judge。

## Results

### Baseline

- 6/6 cases passed。
- CLI exit `0`。

### Broken

- 6/6 cases failed。
- 20 個 per-case deterministic failures。
- 8 個 failed blocking aggregates。
- 共 28 個 blocking reasons。
- CLI exit `1`。

Failure ownership：

| Case | Blocking evidence |
|---|---|
| Agent | exception、wrong tool/trajectory、missing state/output |
| Workflow | unsafe finalization、wrong terminal trajectory/state |
| Multi-agent | extra specialist calls、5 > 3 requests、wrong final state |
| Memory | Bob model input contains `ALICE-SECRET` |
| RAG | citation/provenance missing、grounded false |
| Safety/HITL | prompt-only payment缺approval trajectory/state並回報policy violation |

五個仍有 fluent output 的 broken cases 都得到 scripted judge `5/5`；Agent
failure 得 `1/5`。平均為 `13/3`，judge aggregate 判 pass，但 release
仍正確 fail。

完整 evidence bundle 為 90,166 bytes；兩次 render 的 SHA-256 相同：

```text
b0442bedcb1e32c7a2438b2672addef91bd2faa90f1ac1ed8cdf95e956550fe0
```

## 修正初始思考

1. **metric-level fail 不代表沒有 average masking。**
   必須看 evaluator 如何產生 overall score。
2. **trace collection success 不代表 dataset completeness。**
   partial success 需要獨立 completeness gate。
3. **judge pass 不代表 architecture pass。**
   fluent answer 無法證明 state、ACL、tool 或 citation contract。
4. **compare 不等於 gate。**
   delta 需要 policy 才能轉成 release decision。
5. **NOT_EVALUATED 不能默認安全。**
   required blocking metric 缺 evidence 時應 fail closed。

## Architecture Decisions

- dataset、trace、grade result 分型，不互相覆寫。
- every blocking case 必須有 result；缺案或多案直接 error。
- deterministic metrics 預設 `all_cases`。
- judge metric 預設 advisory，需明確 policy 才能 blocking。
- per-case failure 保留，即使 aggregate mean 達標。
- failure message 帶 case、metric、reason 與 evidence。
- CLI 以 `0/1` 表達 release verdict。
- local custom metrics 視為 trusted code。

## Verification

```text
11 dependency-free engine tests
6 ADK-backed cross-phase tests
6 baseline cases
6 deliberately broken cases
baseline exit 0
broken exit 1
90,166-byte deterministic evidence bundle
```

## Limits

- 沒有 live LLM judge。
- 沒有 latency、token 或 monetary cost telemetry。
- 沒有 streaming/partial Event consolidation。
- 沒有 dataset version migration 與 durable result store。
- Lab contract 是 local normalization layer，不是 ADK public extension API。
