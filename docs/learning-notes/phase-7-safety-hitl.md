# Phase 7 Learning Note: Safety 與 HITL

日期：2026-08-12

## 問題

1. 哪一個 ADK hook 能在 unsafe transition 前真正阻擋？
2. plugin、Agent callback、tool confirmation、`RequestInput` 各自擁有什麼
   lifecycle？
3. `confirmed=true` 是否足以授權 payment？
4. fresh Runner resume 與重送 confirmation 時，side effect會不會重複？
5. credential request與 business approval是否為同一種安全邊界？

## 初始假設

1. prompt只能影響 model behavior，不能當 enforcement。
2. tool input policy必須在 tool執行前檢查。
3. approval需要 identity、scope、expiry、request integrity與idempotency。
4. framework的 resume/dedup不能取代外部 side-effect ledger。

## Primary Sources

ADK runtime：

- `plugins/base_plugin.py`
- `plugins/plugin_manager.py`
- `runners.py`
- `flows/llm_flows/base_llm_flow.py`
- `flows/llm_flows/functions.py`
- `flows/llm_flows/request_confirmation.py`
- `tools/function_tool.py`
- `tools/tool_confirmation.py`
- `events/request_input.py`
- `workflow/utils/_workflow_hitl_utils.py`
- `agents/context.py`
- `agents/remote_a2a_agent.py`
- confirmation與Workflow HITL unit tests

Recipes：

- `core/python/safety-plugins`
- `core/python/ambient-expense-agent`

所有 source paths皆由 `references/upstream-lock.yaml` 固定 commit。

## Source Findings

### Plugin是App-wide，callback是Agent-local

`App.plugins`套用整棵 Agent tree。model/tool lifecycle中，plugin先於Agent
callback執行。多個 plugins依註冊順序執行，第一個 non-`None`結果會
short-circuit後續 plugins與Agent callback。

所以 plugin ordering本身就是policy composition。

### Hook coverage不是等價的

- `on_user_message`可在Session append與model request前替換input。
- `before_model`可直接 bypass model。
- `after_model`可在Event persistence前替換response。
- `before_tool`可不執行tool而直接回FunctionResponse。
- `after_tool`只能替換result，不能回滾已發生的side effect。

### Safety sample與pinned Runner有差異

Safety recipe用 `on_user_message`寫flag，再由`before_run`回傳refusal。
Lab第一次照做時，model仍被呼叫。

追到 pinned Runner後發現這條ADK 2 setup path有await
`run_before_run_callback`，但沒有使用其return value作early exit。

修正不是假裝sample行為成立，而是：

- 保留`before_run` trace作source/runtime evidence；
- 把hard stop放到確實受尊重的`before_model`。

### ToolConfirmation只提供transport

Dynamic confirmation first turn observed：

```text
execute_vendor_payment FC
adk_request_confirmation FC
approval_required FR
pause
```

Resume observed：

```text
user confirmation FR
execute_vendor_payment FR
model text
end-of-agent metadata
```

ADK會核對original function call的name、args、history、registered tool與
confirmation requirement，但`ToolConfirmation`本身只有
`confirmed/hint/payload`。

### RequestInput是node-level HITL

`RequestInput`會產生`adk_request_input`，帶interrupt ID、payload與
response schema。response在resume後成為node output，適合deterministic
business process，而不是只確認一個LLM-selected tool call。

### Credential不是approval

`request_credential`必須有`function_call_id`，request會綁定該call。
credential service負責credential lifecycle；它不代表approver對特定
payment的決策。

## Experiment

Lab 07固定同一筆payment：

```text
action_id: PAY-2026-0812-01
vendor: vendor-atlas
amount: USD 2500
destination: acct-vendor-atlas
```

比較三條path：

1. prompt-only；
2. global policy plugin；
3. dynamic ToolConfirmation + application approval envelope。

Approval envelope固定：

- approval/action ID；
- action type；
- full request hash；
- approver ID；
- decision；
- policy version；
- issue/expiry time。

外部ledger以action ID做idempotency。

## Results

### Enforcement

| Variant | Payment effects |
|---|---:|
| Prompt-only | 1 |
| Complete plugin `before_tool` | 0 |
| Output-only plugin `after_tool` | 1 |

另外：

- unsafe user input：0 model calls；
- unsafe tool output：第二次model request看不到`RAW-SECRET`；
- unsafe model output：Event persistence前被替換。

### Approval

| Decision | Payment effects |
|---|---:|
| valid approval | 1 |
| confirmed false | 0 |
| expired | 0 |
| unauthorized approver | 0 |
| request hash mismatch | 0 |

Fresh Agent與Runner使用同一`InMemorySessionService`成功resume。

### Replay

重送相同confirmation到later run：

- tool invocation count從2變3；
- ledger execution attempts為2；
- external effects仍為1。

因此ADK consumed-confirmation dedup不是cross-run business idempotency。

### Evaluation

Phase 6 gate擴為6個cases：

- baseline 6/6 pass；
- broken 6/6 fail；
- safety break由trajectory、state、output、policy四個metrics阻擋；
- broken report共有28個blocking failures；
- scripted judge平均`13/3`仍pass；
- baseline exit `0`，broken exit `1`。

更新後evaluation evidence bundle為90,166 bytes，兩次SHA-256相同：

```text
b0442bedcb1e32c7a2438b2672addef91bd2faa90f1ac1ed8cdf95e956550fe0
```

Lab 07 evidence bundle為65,971 bytes：

```text
b8816d2ec4bd0ab44557a8deb0f0d1f67bd46382da876d0cb9c6a533d4776f61
```

## 修正初始思考

1. **global hook不代表所有Runner path都正確消費return value。**
   需要runtime test，不只讀interface。
2. **after_tool safety可能已太晚。**
   它能保護model與history，不能撤銷payment。
3. **confirmation不是authorization。**
   application仍需驗identity、scope、integrity與time。
4. **resume dedup不是side-effect idempotency。**
   later-run replay仍可能重新進tool。
5. **credential與approval是兩個contract。**
   possession不能取代business decision。

## Architecture Decisions

- Prompt只表達behavior preference，不承擔enforcement。
- Global invariant放App plugin，Agent-specific adaptation放callback。
- Consequential tool arguments在`before_tool`與service端各自驗證。
- Unsafe tool/model output在進model、telemetry、memory前redact。
- Approval payload不包含raw credential。
- 每個approval綁定full request hash與action scope。
- External system以action ID enforce idempotency。
- Rejected、expired、unauthorized、tampered response全部fail closed。
- Tool-level與Workflow node-level HITL依ownership選擇，不做一個模糊
  approval abstraction。

## Verification

```text
7 dependency-free Lab 07 tests
15 ADK-backed Lab 07 tests
6 baseline evaluation cases
6 deliberately broken evaluation cases
65,971-byte deterministic Lab 07 bundle
90,166-byte deterministic evaluation bundle
```

## Limits

- Session與ledger都在memory。
- 未驗process-loss recovery與atomic checkpoint/effect commit。
- 未驗approval UI authentication、revocation與separation of duties。
- 未呼叫live Model Armor、judge、credential provider或remote A2A。
- pinned FunctionTool live mode仍未支援confirmation。
