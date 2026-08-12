# Lab 03: Multi-Agent Specialist Boundaries

This lab holds one typed case-triage capability constant while changing only
its execution boundary:

1. deterministic Workflow function node;
2. isolated `single_turn` Agent node;
3. conversational transfer to a chat Agent;
4. coordinator-selected task Agent.

No provider or cloud credential is required. `ScriptedModel` makes every model
response deterministic while retaining the actual ADK requests and Events.

## Common Contract

Input:

```text
case_id, amount_usd, days_open, chargeback_signal, customer_tier
```

Output:

```text
case_id, risk_level, owner, reasons
```

All four happy paths materialize the same decision in Session state. The
comparison therefore measures architecture rather than model quality.

## Experiments

| Experiment | Boundary being tested |
|---|---|
| Baseline comparison | Model calls, Event trajectory, state and isolation |
| Transfer continuation | Which Agent owns the next conversational turn |
| Task validation recovery | Whether invalid `finish_task` output can be repaired |
| Hard task failure | Error Event and fallback behavior |
| Overlapping specialists | Ambiguous descriptions and model-selected routing |
| Shared-state conflict | Two task Agents writing the same state key |

## Run

Offline domain tests:

```bash
python3 -m unittest discover -s tests -v
```

ADK-backed runtime tests:

```bash
../01-agent-basics/.venv/bin/python \
  -m unittest discover -s runtime_tests -v
```

Render the complete trace bundle:

```bash
../01-agent-basics/.venv/bin/python \
  scripts/run_multi_agent_traces.py
```

From the repository root:

```bash
make verify-multi-agent
```

## Files

- `multi_agent_lab/domain.py`: dependency-free business capability.
- `multi_agent_lab/builders.py`: four baseline roots and broken variants.
- `multi_agent_lab/runtime.py`: Runner harness and JSON-safe Event summaries.
- `runtime_tests/test_multi_agent.py`: behavioral architecture assertions.
- `OBSERVATIONS.md`: concise observed results and limits.
