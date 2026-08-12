# Lab 12: MVP Architecture

這個dependency-free lab從Phase 8、10與11已驗證的contracts反推Mini Agent
Garden的最小component model，而不是先選database、queue或distributed
runtime。

Baseline驗證：

- 6個authority-separated components；
- 12個typed artifacts與6種storage classes；
- 9個trust boundaries與7個extension points；
- `discover -> validate -> render -> stage -> evaluate -> promote -> record`
  release path；
- `plan-rollback -> execute-rollback` rollback path；
- single Agent、Workflow/RAG與multi-agent/HITL三個Blueprint walkthroughs；
- 6份Accepted ADRs與所有repository evidence refs。

## Deliberate Breakages

15個invalid cases涵蓋artifact ownership、credential scope、secret material、
candidate/report immutability、deployment cache、append-only release history、
typed architecture extension、adapter guards、promotion evidence、walkthrough
validator/metric coverage與missing ADR。

## Run

```bash
python3 -m unittest discover -s tests -v
python3 scripts/run_architecture_gate.py --variant baseline
! python3 scripts/run_architecture_gate.py --variant broken
python3 scripts/run_architecture_traces.py
```

From the repository root:

```bash
make verify-mvp-architecture
```

## Boundary

這個lab驗證component authority、artifact flow、storage/trust/extension boundary
與deterministic lifecycle receipts。它不建立cloud resource、不解析secret
value、不證明transactional deploy/ledger commit，也不實作Phase 13 CLI。
