# Lab 02: Workflow Engineering

This lab holds deterministic business rules constant while comparing:

- deprecated `SequentialAgent`, `ParallelAgent` and `LoopAgent`;
- ADK 2.0 graph `Workflow`, `FunctionNode` and `JoinNode`;
- retry, loop exhaustion, state failure, output delegation and resume behavior.

The runtime uses the exact pinned `google-adk 2.6.3` source. No model or cloud
credential is required.

## Run

Dependency-free domain tests:

```bash
python3 -m unittest discover -s tests -v
```

ADK-backed comparison tests, using Lab 01's pinned environment:

```bash
../01-agent-basics/.venv/bin/python \
  -m unittest discover -s runtime_tests -v
```

Render the full evidence bundle:

```bash
../01-agent-basics/.venv/bin/python scripts/run_workflow_traces.py
```

## Experiments

1. Equivalent happy path with sequence, fan-out/join and iterative review.
2. Review limit that silently falls through in an unsafe legacy variant but
   explicitly routes to rejection in the graph.
3. Built-in graph node retry versus an un-retried legacy child exception.
4. Missing state parameter with a node-path error event.
5. Duplicate dynamic output versus `use_as_output=True` delegation.
6. Fresh Runner/root-object resume over the same Session service.

The resume experiment intentionally records a pinned-runtime difference:
the graph root rehydrates and continues downstream, while the legacy composite
resume is routed to the interrupted leaf and does not naturally continue the
parent tail.
