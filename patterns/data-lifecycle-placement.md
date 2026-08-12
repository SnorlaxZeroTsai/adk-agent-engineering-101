# Data Lifecycle Placement

Status: candidate, validated locally against pinned ADK 2.6.3.

## Problem

Agent data is placed in prompts, state, artifacts or memory without an explicit
lifecycle, causing stale facts, repeated context, cross-user exposure or
undeletable derived data.

## Architecture

Classify every datum before implementation:

```text
invocation-only -> model_input_context
small mutable process fact -> typed state
large/versioned/on-demand payload -> artifact
intentional cross-session recall -> memory
```

Then define writer, readers, scope, freshness and deletion.

## When To Use

- an Agent combines runtime context with persistent data;
- the system has user/app/session tenancy;
- documents or blobs exceed comfortable prompt size;
- prior conversations may be recalled;
- deletion and retention obligations exist.

## When Not To Use

- a local pure function receives all data as normal parameters;
- no value crosses a function boundary or invocation;
- the classification adds labels but no enforceable behavior.

## Why

Each ADK surface has a different visibility and persistence contract. Explicit
placement prevents storage choice from silently defining model context or
retention.

## Alternatives

- external database with application-owned context builder;
- document store plus retrieval service;
- external workflow engine variables;
- provider-managed conversation history;
- one opaque Session state blob.

## Trade-Offs

- callers must supply transient context each invocation;
- state requires schema and conflict policy;
- artifact load adds I/O or a tool/model round trip;
- memory adds ingestion, retrieval evaluation and deletion workflows;
- cross-scope state prefixes need validation outside `state_schema`.

## Failure Modes

- stale state contradicts current user input;
- large context is resent on every turn;
- artifact content is assumed token-free after load;
- memory is searched before ingestion;
- Session deletion is assumed to delete memory;
- custom memory adapter ignores app/user identity;
- `user:` or `app:` state bypasses schema validation;
- user-scoped artifacts are used for session-private data.

## ADK Implementation

- `RunConfig.model_input_context`;
- string instruction placeholders or callable `InstructionProvider`;
- unprefixed, `user:`, `app:` and `temp:` state keys;
- `BaseArtifactService` with explicit versions and namespaces;
- `BaseMemoryService` ingestion plus `load_memory` or `preload_memory`;
- application-level retention and deletion orchestration.

## Primary Sources

- pinned content and instruction processors;
- pinned State and Session services;
- pinned artifact services and Context methods;
- pinned memory services and memory tools.

See [`../references/source-index.md`](../references/source-index.md).

## Minimal Example

See
[`../labs/04-context-and-memory/context_memory_lab/runtime.py`](../labs/04-context-and-memory/context_memory_lab/runtime.py)
and its runtime tests.
