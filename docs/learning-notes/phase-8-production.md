# Phase 8 Learning Note: Production Engineering

日期：2026-08-12

## 問題

1. Starter Pack與Agents CLI把production concern放在哪裡？
2. `agents-cli-manifest.yaml`是否等於完整desired state？
3. `.env`、secret binding、live environment update的ownership如何分開？
4. telemetry enabled是否代表prompt/response不會被保存？
5. `deployment_metadata.json`能否支援rollback？
6. Cloud Run與Agent Runtime能否共用同一rollback abstraction？

## 初始假設

1. Agent code應獨立於deployment target。
2. config與secret需要不同資料型別。
3. staging通過的artifact應原樣promotion到production。
4. current deployment metadata可能不足以做rollback。
5. rollback的evidence可以共用，platform action不一定能共用。

## Primary Sources

Starter Pack：

- `cli/utils/template.py`
- `cli/commands/enhance.py`
- `cli/utils/merge.py`
- `docs/guide/deployment.md`
- `docs/cli/upgrade.md`
- generated PR/staging/production workflows

Agents CLI：

- `_project.py`
- `scaffold/utils/template.py`
- `scaffold/utils/upgrade.py`
- `deploy/_utils.py`
- `deploy/_operation.py`
- `deploy/agent_runtime.py`
- `deploy/cmd_deploy.py`
- deployment與observability skills
- target-specific Terraform service files

所有source paths由`references/upstream-lock.yaml`固定commit。

## Source Findings

### Starter Pack是rendered-files ownership

Template composition順序為shared base、language base、deployment overlay、
agent overlay。Upgrade透過old/current/new三方比較更新scaffolding，Agent code
與`.env`等config不覆寫。

Generated CI表達PR checks、staging deploy/load test、production approval與
promotion。這是很好的lifecycle skeleton，但rendered files進入application
repo後，ownership已轉給使用團隊。

### Agents CLI把lifecycle拆成commands

Manifest保留project/scaffold metadata，不包含完整deploy desired state。
Deploy target可由CLI override；缺manifest時甚至可使用defaults deploy。
Version mismatch只warning。

所以manifest不是release record，也不是所有runtime config的唯一authority。

### `.env` copy model會模糊secret boundary

Deploy utilities把project `.env`原樣讀入runtime env，再由explicit flags
覆蓋。Cloud Run有command redaction，Agent Runtime structured secret顯示會
mask；但一般plain env仍是plain string。

因此「log有redact」不能證明「secret沒有進plain config」。

### Update preserve可能保存drift

Agent Runtime update先讀live plain env，再以`setdefault`補到新env map。
這可避免不相關setting遺失，也會讓out-of-band `DEBUG_BYPASS`繼續存在。

Lab把它視為drift，先block再由人決定adopt或delete。

### Telemetry有兩條content path

Bare deploy把span content fail closed：

```text
OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=NO_CONTENT
ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false
```

但Terraform provisioned deployment可同時透過completion upload把完整
prompt/response寫入GCS/BigQuery。關掉trace content不等於關掉content
storage。

### Metadata不是release ledger

Pending operation只保存operation/project/location/target/time；完成後metadata
只保存current resource、target與timestamp。Corrupt file會當空資料處理。

這適合local status recovery，不足以證明：

- deploy的是哪個immutable artifact；
-哪份behavior report通過；
-從哪個staging release promotion；
-previous release是誰；
-如何rollback。

### Rollback能力因target不同

- Cloud Run：revision traffic shifting。
- GKE：`kubectl rollout undo`。
- Agent Runtime：沒有revision rollback，修正後重新deploy。

共用接口應固定evidence，不應捏造所有platform都有同一rollback command。

## Experiment

Lab 08固定同一Agent source與Phase 6 behavior report，render：

1. local；
2. Cloud Run；
3. Agent Runtime。

每個render有六個owned artifacts：

```text
agent contract
behavior gate
runtime config
deployment spec
lifecycle manifest
derived release candidate
```

另外建立append-only release ledger，固定source/artifact/spec/eval digests、
staging promotion、previous release與platform revision。

## Results

### Replaceable target

三target的Agent contract與behavior gate完全相同。

Target change只影響：

- runtime config；
- deployment spec；
- lifecycle manifest；
- derived release candidate。

### Release promotion

Cloud Run與Agent Runtime的production v4都與staging v4共享相同artifact
digest與behavior report digest。Previous v3有自己的staging evidence。

### Rollback

| Target | Observed plan |
|---|---|
| local | restart previous source artifact |
| Cloud Run | shift traffic to previous revision |
| Agent Runtime | release orchestrator restores bundle, then redeploys |

### Breakages

8個broken scenarios全部fail：

1. plaintext secret；
2. unapproved full-content telemetry；
3. failed/missing behavior gate；
4. mutable artifact tag；
5. target capability mismatch；
6. silently preserved environment drift；
7. mutable current-resource metadata；
8. orphaned rollback/promotion history。

共23個blocking failures，broken CLI exit `1`。

## 修正初始思考

1. **manifest不是desired state。**
   它是project lifecycle metadata，deploy flags與live platform state仍有自己的
   precedence。
2. **preserve live config不是純粹安全行為。**
   它同時可能保存drift。
3. **telemetry no-content需要逐sink判斷。**
   traces沒有content時，GCS completions仍可能有完整content。
4. **current resource ID不能做rollback。**
   需要artifact、spec、eval與history。
5. **rollback abstraction應共用證據，不共用假command。**
   Agent Runtime redeploy與Cloud Run traffic shift是不同能力。

## Architecture Decisions

- Agent source與behavior gate不依target分叉。
- Manifest、runtime config、secret refs、deployment spec與release record分型。
- Production secret version固定，不使用`latest`。
- Live drift先阻擋，再顯式adopt/delete。
- Remote target必須命名durable state services與runtime identity。
- Full content telemetry需要approval、sink與retention。
- Staging與production使用同一artifact/eval digests。
- Release history append-only；metadata file只當local cache。
- Rollback strategy由target adapter擁有。
- Agent Runtime保留prior immutable source bundle，由release orchestrator
  restore/redeploy。

## Verification

```text
18 dependency-free tests
7 baseline scenarios pass
8 broken scenarios fail
23 blocking failures
baseline exit 0
broken exit 1
43,765-byte deterministic evidence bundle
```

SHA-256：

```text
d3d51a6a421c37ef7dd775bb456b84142b9166dfaab603b081e07a624355cf89
```

## Limits

- 未執行real cloud build/deploy。
- 未驗IAM、WIF、Terraform state與drift。
- 未驗database migration向前/向後相容。
- 未驗traffic shift、health signal與automatic rollback。
- Release ledger仍在memory，沒有signing或transactional storage。
- Artifact digest是lab contract，未連接real registry attestation。
