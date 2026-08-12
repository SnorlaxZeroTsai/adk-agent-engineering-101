# Agent Garden Research

這個區域從已驗證的Agent architecture、recipe、template與lifecycle
contracts反推internal Agent Garden，而不是先設計一個萬用manifest。

## Current Artifacts

- [`concepts.md`](concepts.md)：CatalogEntry、Implementation、Template、
  Project Instance、Blueprint與Release的identity boundary。
- [`discoverability-contract.md`](discoverability-contract.md)：三套upstream
  metadata contract、consumer behavior與最小discoverability contract。
- [`metadata-surfaces.json`](metadata-surfaces.json)：33個source fields的
  catalog/scaffold/runtime/governance ownership matrix。
- [`catalog-entry.schema.json`](catalog-entry.schema.json)：明確非executable
  的catalog schema。
- [`discovery-catalog.json`](discovery-catalog.json)：同一個Agent
  implementation的有效catalog entry。

## Planned Artifacts

`blueprint-schema.md`、`architecture.md`、`mvp.md`與
`future-evolution.md`會在後續phases依序建立。

Catalog contract不包含model、tool、workflow、policy、evaluation、
deployment或secret設定。那些欄位必須等Phase 11的executable blueprint
examples暴露共同需求後再建立。
