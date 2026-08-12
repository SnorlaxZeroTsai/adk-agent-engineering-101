# Lab 05: RAG Engineering

This lab compares two RAG ownership models against one versioned, access-aware
corpus:

- provider-native Search through `VertexAiSearchTool`;
- caller-owned chunking/indexing exposed through a `FunctionTool`.

The managed path uses the real ADK built-in-tool request surface with a
scripted provider model. The explicit path uses the real FunctionTool
call/response lifecycle. Neither path needs cloud credentials.

## Shared Contract

Both paths receive the same:

- source documents, versions, ACL labels and deleted-document set;
- public/internal principals;
- five baseline query cases;
- deterministic evidence-only answer composer;
- retrieval recall/precision, citation fidelity, ACL, stale-hit and deletion
  gates.

## Intentional Breaks

- remove the principal filter from native Search;
- strip document ID/version/URI from explicit retrieval;
- retain an obsolete document version during incremental ingestion;
- fail to remove an indexed document after source deletion.

## Run

Offline domain and retrieval tests:

```bash
python3 -m unittest discover -s tests -v
```

ADK-backed runtime tests:

```bash
../01-agent-basics/.venv/bin/python \
  -m unittest discover -s runtime_tests -v
```

Render the deterministic evidence bundle:

```bash
../01-agent-basics/.venv/bin/python scripts/run_rag_traces.py
```

## Limits

The managed search backend and model are scripted. The lab proves ADK request,
Event and provenance contracts, not live Search relevance, service latency,
token accounting or monetary cost. Those remain credentialed integration
gates.
