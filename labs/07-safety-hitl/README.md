# Lab 07: Safety and Human Approval

This lab holds one consequential vendor payment constant across three control
models:

- prompt-only confirmation;
- a global `BasePlugin` policy;
- dynamic `ToolConfirmation` with an application-owned approval envelope.

It also compares tool-call confirmation with Workflow `RequestInput`.

## Enforcement Matrix

The deterministic plugin exercises:

- unsafe user input replaced at `on_user_message` and stopped at
  `before_model`;
- unsafe tool arguments blocked at `before_tool`;
- unsafe tool results replaced at `after_tool`;
- unsafe model output replaced at `after_model`.

The intentional incomplete plugin checks tool output only. It can hide a
payment result, but it cannot undo the payment that already happened.

## Approval Contract

ADK provides the pause/resume transport. The application validates:

- approval ID and approver identity;
- action ID, action type and full request hash;
- explicit approve/reject decision;
- policy version;
- issue and expiry times.

An external ledger uses `action_id` as its idempotency key. Replaying the same
confirmation can re-enter the tool on a later run, so framework confirmation
deduplication is not the side-effect idempotency boundary.

## Run

Dependency-free domain tests:

```bash
python3 -m unittest discover -s tests -v
```

ADK-backed runtime tests:

```bash
../01-agent-basics/.venv/bin/python \
  -m unittest discover -s runtime_tests -v
```

Render deterministic evidence:

```bash
../01-agent-basics/.venv/bin/python \
  scripts/run_safety_hitl_traces.py
```

## Limits

Fresh Agent, Workflow and Runner objects reuse one
`InMemorySessionService`. This proves runtime rehydration, not process-loss
durability. The lab does not authenticate a real approval UI, use a durable
ledger, negotiate live credentials or validate streaming confirmation.
