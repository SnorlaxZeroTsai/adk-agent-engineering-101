# Lab 13: Mini Agent Garden

這個dependency-free lab實作Phase 13的local product flow：

```text
list/inspect -> validate -> create -> test -> upgrade
```

Baseline會：

- discover 3個CatalogEntries與Blueprints；
- 從immutable Git commit scaffold 3個Project Instances；
- 執行13/7/7個implementation contract tests；
- 產生candidate-bound Behavior Reports；
- plan v0.1 schema migration；
- apply compatible Blueprint update並保留user-owned file；
- append一筆secret-free local release evidence；
- 注入typed experimental architecture handler，走相同CLI path。

## Deliberate Breakages

11個invalid flows涵蓋unknown Blueprint、missing metric、managed-file tamper、
forged candidate digest、failing behavior command、unreviewed Implementation
change、duplicate/secret-bearing ledger record、unknown handler、existing
output與untyped architecture。

## Run

```bash
python3 -m unittest discover -s tests -v
python3 scripts/run_garden_gate.py --variant baseline
! python3 scripts/run_garden_gate.py --variant broken
python3 scripts/run_garden_traces.py
```

From the repository root:

```bash
make verify-mini-agent-garden
```

## Boundary

這個lab不deploy cloud、不跑live model，也不把JSONL ledger宣稱為durable
transactional service。它驗證local CLI、authority boundaries與typed artifacts。
