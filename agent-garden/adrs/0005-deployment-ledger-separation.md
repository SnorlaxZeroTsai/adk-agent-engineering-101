# ADR 0005: Separate Deployment Control From Release History

Status: Accepted

## Context

Deployment Controller需要target credentials並操作mutable platform status。
Release Ledger需要append-only history、previous release與promotion evidence，
但不需要cloud credentials。Agents CLI current metadata只保存current或pending
resource，不能回答rollback history。

## Decision

- Deployment Controller build/stage/promote/rollback並回報platform revision。
- Release Ledger驗證candidate、behavior report與deployment status後append
  ReleaseRecord。
- Ledger從previous immutable record產生RollbackPlan。
- Deployment Controller執行plan；Ledger不呼叫target API。

## Consequences

- Target compromise不能直接改寫release history。
- Ledger outage不授權unchecked promotion。
- Deployment status可丟失或重建，不影響rollback truth。

## Evidence

- `labs/08-production-engineering/production_lab/release.py`
- `docs/production/production-engineering.md`
- `references/source-index.md`
