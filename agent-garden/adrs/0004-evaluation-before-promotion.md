# ADR 0004: Bind Evaluation Evidence Before Promotion

Status: Accepted

## Context

Phase 6證明fluent output與高judge score仍可能違反tool、state、trajectory、
retrieval或policy contracts。Phase 8要求production promotion使用staging測過
的同一artifact與behavior report。

## Decision

Behavior Gate：

- 消費exact immutable release candidate；
- 保留dataset、trace與grade stages；
- 對每個requested blocking metric fail closed；
- 產生綁candidate digest的immutable behavior report。

Deployment Controller只能在report passed且candidate/report match時promote。

## Consequences

- Judge metric不能覆蓋deterministic blocker。
- Missing case或`NOT_EVALUATED`不能成為success。
- Re-evaluation產生新report，不修改舊evidence。

## Evidence

- `labs/06-evaluation/evaluation_lab/engine.py`
- `docs/evaluation/evaluation-engineering.md`
- `labs/08-production-engineering/production_lab/policy.py`
