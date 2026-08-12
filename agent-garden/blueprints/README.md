# Executable Blueprints

Blueprint將Phase 10的stable CatalogEntry選擇，連接到architecture、runtime、
policy、evaluation與lifecycle contracts。它不複製display、owner、source或
compatibility authority。

## Artifacts

- [`catalog-snapshot.json`](catalog-snapshot.json)：三個CatalogEntry與
  immutable implementations，固定於repository commit
  `9702a79d15f81a9a44a8d40af3ca038196746c46`。
- [`schema/blueprint.schema.json`](schema/blueprint.schema.json)：Draft
  2020-12 v1.0 schema。
- [`examples/order-support.blueprint.json`](examples/order-support.blueprint.json)：
  single Agent + typed read-only tools。
- [`examples/research-workflow.blueprint.json`](examples/research-workflow.blueprint.json)：
  deterministic Workflow + explicit RAG contract。
- [`examples/case-triage.blueprint.json`](examples/case-triage.blueprint.json)：
  coordinator/task specialist + durable approval contract。

## Resolution Model

```text
Blueprint catalog_ref
  -> CatalogEntry
  -> Implementation
  -> immutable repository revision + implementation path
  -> Blueprint-relative entrypoint

Blueprint bindings
  -> repository-local typed contracts
  -> policy/evaluation/lifecycle evidence
```

Workflow example的core implementation來自Lab 02，RAG binding來自Lab 05。
Multi-agent example的core implementation來自Lab 03，approval binding來自
Lab 07。Composition屬於Blueprint；Catalog仍只保存core implementation
provenance。

## Validate

```bash
make verify-blueprints
```

這個gate不需要ADK或cloud credentials。它使用Git object resolution、Python
AST、published schema與cross-domain semantic rules。
