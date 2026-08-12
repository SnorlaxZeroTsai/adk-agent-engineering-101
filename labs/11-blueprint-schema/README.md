# Lab 11: Executable Blueprint Schema

這個dependency-free lab先固定三個materially different Blueprint examples，
再驗證共同schema與architecture-specific semantics：

- single Agent + typed tools；
- deterministic Workflow + RAG；
- coordinator/task specialist + durable approval。

Baseline驗證：

- 3個CatalogEntries與3個immutable implementations；
- 3個architecture branches；
- 38個local refs，26個unique refs；
- pinned Git entrypoints與behavior assurance digests；
- graph、retrieval、delegation、state、policy、eval與lifecycle invariants；
- flat v0.1 single-Agent到v1.0的exact migration。

## Deliberate Breakages

15個invalid cases涵蓋unknown catalog refs、authority duplication、missing
entrypoint/eval/lifecycle、unsafe write tool、broken graph/loop/RAG、
untyped specialist、namespace conflict與approval replay gap。

## Run

```bash
python3 -m unittest discover -s tests -v
python3 scripts/run_blueprint_gate.py --variant baseline
! python3 scripts/run_blueprint_gate.py --variant broken
python3 scripts/run_blueprint_traces.py
```

From the repository root:

```bash
make verify-blueprints
```

## Boundary

這裡的executable表示all contract refs可解析，core implementation固定於
immutable Git revision且已有runtime behavior tests。這個lab不呼叫live
model、不建立cloud resource，也不把Catalog metadata複製進Blueprint。
