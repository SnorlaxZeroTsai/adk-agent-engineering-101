# ADR 0002: Use Git First, Not A Premature Registry Service

Status: Accepted

## Context

Phase 10與11的Catalog、Blueprint、Implementation source與schemas都已有stable
Git identity、review history與full revision pins。MVP尚無證據需要distributed
database、event bus或independent schema registry。

## Decision

- Catalog index、Blueprint、schema與Implementation source先保存在version
  control。
- Validation report、release candidate與behavior report使用
  content-addressed store。
- Project Instance與rollback plan是regenerable workspace artifacts。
- Release records進append-only ledger。
- Deployment status留在target control plane，僅作cache。
- Secret material只存在external secret manager。

## Consequences

- MVP可用filesystem/Git實作而不改contract。
- 後續storage adapter必須保留digest、immutability與write model。
- Mutable index或platform status不能成為source/release truth。

## Evidence

- `agent-garden/blueprints/catalog-snapshot.json`
- `labs/08-production-engineering/production_lab/release.py`
- `labs/10-agent-garden-discovery/garden_discovery/validation.py`
