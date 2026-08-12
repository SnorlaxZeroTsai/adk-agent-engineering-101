# Phase 9 Learning Note: Pattern Catalog

日期：2026-08-12

## 問題

1. 七張pattern cards能否使用同一個contract？
2. `validated`與`version-specific`是否是同一維度？
3. source list是否足以支持observable invariant？
4. pattern之間的dependency、overlap與conflict如何表示？
5. catalog錯誤能否由CI阻擋？

## 初始假設

1. 統一Markdown headings即可完成normalization。
2. Roadmap原本的single `status` enum足夠。
3. 每張card底部列出source與lab即可。
4. Pattern彼此獨立，relation只需寫在敘述中。

## Experiment

建立：

- canonical catalog index；
- JSON Schemas；
- 七個pattern manifests；
- 七張normalized Markdown cards；
- relation graph；
- decision boundaries；
- stdlib validator；
- 12個invalid mutation fixtures；
- baseline/broken CLI與deterministic evidence renderer。

Validator同時檢查：

- schema/validator required-field parity；
- status與portability；
- pinned source URLs；
- existing lab paths；
- 每個contract/failure的source+lab evidence；
- Markdown headings與claim IDs；
- relation與decision-boundary coverage；
- rejected decisions。

## Results

Baseline：

```text
7 validated patterns
6 portable
1 version-specific
28 observable contracts
28 failure modes
7 rejected decisions
11 relations
5 decision boundaries
0 validation issues
exit 0
```

Broken：

```text
12 invalid mutations
12 expected issue codes detected
exit 1
```

14個dependency-free tests全數通過。兩次3,327-byte renderer輸出
byte-identical。

## 修正初始思考

### Markdown template不夠

Headings只能改善閱讀，無法檢查evidence ID、path、version scope與relations。
Machine authority需要structured manifest。

### Maturity與portability正交

Bounded Specialist可以是locally validated，同時保持ADK 2.6.3
version-specific。把兩者放在一個enum會失去資訊。

### Source list不等於claim evidence

每個observable contract與failure mode都需要明確source/lab refs，否則reviewer
無法知道哪個evidence支持哪個claim。

### Pattern不是彼此獨立

Behavior Contract Gate驗證其他patterns；Production Envelope依賴behavior與data
lifecycle；Durable Approval Boundary specialization of deterministic resume。
Relation graph是blueprint design前的必要input。

## Architecture Decisions

- JSON manifest是canonical machine contract。
- Markdown card是human explanation，必須與manifest identity同步。
- `status`與`portability`分開。
- 每個claim至少一筆pinned source與一筆existing lab evidence。
- 每個pattern至少一個counterexample與rejected decision。
- Catalog index負責relations與decision boundaries。
- stdlib validator與published JSON Schema由tests保持field parity。
- Broken catalog CLI必須nonzero。

## Verification

```text
14 dependency-free tests
baseline exit 0
broken exit 1
12 invalid cases detected
3,327-byte deterministic evidence bundle
```

SHA-256：

```text
4bf1fea24ebc3ce4a06c2423da64ab017be11cba911d6452f4875730b92d91a9
```

## Limits

- 只有current seven patterns。
- Portable decision不代表所有runtime implementation已測。
- Validator不執行general JSON Schema semantics。
- Evidence linkage不自動證明claim interpretation正確。
- Catalog metadata尚未分成discoverability、scaffold、runtime與governance
  blueprint fields。
