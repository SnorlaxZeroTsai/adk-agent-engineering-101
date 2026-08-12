# Lab 10: Agent Garden Discovery

這個dependency-free lab比較ADK recipe manifest、Starter Pack template
config與Agents CLI project manifest，並驗證最小CatalogEntry。

Baseline包含：

- 3個upstream metadata contracts；
- 33個field-level ownership rows；
- catalog、scaffold、runtime、governance四個planes；
- 9個required discovery facts；
- 1個stable Agent identity；
- 1個immutable implementation與assurance artifact。

## Deliberate Breakages

13個misleading entries涵蓋：

- missing或project-derived catalog identity；
- mutable source/template ref；
- frozen legacy path；
- framework、language、status drift；
- missing owner或assurance；
- scaffold deployment targets越權；
- deprecation沒有replacement；
- 同一implementation重複註冊。

## Run

```bash
python3 -m unittest discover -s tests -v
python3 scripts/run_discovery_gate.py --variant baseline
! python3 scripts/run_discovery_gate.py --variant broken
python3 scripts/run_discovery_traces.py
```

From the repository root:

```bash
make verify-agent-garden-discovery
```

## Boundary

`agent-garden/catalog-entry.schema.json`刻意不包含model、tool、workflow、
policy、evaluation、secret、deployment或release設定。它不是Phase 11
Blueprint schema。
