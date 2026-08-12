# Phase 10 Learning Note: Agent Garden Discoverability

日期：2026-08-12

## 問題

1. Recipe、template與project manifest是否能直接合併成Agent Garden schema？
2. 哪些fields屬於catalog、scaffold、runtime或governance？
3. Path、template folder或project name能否當stable identity？
4. Valid repository recipe為何仍可能無法被consumer發現？
5. 最小discoverability contract應包含什麼，又應排除什麼？

## 初始假設

1. ADK recipe manifest已接近完整catalog contract。
2. Starter Pack/Agents CLI的template與project fields可以補齊其餘欄位。
3. Folder name或generated project name足以當Agent ID。
4. `deployable`或`deployment_targets`可以直接成為runtime capability。

## Source Audit

Field-level inventory得到33 rows：

```text
catalog:    16
scaffold:   19
runtime:     6
governance:  7
```

同一field可跨plane，但authority不同。

Recipe manifest提供description、status、owner與classification，schema與
repository policy也最嚴格；但identity/source revision隱含在path/repository。

Template config提供selection、dependencies與render options；folder name是
implicit template identity，沒有owner或lifecycle。

Project manifest保存generation/upgrade/deploy defaults；known fields以defaults
讀取，unknown fields忽略，version mismatch只warning。Project name是instance
identity。

## Discovery Gap

Pinned Agents CLI的`discover_adk_agents`仍掃描`python/agents`。同一個ADK
Samples commit已由policy凍結該root，active recipes則在`core/`與`contrib/`。

因此repository validation與consumer discovery沒有共享authority。

## Experiment

建立：

- four-plane metadata ownership matrix；
- non-executable CatalogEntry JSON Schema；
- `cross-session-memory` valid entry；
- stdlib validator；
- 13個misleading mutations；
- baseline/broken CLI與deterministic renderer。

Catalog要求九個facts：

```text
stable identity
display
lifecycle + replacement
ownership
classification
immutable source
compatibility
reuse locator
implementation-bound assurance
```

三個source surfaces分別涵蓋4、3、1項；registry-composed entry涵蓋9/9。

## Results

```text
3 source contracts
4 pinned consumer observations
33 field rows
9 required discovery facts
1 catalog entry
1 implementation
1 assurance artifact
13 misleading cases detected
baseline exit 0
broken exit 1
```

16個dependency-free tests全數通過。兩次5,578-byte renderer輸出
byte-identical。

## 修正初始思考

### Manifest union不是product model

把三份manifest做field union會同時混入repository governance、template
choices、project instance defaults與runtime hints，且仍缺stable ID、immutable
source與assurance。

### Path與project name不是identity

Recipe移動path、template重新命名或project加上environment suffix時，Agent
identity不應改變。Identity必須由registry明確擁有。

### Scaffold capability不是runtime proof

`deployment_targets`表示generator有overlay，不代表implementation在每個
target通過behavior、security與rollback gates。

### Discoverability需要consumer contract

Producer寫出valid manifest不代表consumer會掃描它。Catalog index與consumer
必須使用同一個versioned contract。

## Architecture Decisions

- Agent ID、Implementation ID、Project Instance與Release ID分開。
- CatalogEntry只負責discovery與immutable implementation selection。
- Implementation保存language、framework constraint、source與reuse locator。
- Lifecycle保存replacement；active entry拒絕frozen path。
- Assurance綁implementation與digest。
- Blueprint fields明確排除，留給Phase 11。
- Baseline與broken gate都要有process exit semantics。

## Verification

```text
16 dependency-free tests
baseline exit 0
broken exit 1
13 misleading cases detected
5,578-byte deterministic evidence bundle
```

SHA-256：

```text
406fa09ddf419acfa0821fc1faa6796626ba485cae65ab5aa8aff87b767fdfee
```

## Limits

- 目前只有一個valid CatalogEntry。
- Compatibility尚未執行cross-version migration。
- Assurance只有runnability。
- Controlled capability taxonomy、search ranking與access control尚未設計。
- Executable Blueprint examples與schema屬於Phase 11。
