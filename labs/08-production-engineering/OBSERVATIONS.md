# Lab 08 Observations

Observed from the fixed stdlib-only production envelope.

## Replaceable Rendering

The local, Cloud Run and Agent Runtime renders retained identical:

- `agent/contract.json`;
- `quality/behavior-gate.json`.

Changing target modified only:

- `runtime/config.json`;
- `deployment/spec.json`;
- `lifecycle/manifest.json`;
- derived `release/candidate.json`.

This is the local proof that deployment topology is an overlay around Agent
behavior rather than a reason to fork the Agent implementation.

## Release and Rollback

The append-only ledger retained separate staging and production records.
Production v4 used the same artifact and behavior-report digests that passed
staging.

Rollback plans were target-specific:

| Target | Strategy |
|---|---|
| Local | restart the prior source artifact |
| Cloud Run | shift 100% traffic to the prior platform revision |
| Agent Runtime | restore the prior immutable source bundle and redeploy |

Current-resource metadata alone failed because it did not identify the
artifact, source, behavior report, previous release or rendered spec.

## Configuration and Telemetry

- Plaintext `PAYMENTS_API_KEY` produced separate config and render-leak
  failures.
- A merge-style update retained unmanaged `DEBUG_BYPASS=true`; drift
  detection blocked before deploy.
- Full content telemetry without governance approval, sink and retention
  produced three independent failures.
- Secret references retained ID and pinned version without rendering secret
  material.

## Gate Results

- Baseline: 7 scenarios, 0 blocking failures, exit `0`.
- Broken: 8 scenarios, 23 blocking failures, exit `1`.
- Offline tests: 18.
- Two 43,765-byte evidence renders were byte-identical.
- SHA-256:
  `d3d51a6a421c37ef7dd775bb456b84142b9166dfaab603b081e07a624355cf89`.

## Limits

No real build, deploy, migration, telemetry export or rollback was performed.
The release ledger is in memory and has no signing, transactional store,
artifact registry attestation or external identity verification.
