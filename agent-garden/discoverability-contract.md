# Agent Garden Discoverability Contract

Research snapshot: 2026-08-12. Source facts are pinned to
`google/adk-samples@4b5dd77`,
`GoogleCloudPlatform/agent-starter-pack@659f047` and
`google/agents-cli@5a306f8`.

## Question

> 一個sample需要哪些metadata，才能被穩定發現、比較、重用與淘汰，同時不把
> scaffold、runtime與governance誤塞進同一份manifest？

## Source Contracts

### ADK Recipe Manifest

`manifest-schema.json`使用`additionalProperties: false`，required fields為
`type`、`status`、`language`、`description`與`ownership`。Optional fields
補上architecture、dependencies、license、tags、deployable與repository size
tier。

`validate_manifest.py`除了Draft 7 schema，還阻擋placeholder owner與TODO
description；repository policy另外負責required files、placement、size與
frozen roots。這是三套surface中最完整的catalog/governance contract。

仍有四個限制：

1. identity隱含在directory path；
2. manifest沒有repository revision；
3. dependency names通常沒有version semantics；
4. inactive沒有replacement identity或assurance artifact。

### Starter Pack Template Config

`templateconfig.yaml`的consumer使用folder name作identity，讀取description、
example question、hidden、language、tags、deployment targets、extra
dependencies、Session與frontend choices。

這些欄位適合template selection與scaffold rendering。它沒有owner、
lifecycle或immutable source；`deployment_targets`表示generator可提供哪些
overlay，不證明某個Agent implementation已在那些targets通過runtime、
behavior或rollback驗證。

### Agents CLI Project Manifest

`ProjectConfig`讀取project name、Agent directory、region、base template、
language、`acli_version`與`create_params`。Absent manifest、missing keys與
unknown keys會使用defaults或被忽略；CLI/scaffold version mismatch只warning。

這份manifest回答：

> 這個generated project當初如何建立，lifecycle commands預設操作哪裡？

它不回答：

> 這是哪一個stable Agent identity，誰負責，哪個immutable implementation
> 通過哪些驗證？

`generated_at`會被template寫入，但`ProjectConfig`沒有保留它，顯示producer
與consumer contract也不是完全對稱。

## Discovery Drift

Pinned Agents CLI的`discover_adk_agents`仍只掃描
`python/agents/*`，以folder、`pyproject.toml`或heuristics建立`adk@...`
selection。ADK Samples同一commit已把active recipe roots移到
`core/<language>`與`contrib/<language>`，並在policy凍結`python/agents`。

因此：

```text
repository governance says: discover core/ and contrib/ manifests
current scaffold discovery says: scan frozen python/agents
```

一個存在、active且schema-valid的recipe仍可能不出現在consumer list。
Discoverability必須由versioned catalog index或manifest traversal擁有，不能
依賴舊folder heuristic。

## Field Ownership

完整33-field comparison在
[`metadata-surfaces.json`](metadata-surfaces.json)。

| Surface | Catalog | Scaffold | Runtime | Governance |
|---|---:|---:|---:|---:|
| ADK recipe manifest | identity/display hints | deployable hint | none | status/owner/policy inputs |
| Starter template config | selection display/filter | primary authority | generated path hint | none |
| Agents CLI project manifest | language hint only | project-instance authority | command defaults | scaffold provenance only |

同一field可能跨欄；表格描述的是authority，不是檔案是否出現文字。

## Minimum Discovery Facts

Lab 10要求九項：

1. `stable_identity`：不隨path、display name或environment改變；
2. `display`：name與summary；
3. `lifecycle`：active/deprecated/retired與replacement；
4. `ownership`：team與accountable contacts；
5. `classification`：standalone/module與search tags；
6. `immutable_source`：repository、full commit與path；
7. `compatibility`：language、framework package與version constraint；
8. `reuse_locator`：reference/import/remote-template的pinned locator；
9. `assurance`：綁定implementation的structure/runnability/behavior evidence。

三個upstream surface分別只涵蓋4、3與1項，沒有一個可單獨成為CatalogEntry。
[`discovery-catalog.json`](discovery-catalog.json)將它們與registry-owned facts
組合後涵蓋9/9。

## Catalog Shape

```text
CatalogEntry
  stable identity
  display + lifecycle + owner
  classification
  implementations[]
    language + framework compatibility
    immutable source
    pinned reuse locator
  assurance[]
    implementation ID + evidence ref + digest
```

一個CatalogEntry可以容納多個implementations。Deployment environments、
models、tools、workflow、state schema、policy、eval dataset、secrets與release
metadata不在這份contract；它們屬於Phase 11 Blueprint與Phase 8 Release。

## Deliberate Misleading Entries

Lab 10以同一個`cross-session-memory` implementation建立13個反例：

- missing ID與project-instance-derived ID；
- `main` source與`main` remote-template locator；
- active entry指向frozen legacy path；
- ADK 1.x實作誤標ADK 2.x compatibility；
- language與recipe status drift；
- missing owner與assurance；
- template deployment targets越權進入catalog；
- deprecated entry沒有replacement；
- 同一immutable source註冊成第二個Agent identity。

所有反例都產生nonzero gate。

## Engineering Decisions

- Catalog schema是non-executable discovery contract。
- Recipe path、template folder與project name都不是stable identity。
- Immutable source與framework compatibility屬於implementation，不屬於
  top-level Agent identity。
- Assurance綁implementation，不能只在catalog頁面放一個generic badge。
- Source consumer與producer需要同一個versioned discovery contract。
- Blueprint schema不從現有manifest欄位做union；下一phase先建立三個
  materially different executable examples。

## Limits

- Baseline只驗證一個ADK 1.x implementation。
- Runnability digest證明固定檔案identity，不等於live service quality。
- Catalog tags仍是curated labels，尚未建立controlled capability taxonomy。
- GitHub full commit是本lab的source locator；其他artifact registries需要
  等價的immutable digest。
- Phase 11仍需決定Blueprint如何引用CatalogEntry與Implementation，而不
  複製其authority。
