# Lab 11 Observations

## Baseline

- 3個Blueprint examples。
- Architecture counts：single Agent 1、Workflow 1、multi-agent 1。
- 3個CatalogEntries與3個immutable implementations。
- 38個local refs，26個unique refs。
- 3個model slots、3個state contracts。
- 1個retrieval contract、1個approval action。
- 16個blocking metric bindings。

## Gate Results

- Dependency-free tests：19。
- Baseline exit：`0`。
- Broken exit：`1`。
- 15個invalid cases全部由指定issue code攔下。
- v0.1 migration與canonical v1.0 order-support example完全相同。
- CatalogEntry ID、Implementation ID與Blueprint ID在migration中不變。
- 兩次4,383-byte evidence renders byte-identical。
- SHA-256：
  `a66203d7207337512552d6f872a8918c142222d86f48d977e1202eaa2dc37234`。

## Decisions

- Catalog owns identity/provenance；Blueprint owns executable composition。
- Top-level schema只保留三個examples共同的domains。
- Architecture差異用strict typed union，不用generic options map。
- JSON Schema負責shape；Git、AST、graph與cross-domain rules由semantic
  validator負責。
- RAG provenance、approval safety與common behavior metrics是blocking
  contracts。
- Compatible field relocation可以auto-migrate；behavior/ownership changes
  需要new implementation或human review。

## Limits

- v0.1 migrator只支援single Agent。
- Pinned source verification使用local Git object database，沒有remote trust
  signature。
- Live model、cloud deployment、registry ACL與scaffold rendering未驗證。
