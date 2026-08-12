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
- [`blueprint-schema.md`](blueprint-schema.md)：example-first executable
  Blueprint contract、semantic validation與migration boundary。
- [`blueprints/`](blueprints/)：三個architecture examples、Catalog snapshot
  與Draft 2020-12 schema。

## Planned Artifacts

`architecture.md`、`mvp.md`與`future-evolution.md`會在後續phases依序建立。

Catalog contract不包含model、tool、workflow、policy、evaluation、
deployment或secret設定。Phase 11 Blueprint以Catalog reference連接這些
executable contracts，而不複製Catalog authority。
