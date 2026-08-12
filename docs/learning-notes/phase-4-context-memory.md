# Phase 4 Learning Note: Context, State, Artifacts and Memory

Date: 2026-08-12

## Questions

1. Which data belongs only in the current model request?
2. How do Session state prefixes change persistence scope?
3. When does an artifact reduce context pressure?
4. How does Session history become cross-session memory?
5. What survives deletion, and who enforces tenant isolation?

## Hypotheses

1. Storage and model visibility are orthogonal.
2. State needs explicit writers and freshness policy.
3. Artifacts reduce repeated context only when loaded selectively.
4. Memory requires explicit ingestion and separate deletion governance.
5. User identity at the memory-service boundary is security-critical.

All five are supported within the in-memory scripted scope.

## Primary Sources

Pinned runtime:

```text
google/adk-python
a56f6e13ae38296b608808c7a3b37efe4b8c862e
google-adk 2.6.3
```

Studied symbols:

- `RunConfig.model_input_context`;
- instruction processors and `ReadonlyContext`;
- `State`, `BaseSessionService`, `InMemorySessionService`;
- `BaseArtifactService`, `InMemoryArtifactService`, artifact `Context` APIs;
- `BaseMemoryService`, `InMemoryMemoryService`;
- `load_memory` and `preload_memory`;
- related state, artifact and memory tests.

Exact links are in
[`references/source-index.md`](../../references/source-index.md).

## Experiment Design

One fixed support dossier contains:

```text
contact channel = SMS
previous fix = router reboot
product = HomeHub
account tier = priority
```

Four adapters expose it to one scripted Agent:

```text
caller -> model_input_context
Session state -> instruction placeholder
artifact service -> explicit load tool
memory service -> preload search
```

## Baseline Results

| Placement | Requests | Request chars | Stored Events | Persistent owner |
|---|---:|---:|---:|---|
| Transient | 1 | 240 | 2 | None |
| State | 1 | 263 | 2 | Session service |
| Artifact | 2 | 125, 254 | 4 | Artifact service |
| Memory | 1 | 446 | 2 | Memory service |

All produced the same scripted answer.

The artifact path required a model call to choose the load tool, then a second
model call with the tool response. Preloaded memory added no callable tool.

## Stale State

Turn two said the customer changed from SMS to email. No state writer ran.

The request contained both:

```text
instruction state: Preferred contact channel: SMS
user message: changed ... to email
```

Session state still contained the old dossier. Conversation does not
automatically reconcile state.

## Large Context

The payload exceeded 20 KB.

```text
transient: [22961, 22912] chars, payload in both requests
artifact:  [125, 22976, 104] chars, payload only after load
```

The artifact prevented resend on an unrelated second turn, but loaded content
still appeared in the tool-response Event and model request.

## State Scope

One Event wrote four keys.

Observed views:

```text
current invocation:
  session + user + app + temp

same Session after read:
  session + user + app

new Session, same user:
  user + app

new Session, other user:
  app
```

The persisted Event delta excluded `temp:`. Prefixed keys also bypassed the
declared state schema.

## Artifact Lifecycle

- versions were `[0, 1]`;
- latest and version zero returned different payloads;
- a session artifact did not cross Sessions;
- a `user:` artifact crossed Sessions for the same user;
- it did not cross users;
- deletion removed all versions of that artifact.

## Memory Lifecycle

The source Session was explicitly ingested. Search returned its event only for
the correct user.

After deleting the Session, memory still returned the event. An event ingested
with `ttl="0s"` also remained in the in-memory service.

The base API has no portable delete method, and TTL metadata is
implementation-defined.

## Intentional Isolation Failure

`LeakyMemoryService` discarded the requesting user ID and searched Alice for
every caller.

Bob's preloaded request contained `ALICE-SECRET`.

This is not an ADK in-memory service defect. It demonstrates that a custom
memory adapter can defeat isolation even when the Agent and tool APIs pass the
correct caller identity.

## Source-to-Experiment Corrections

Initial assumption:

> Session history automatically becomes memory.

Correction:

Memory remains empty until explicit ingestion.

Initial assumption:

> Moving a document to artifact storage removes its context cost.

Correction:

Storage removes default prompt inclusion. Full content costs context whenever
it is loaded into an instruction or tool response.

Initial assumption:

> Deleting the source Session deletes derived memory.

Correction:

The two services have separate lifecycles. Local memory retained the ingested
event.

## Architecture Decisions

- Use `model_input_context` for caller-owned invocation facts.
- Keep mutable process facts in typed state with one writer and freshness.
- Validate prefixed state keys independently.
- Use artifacts for large/versioned data and load selectively.
- Treat artifact tool responses as persisted context-bearing Events.
- Ingest memory deliberately and evaluate retrieval quality.
- Make memory deletion and TTL explicit product operations.
- Require app/user isolation tests for every memory adapter.
- Do not treat memory as exact current state.

## Verification

Commands:

```bash
make verify
make verify-context-memory
```

Current Lab 04 results:

- 6 dependency-free placement tests;
- 13 ADK-backed lifecycle tests;
- 28,792-byte deterministic JSON evidence bundle;
- repeated render is byte-identical.

## Limits

- Scripted model does not test context utilization quality.
- Character counts are not provider token counts.
- In-memory memory is keyword matching.
- No durable artifact or memory backend.
- No managed Memory Bank TTL/deletion integration test.
- No concurrent state update or optimistic-lock test.
- No automatic context compaction experiment.

## Roadmap Effect

Phase 4 local exit gate is satisfied:

- data surfaces have explicit lifecycle and ownership;
- retention, isolation, stale state and deletion gaps are observable;
- context size behavior is measured at request level.

Phase 5 can now compare RAG ownership and retrieval quality without confusing
retrieval context, Session state, artifacts and long-term memory.
