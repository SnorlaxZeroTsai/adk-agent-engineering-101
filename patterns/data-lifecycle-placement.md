# Data Lifecycle Placement

Status: `validated`.

Portability: `portable`.

Canonical manifest:
[`manifests/data-lifecycle-placement.json`](manifests/data-lifecycle-placement.json).

## Problem

Agent data is placed in prompts, state, artifacts or memory without an explicit
lifecycle, causing stale facts, repeated context, cross-user exposure or
undeletable derived data.

## Context

Use this pattern when data crosses an invocation, Session or user boundary, or
when payload size, freshness, tenancy, retention and deletion matter.

## Forces

- Transient context must be supplied on each invocation.
- State needs schema, concurrency and freshness policy.
- Artifact load adds I/O.
- Memory adds ingestion, retrieval evaluation and deletion workflows.

## Decision

Choose placement from writer, readers, scope, freshness, retention and
deletion:

```text
invocation-only                  -> model_input_context
small mutable process fact       -> typed state
large/versioned/on-demand data   -> artifact
intentional cross-session recall -> memory
```

## Architecture

The application owns the placement decision and lifecycle policy. ADK context,
state, artifact and memory services implement different visibility and
persistence contracts rather than interchangeable storage APIs.

## Observable Contract

| ID | Contract |
|---|---|
| `transient-is-not-persisted` | Invocation context is model-visible for one run and absent from Session state/history. |
| `state-scope-is-explicit` | Session, user, app and temporary state materialize and persist differently. |
| `artifact-is-versioned-on-demand` | Large payloads retain artifact version/scope and enter context only after load. |
| `memory-has-separate-lifecycle` | Recall requires ingestion and identity-scoped search independent of Session deletion. |

## When To Use

- runtime context and persistent data coexist;
- user/app/session tenancy matters;
- blobs exceed comfortable prompt size;
- prior conversations may be recalled;
- deletion and retention obligations exist.

## When Not To Use

- a pure function receives all data through normal parameters;
- no value crosses an invocation boundary;
- a current lookup belongs in a transactional system of record.

## Implementation

1. Pass small transient values through `model_input_context`.
2. Validate scoped state before mutation and namespace independent writers.
3. Save large payloads as versioned artifacts and load them on demand.
4. Ingest memory explicitly.
5. Apply app/user identity in memory search.
6. Orchestrate retention and deletion beyond Session lifecycle.

## Failure Modes

| ID | Failure |
|---|---|
| `stale-or-repeated-context` | State remains stale or large transient context is resent every turn. |
| `scoped-state-bypasses-schema` | Prefixed user/app state bypasses Agent `state_schema`. |
| `session-delete-assumption` | Session deletion is assumed to delete memory or user artifacts. |
| `cross-user-recall` | A memory adapter ignores identity and returns another principal's data. |

## Counterexamples

Use function parameters when nothing persists. Use a database or API tool for
current deterministic records rather than treating Agent memory as a system of
record.

## ADK Versions

- ADK 2.6.3 context, state, artifact and memory behavior is validated.
- The placement decision is portable; concrete namespaces and deletion APIs
  require runtime-specific adapters.

## Evidence

- Source and claim-level links:
  [`manifests/data-lifecycle-placement.json`](manifests/data-lifecycle-placement.json)
- Architecture analysis:
  [`../docs/context/data-lifecycle.md`](../docs/context/data-lifecycle.md)
- Executable evidence:
  [`../labs/04-context-and-memory`](../labs/04-context-and-memory/)

## Rejected Decisions

`one-opaque-state-blob`: reject placing every datum in one Session state object
and injecting it into every prompt. Select context, state, artifact or memory
from an explicit lifecycle contract.
