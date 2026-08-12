# ADR 0003: Keep Project Rendering Pure And Credential-Free

Status: Accepted

## Context

Starter Pack與Agents CLI證明template composition有價值，但rendered config、
deployment action與live environment merge有不同owners。Renderer若能解析
secret material或直接deploy，就無法重現、diff或安全測試。

## Decision

Project Renderer只消費passing validation report、immutable source、
Blueprint與secret references，輸出有digest的regenerable Project Instance。

Renderer不得：

- 取得secret values；
- 更改Catalog、policy或evaluation contracts；
- build、stage、promote或rollback。

## Consequences

- 同一input可byte-deterministically render。
- Deployment target adapters可替換。
- Project Instance manifest是derived output，不是Agent identity。

## Evidence

- `labs/08-production-engineering/production_lab/rendering.py`
- `docs/production/production-engineering.md`
- `agent-garden/discoverability-contract.md`
