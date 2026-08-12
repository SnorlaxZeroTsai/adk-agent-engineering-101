# Agent Garden Concepts

Research snapshot: 2026-08-12.

## Identity Boundaries

### Agent Identity

使用者搜尋、比較與追蹤lifecycle的穩定概念。例如
`cross-session-memory`。Display name、repository path、generated project
name或deployment resource都不能取代這個identity。

### Implementation

一個Agent identity可以有多個實作，例如Python ADK 1.x、Python ADK 2.x
或TypeScript。Implementation必須以immutable repository revision與path
定位，並獨立宣告language、framework compatibility、reuse mode與assurance
evidence。

不同implementation不等於不同Agent identity。同一個immutable source也
不能在沒有alias或migration semantics時被註冊為兩個Agent identities。

### Template

Template負責把implementation與platform overlays render成project。
Deployment targets、extra dependencies、Session choice、frontend與CI runner
是scaffold capabilities，不是CatalogEntry對runtime behavior的保證。

### Project Instance

Project instance是一次generation的結果。`agents-cli-manifest.yaml`中的
project name、Agent directory、region、base template、CLI version與
create params屬於這個instance。

Project name可能包含team、environment或region，因此不能回推stable Agent
identity。

### Blueprint

Blueprint是Phase 11才要建立的executable contract。它需要描述architecture、
model、tools、workflow、state、policy、evaluation與lifecycle，但不應重複
CatalogEntry的stable identity與human discovery目的。

### Release

Release是某個Blueprint/Implementation在特定environment的immutable
artifact、behavior evidence與platform revision。Phase 8已證明project
manifest與current deployment metadata都不是release ledger。

## Four Metadata Planes

| Plane | Question | Examples |
|---|---|---|
| Catalog | 使用者如何找到、比較與選擇？ | stable ID、summary、tags、lifecycle、implementation compatibility |
| Scaffold | 如何產生或升級project？ | template、dependencies、target choices、frontend、CI |
| Runtime | code在哪裡、runtime defaults是什麼？ | Agent directory、Session choice、region、transport |
| Governance | 誰負責、如何驗證與淘汰？ | owner、status、replacement、source pin、assurance |

一個field可以服務多個plane，但必須有單一authority。例如language同時影響
catalog filter與scaffold overlay；deployment target則不應因出現在template
config就升格為runtime truth。

## Authority Rules

1. Catalog ID獨立於path、display name與project name。
2. Implementation source使用full Git commit，不接受branch。
3. Framework compatibility來自實際dependency contract，不由template
   family推測。
4. Active entry不能指向repository已frozen的legacy root。
5. Deprecation需要replacement identity，不只是一個inactive flag。
6. 每個implementation至少有一筆structure、runnability或behavior
   assurance。
7. Catalog不保存model、tool、workflow、policy、secret或deployment desired
   state。

## Consumer Boundary

Catalog consumer可以：

- list/filter/search；
- 顯示owner、lifecycle與compatibility；
- 選擇immutable implementation；
- 跳轉到pinned source或remote-template locator；
- 顯示assurance evidence。

Catalog consumer不能：

- 宣告Agent已可部署；
- 產生完整runtime topology；
- 取得credentials；
- 決定policy或evaluation gate；
- 推斷目前production release。

這些能力需要Blueprint、Project Instance與Release contracts。
