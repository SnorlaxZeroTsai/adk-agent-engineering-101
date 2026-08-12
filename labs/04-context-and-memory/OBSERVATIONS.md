# Lab 04 Observations

Pinned runtime: `google-adk 2.6.3` at
`a56f6e13ae38296b608808c7a3b37efe4b8c862e`.

## Baselines

| Placement | Model requests | Request text chars | Stored Events | Dossier in Session state |
|---|---:|---:|---:|---|
| Transient context | 1 | 240 | 2 | No |
| Session state | 1 | 263 | 2 | Yes |
| Artifact tool | 2 | 125, 254 | 4 | No |
| Preloaded memory | 1 | 446 | 2 | No |

Character counts are harness metrics, not provider token counts.

## Large Payload

A deterministic dossier longer than 20 KB produced:

```text
transient requests: [22961, 22912]
artifact requests:  [125, 22976, 104]
```

The transient context was supplied on both turns. The artifact appeared only
after the first turn's load call and was absent from the unrelated second turn.
Once loaded, artifact content still consumes model context and is persisted in
the tool-response Event.

## State

One delta demonstrated:

- unprefixed state remained only in the same Session;
- `user:` state appeared in a new Session for the same user;
- `app:` state appeared for another user in the same app;
- `temp:` state was visible on the invocation Session object but removed from
  the persisted Event and later Session read.

Prefixed keys bypass `state_schema` validation in the pinned runtime.

## Artifacts

- saves produced versions `[0, 1]`;
- latest and explicit version zero loaded independently;
- session artifact was invisible from another Session;
- `user:` artifact was visible in another Session for the same user;
- another user could not load it;
- delete removed all versions of the selected artifact.

## Memory

Memory required explicit Session ingestion. Search was correctly user-scoped.

After the source Session was deleted, its ingested memory remained searchable.
`InMemoryMemoryService` also ignored `custom_metadata={"ttl": "0s"}`.

An intentionally broken adapter that replaced the requesting user with
`alice` injected `ALICE-SECRET` into Bob's request. Memory service identity is
a security boundary.

## Limits

- Scripted answers do not measure whether a model uses context correctly.
- Character count is not token count.
- In-memory memory uses keyword matching, not semantic retrieval.
- Managed Memory Bank TTL behavior is source-level evidence only.
- Artifact and memory services are in-memory and do not prove distributed
  concurrency or deletion propagation.
