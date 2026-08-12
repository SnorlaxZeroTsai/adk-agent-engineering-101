# Lab 01: Agent Basics

This lab isolates the first architecture boundary:

```text
natural-language intent and tool choice -> Agent
deterministic lookup and pricing       -> typed Python tools
application/runtime services           -> outside this lab
```

The offline path uses only Python stdlib. ADK and model credentials are required
only for interactive execution.

## Hypothesis

A small Agent with narrow tool contracts is easier to inspect, test and evolve
than one catch-all tool that accepts a free-form query.

## Files

| Path | Purpose |
|---|---|
| `agent_basics/agent.py` | ADK `Agent` and `App` definition |
| `agent_basics/tools.py` | Deterministic baseline tools |
| `experiments/broken_tools.py` | Intentional catch-all and exception variants |
| `scripts/inspect_contract.py` | AST/signature inspection without importing ADK |
| `tests/` | Baseline behavior and broken-boundary observations |
| `OBSERVATIONS.md` | Current evidence and unverified claims |

## Offline Baseline

```bash
python3 -m unittest discover -s tests -v
python3 scripts/inspect_contract.py
```

The tests check:

- order IDs are normalized;
- missing orders return structured domain errors;
- shipping rules are deterministic and validate their domain;
- the Agent source exposes exactly the two intended tools;
- the broken lookup raises while the baseline returns data;
- the catch-all signature removes explicit business inputs.

## Interactive ADK Run

Create `.env` from `.env.example`, configure either a Gemini API key or Vertex
AI credentials, then:

```bash
uv sync --dev
uv run adk run agent_basics
```

Suggested prompts:

```text
What is the status of order A100?
Estimate shipping to the regional zone for 2.5 kg.
What is order Z999?
Ship order A100 now.
```

The last prompt tests scope: the Agent has no mutation tool and must not claim
that it shipped anything.

## Intentional Break Experiment

Inspect `experiments/broken_tools.py`, then compare its signatures in the
contract inspector output.

1. The catch-all tool accepts only `query: str`; required domain fields are
   hidden inside natural language.
2. The raising lookup treats a normal "not found" outcome like a program
   failure.
3. Tests record these differences without making the project test suite fail.

Do not "fix" the broken variants. They are controlled counterexamples.

## Exit Gate

This lab is complete only after:

- offline tests pass;
- contract inspection output is recorded;
- a fake-model ADK Runner trace verifies tool-call and event behavior;
- a live model is tested separately and its model/version is recorded.

The first two are implemented. Runtime gates remain pending.
