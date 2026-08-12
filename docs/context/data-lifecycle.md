# Context, State, Artifact and Memory Lifecycles

Status: pinned ADK 2.6.3 source analysis and local scripted runtime experiments
complete.

## Question

Where should a datum live when an Agent needs it now, later in the same
Session, on demand as a large payload or across Sessions?

## Hypothesis

Choose placement from lifecycle and ownership, not convenience:

- transient model context for invocation-only facts;
- typed state for small mutable process facts;
- artifacts for large or versioned payloads;
- memory for intentionally ingested cross-session recall.

Storage and model context are separate decisions. Persisting a value does not
make it model-visible, and injecting a value does not define retention.

## Four Data Surfaces

| Surface | Model visibility | Persistence | Typical owner |
|---|---|---|---|
| `model_input_context` | Current invocation | None | Caller |
| Session state | Instruction/tool/callback injection | Session, user, app or temp scope | Runtime and application |
| Artifact | Only when explicitly loaded/injected | Versioned service storage | App/user/session |
| Memory | Search or preload result | Memory-service policy | App + user |

## Transient Model Context

`RunConfig.model_input_context` is inserted into the LLM request before the
current user message. The Runner does not append it to Session Events.

It is suitable for:

- request-specific authorization decisions already made upstream;
- current page or selected-record context;
- retrieval results that should not become conversation history;
- volatile facts supplied by the caller.

The caller must provide it again on another invocation. This is useful
ephemerality and a potential repeated-token cost.

`include_contents="none"` controls conversation history. It does not remove
`model_input_context` for the current invocation.

## Instruction and State Context

A string instruction can contain state placeholders:

```text
Use this support context: {support_context}
```

The instruction processor resolves placeholders against the current Session.
Missing required variables raise `KeyError`; a `?` suffix makes a variable
optional.

A callable `InstructionProvider` receives `ReadonlyContext` and bypasses the
automatic placeholder pass. It must perform any templating itself.

`static_instruction` is different:

- it is sent literally;
- it is intended for stable cacheable content;
- dynamic `instruction` moves into user content when static content exists;
- configuring it does not itself enable explicit caching.

The old `global_instruction` field is deprecated in favor of an App-level
plugin.

## State Scopes

`State` tracks a current value and pending Event delta.

| Key form | Scope in Session service |
|---|---|
| `key` | Current Session |
| `user:key` | Same app and user across Sessions |
| `app:key` | Same app across users and Sessions |
| `temp:key` | Current invocation object; removed before persistence |

The in-memory service stores app and user state separately, then merges prefixed
views into each returned Session.

### Schema Boundary

`state_schema` validates unprefixed keys and values. Any key containing `:`
bypasses schema validation.

This permits framework namespaces and cross-scope values, but means a typed
Workflow schema does not protect `user:`, `app:` or `temp:` contracts.
Applications need separate validators and naming ownership for prefixed state.

### Staleness

State is not inferred from conversation. If a user says that a preference
changed but no tool, callback or node writes the new value, instruction
injection continues to expose the old state.

State therefore needs:

- an authoritative writer;
- freshness/version metadata when relevant;
- conflict policy;
- invalidation or deletion behavior;
- tests for disagreement between user prose and stored facts.

## Artifacts

An artifact is a `types.Part` addressed by app, user, optional Session,
filename and version.

### Scope

- normal filename: Session-scoped;
- filename starting `user:`: user-scoped across Sessions;
- every path still includes app and user.

`Context.save_artifact()` records the returned version in the Event's
`artifact_delta`. `load_artifact()` returns the latest version unless a version
is named.

### Version and Deletion

Successful saves start at version 0 and increment. Metadata includes:

- canonical URI;
- create time;
- MIME type;
- custom metadata.

`delete_artifact()` removes the selected artifact and all its versions in the
tested in-memory implementation.

### Context Cost

An artifact is not automatically model context. A tool or instruction template
must load it. Once its full content enters a function response or instruction,
it consumes context like any other text.

Artifacts reduce default prompt size only when loading is selective.

## Memory

Memory is separate from Session storage. A Session becomes searchable only
after:

```text
add_session_to_memory(session)
```

or an explicit event/direct-memory write supported by the service.

The base search contract is scoped by:

```text
app_name + user_id + query
```

### Retrieval Modes

`load_memory` is model-selected. It adds a function declaration and tells the
model that memory is available.

`preload_memory` is runtime-selected. For each LLM request it:

1. uses current user text as the query;
2. searches memory;
3. converts text results into a dynamic instruction under
   `<PAST_CONVERSATIONS>`;
4. does not register a callable model tool.

Preloading is convenient but injects every matching result before the model
decides whether it is relevant.

### Retention and Deletion

`BaseMemoryService` defines ingestion and search, but no portable delete API.
Provider-specific services may accept TTL metadata; support is
implementation-defined.

In the local experiment:

- deleting the source Session did not delete already ingested memory;
- `InMemoryMemoryService` ignored `ttl="0s"`;
- search still returned both entries.

Session deletion and memory deletion are separate workflows.

## Lab 04 Baseline

One support dossier answered one fixed question through four placements.

| Placement | Model requests | Request chars | Stored Events | Stored dossier |
|---|---:|---:|---:|---|
| Transient | 1 | 240 | 2 | No |
| State | 1 | 263 | 2 | Session state |
| Artifact | 2 | 125, 254 | 4 | Artifact service + tool Event |
| Memory | 1 | 446 | 2 | Memory service |

All returned the same scripted answer.

These metrics describe the harness. They are not tokens, latency or cost.

## Large-Context Break

A greater-than-20-KB dossier was supplied across two turns.

Transient:

```text
request chars: [22961, 22912]
payload present: [true, true]
```

Artifact:

```text
request chars: [125, 22976, 104]
payload present: [false, true, false]
```

The artifact added one model/tool round trip, but the unrelated next turn did
not resend the payload. This is a lifecycle trade-off, not a claim that
artifacts make loaded content free.

## Cross-User Memory Break

The official in-memory service returned no Alice memory for Bob.

An intentional adapter bug ignored the incoming `user_id` and always searched
Alice. Bob's request then contained:

```text
ALICE-SECRET
```

The model and preload tool cannot repair a broken identity boundary below
them. Memory adapters must include tenant-isolation tests.

## Decision Guide

Use transient context when:

- only this invocation needs the datum;
- the caller is authoritative;
- it must not enter Session history.

Use state when:

- the datum is small and mutable;
- process steps need direct keyed access;
- its scope and writer are explicit.

Use an artifact when:

- payload is large, binary or versioned;
- loading can be on demand;
- a canonical reference is useful.

Use memory when:

- recall crosses Sessions;
- ingestion is intentional;
- retrieval quality, retention and deletion are governed.

Do not use memory as a replacement for exact current state. Do not put large
documents into state merely because placeholders can inject them.

## Engineering Checklist

- Name the writer, readers and authoritative source.
- Declare lifetime: invocation, Session, user, app or retained memory.
- Declare whether model visibility is automatic or on demand.
- Validate prefixed state separately from `state_schema`.
- Record freshness/version and invalidate stale state.
- Keep large payloads out of every request unless always required.
- Test artifact version selection and namespace isolation.
- Test memory ingestion separately from search.
- Test cross-user and cross-app isolation.
- Implement memory deletion/TTL as a product workflow, not an assumption.
- Measure real tokens, latency and cost with a live model before production.
