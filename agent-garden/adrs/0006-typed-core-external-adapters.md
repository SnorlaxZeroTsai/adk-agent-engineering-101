# ADR 0006: Typed Core, Constrained External Adapters

Status: Accepted

## Context

Single Agent、Workflow與multi-agent有不同topology invariants；provider、
source、renderer、metric、deployment target與release store則需要替換。把兩者
都放進untyped plugin map會讓extension繞過state、policy、eval或release
contracts。

## Decision

- New architecture kind必須新增Blueprint typed union branch、semantic
  validator與walkthrough evidence。
- Source resolver、renderer、runtime service、metric、deployment target與
  release store使用external adapter contract。
- Adapter不得覆蓋Catalog identity、immutability、state ownership、blocking
  policy、secret policy或release evidence。

## Consequences

- Core architecture演進較慢但可靜態驗證。
- Provider與platform integration可獨立替換。
- `extensions`不能成為逃避core schema的通道。

## Evidence

- `agent-garden/blueprints/schema/blueprint.schema.json`
- `labs/11-blueprint-schema/blueprint_lab/validation.py`
- `patterns/catalog.json`
