# Lab 04: Context, State, Artifacts and Memory

This lab holds one support dossier and one question constant while changing the
data lifecycle:

1. transient `RunConfig.model_input_context`;
2. Session state injected into an Agent instruction;
3. versioned artifact loaded by an explicit tool;
4. prior Session ingested into memory and preloaded by query.

No provider or cloud credential is required. Scripted models retain the real
ADK requests, Events and service effects.

## Shared Datum

```text
Preferred contact channel: SMS
Previous successful fix: router reboot
Product: HomeHub
Account tier: priority
```

The scripted answer is identical in every baseline. The comparison measures
visibility, persistence, scope and retrieval cost rather than answer quality.

## Experiments

| Experiment | Boundary being tested |
|---|---|
| Four baselines | Model visibility, request count and persistence |
| Stale state | State does not update itself from user prose |
| Large context | Repeated transient payload versus on-demand artifact load |
| State scopes | Session, `user:`, `app:` and `temp:` lifetimes |
| Artifact lifecycle | Versions, user/session scope and deletion |
| Memory lifecycle | Ingestion, user isolation, source deletion and TTL gap |
| Leaky memory adapter | Consequence of ignoring the requesting `user_id` |

## Run

Offline policy tests:

```bash
python3 -m unittest discover -s tests -v
```

ADK-backed runtime tests:

```bash
../01-agent-basics/.venv/bin/python \
  -m unittest discover -s runtime_tests -v
```

Render the deterministic trace bundle:

```bash
../01-agent-basics/.venv/bin/python \
  scripts/run_context_memory_traces.py
```

From the repository root:

```bash
make verify-context-memory
```

## Files

- `context_memory_lab/domain.py`: placement policy and shared dossier.
- `context_memory_lab/runtime.py`: service-backed lifecycle experiments.
- `runtime_tests/test_context_memory.py`: behavioral assertions.
- `OBSERVATIONS.md`: measured results and limits.
