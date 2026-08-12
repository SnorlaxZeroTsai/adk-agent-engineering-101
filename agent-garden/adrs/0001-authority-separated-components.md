# ADR 0001: Separate Components By Authority

Status: Accepted

## Context

CatalogEntry、Blueprint、Project Instance、behavior report、deployment status與
release record有不同identity、mutability與accountable owner。將它們塞進同一
service或manifest會重建Phase 8–11已觀察到的dual ownership。

## Decision

MVP使用六個components：

1. Catalog Registry；
2. Contract Validator；
3. Project Renderer；
4. Deployment Controller；
5. Behavior Gate；
6. Release Ledger。

CLI只負責呼叫這些components，不擁有新的authority。

## Consequences

- 同一artifact只有一個authority owner。
- Pure components不取得deployment credentials。
- Runtime status與release history無法互相冒充。
- Component間需要typed artifacts與digest binding。

## Evidence

- `agent-garden/concepts.md`
- `agent-garden/blueprint-schema.md`
- `docs/production/production-engineering.md`
