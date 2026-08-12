# Phase 13 Learning Note: Mini Agent Garden

日期：2026-08-12

## 問題

1. 六個Phase 12 components能否形成一個可用CLI而不合併authority？
2. 三種Blueprint能否用同一product lifecycle scaffold與test？
3. Upgrade如何區分schema、Implementation與rendered instance？
4. New architecture是否迫使CLI加入kind-specific branches？

## 初始假設

1. CLI需要針對single Agent、Workflow與multi-agent寫三組commands。
2. Scaffold可以從current worktree複製source。
3. `test`可以直接在project directory執行，不需要candidate identity。
4. Upgrade只要重新render整個directory。

## Implementation

CLI實作：

```text
list
inspect
validate
create
test
upgrade
```

Catalog Registry固定三個Phase 11 entries。Contract Validator直接呼叫Phase 11
schema/Git/AST/graph validator，不在CLI重寫rules。

Renderer從Catalog-selected commit `9702a79`讀Git blobs，產生managed-file
manifest。Local Deployment Controller在Behavior Gate前重驗所有digests並
產生content-addressed candidate。

Behavior Gate的test command來自code-owned architecture handler，不來自
Blueprint string。Report綁定candidate digest、Blueprint digest、blocking
metrics、test count與exit code。

## Three Architecture Result

```text
order-support-read-only       24 files  13 tests
research-workflow-rag         18 files   7 tests
case-triage-with-approval     18 files   7 tests
```

所有tests在scaffolded pinned source內執行，三份reports皆pass。

## Upgrade Result

- v0.1 fixture先由Phase 11 migrator轉成canonical v1.0。
- Same identity/Implementation且`compatible-schema`的composition change可
  apply。
- Renderer只更新old/new manifest列出的managed paths。
- Unlisted `user/notes.txt`在upgrade後保持byte-identical。
- Changed Implementation selection需要explicit review。

## Typed Extension Result

CLI parser與service沒有architecture `if/elif`。Architecture Registry提供
render/test handler。

Lab注入`experimental-typed` handler與代表已完成core schema change的
test-only validator，原有`create`/`test` command不用修改即可執行。Default
validator仍以`schema_one_of`與`architecture_kind_unknown`拒絕同一fixture。

這證明可擴充的是CLI dispatch，不是放棄typed core。

## Deliberate Breakage

11個flows分別破壞：

- Catalog/Blueprint resolution；
- blocking metric；
- managed file或candidate digest；
- behavior test；
- Implementation review；
- ledger uniqueness或secret boundary；
- handler registration；
- output ownership；
- typed architecture schema。

所有cases由指定code攔下，broken CLI exit `1`。

## Results

```text
3 Project Instances
27 implementation contract tests
11 invalid flows detected
22 dependency-free Lab 13 tests
baseline exit 0
broken exit 1
5,083-byte deterministic evidence bundle
```

SHA-256：

```text
e1d492a7a7050f2b8cc203bbcf48cdef22877e7688809ce5ebac93e9554fe420
```

## Architecture Decisions

- CLI is orchestration, not authority.
- Read implementation source from immutable Git objects.
- Keep validation delegated to the published Blueprint validator.
- Stage and hash a candidate before behavior execution.
- Keep test commands code-owned and controlled.
- Preserve user files outside the managed-file manifest.
- Require review for Implementation changes.
- Keep architecture schema/validator typed while making CLI dispatch
  registry-based.

## Limits

- Local filesystem adapters have no multi-process locking.
- Append-only JSONL is not signed or transactionally linked to deployment.
- Behavior tests do not replace live-model, ADK runtime, latency or cost gates.
- Cloud targets, registry ACL, remote provenance and stateful migrations remain
  unresolved production integrations.
