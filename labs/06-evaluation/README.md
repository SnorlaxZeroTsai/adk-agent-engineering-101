# Lab 06: Cross-Architecture Evaluation Gate

This lab turns six architecture milestones into one CI-style release gate.
It keeps three stages separate:

1. `EvalDataset`: expected behavior and thresholds;
2. `TraceSet`: normalized runtime evidence with no verdict;
3. `SuiteReport`: per-case metric results and a process exit decision.

## Dimensions

- runtime completion and error propagation;
- exact tool names, order and arguments;
- Event or Workflow-node trajectory;
- nested state and forbidden state paths;
- final observable output;
- model-request budget;
- policy and cross-user isolation;
- retrieval and citation grounding;
- an explicitly scripted, non-blocking response-quality judge.

Blocking deterministic metrics use `all_cases` aggregation. A passing average
or judge score cannot compensate for one failed critical case.

## Cross-Phase Cases

| Case | Baseline | Deliberate break |
|---|---|---|
| Agent | successful order tool round trip | unhandled tool exception |
| Workflow | explicit graph rejection on loop exhaustion | legacy unsafe finalization |
| Multi-agent | one bounded task specialist | two specialists overwrite shared state |
| Context/memory | user-scoped memory preload | cross-user memory adapter leak |
| RAG | source-preserving explicit retrieval | provenance removed before answer |
| Safety/HITL | scoped, expiring approval before one payment | prompt-only instruction executes without approval |

## Run

Dependency-free engine tests:

```bash
python3 -m unittest discover -s tests -v
```

ADK-backed cross-phase tests:

```bash
../01-agent-basics/.venv/bin/python \
  -m unittest discover -s runtime_tests -v
```

Passing gate:

```bash
../01-agent-basics/.venv/bin/python \
  scripts/run_eval_gate.py --variant baseline
```

Expected failing gate:

```bash
../01-agent-basics/.venv/bin/python \
  scripts/run_eval_gate.py --variant broken
```

The second command intentionally exits with status `1`.

## Limits

The quality judge is a labeled scripted score, not an LLM judge. The lab does
not measure live-model variance, statistical confidence, latency, token usage
or monetary cost. It proves the release-policy shape and deterministic
architecture contracts.
