# Phase 5 Learning Note: RAG Engineering

Date: 2026-08-12

## Questions

1. What work does "managed RAG" actually remove?
2. What does an explicit Vector Search application own?
3. Where do source identity, ACL, version and deletion policy live?
4. Can a final answer look correct while the RAG system is wrong?
5. What evidence must a RAG regression test retain?

## Hypotheses

1. Managed Search should use fewer application/model steps because retrieval is
   provider-native.
2. Explicit retrieval should expose more controllable evidence at the cost of
   another model turn and ingestion code.
3. Stable provenance is required to evaluate citations, stale versions and
   deletion.
4. Generic response-quality evaluation will miss retrieval lifecycle failures.

## Primary Sources

Runtime:

- `src/google/adk/tools/vertex_ai_search_tool.py`
- `src/google/adk/tools/discovery_engine_search_tool.py`
- `src/google/adk/tools/retrieval/base_retrieval_tool.py`
- `src/google/adk/tools/retrieval/vertex_ai_rag_retrieval.py`
- `src/google/adk/agents/llm_agent.py`
- grounding preservation tests in `tests/integration/` and `tests/unittests/`

Managed recipe:

- `core/python/rag-agent-search/AGENTS.md`
- `app/retrievers.py`
- `infra/terraform/agent_platform_search.tf`
- connector setup/read/delete scripts
- `tests/eval/eval_config.yaml`

Explicit recipe:

- `core/python/rag-vector-search/AGENTS.md`
- `app/agent.py`
- `app/retrievers.py`
- `data_ingestion/.../process_data.py`
- `data_ingestion/.../ingest_data.py`
- Collection setup script and eval config

All paths are pinned through `references/upstream-lock.yaml`.

## Source Findings

### Managed Is a Control-Plane Trade

The managed recipe has almost no ingestion application code. A GCS data
connector performs parsing, chunking, embedding and indexing.

It still owns substantial platform logic:

- Terraform resources and API enablement;
- connector setup and destroy scripts;
- long-running-operation polling;
- generated data-store/collection discovery;
- sync interval and manual import trigger;
- runtime environment wiring.

Managed does not mean ownership-free. It moves ownership from data-plane code to
connector configuration and service lifecycle.

### Explicit Does Not Mean Local Embeddings

The Vector Search recipe explicitly owns source transformation, chunking,
stable IDs, BigQuery staging and Collection schema. It sends empty vectors;
Vector Search auto-generates embeddings from `text_chunk`.

The meaningful boundary is ingestion/reconciliation ownership, not where the
floating-point embedding is computed.

### Tool Composition Can Change Semantics

`VertexAiSearchTool` is native when used directly. With multiple tools and
`bypass_multi_tools_limit=True`, ADK can replace it with
`DiscoveryEngineSearchTool`.

That changes:

- one provider-native model request into a FunctionTool lifecycle;
- native grounding metadata into an application-parsed result;
- auth/error/latency observability;
- how citations must be retained.

This flag must be treated as an architecture decision.

### Sample Eval Is Not a RAG Gate

Both recipes use identical generic LLM-judge quality and turn-count metrics.
They do not evaluate expected retrieved documents, citations, ACL or lifecycle.
No minimum score is enforced.

## Experiment Design

Lab 05 defines one small Northwind corpus:

- five current documents;
- Atlas specification v1 and v2;
- one internal service bulletin;
- one deleted promotion;
- public and internal principals.

Five baseline cases cover:

- current-version retrieval;
- two-source synthesis;
- authorized internal retrieval;
- public denial/abstention;
- no-hit abstention.

Both architectures use the same deterministic sparse relevance function and
answer composer. This intentionally removes live model variance so the
experiment isolates:

- ADK request/Event shape;
- ownership and provenance;
- ACL filtering;
- version replacement;
- deletion reconciliation;
- citation evaluation.

## Baseline Results

All cases passed the aggregate grounded gate on both paths.

| Metric | Managed | Explicit |
|---|---:|---:|
| Model requests per case | 1 | 2 |
| Yielded Events per case | 1 | 3 |
| Stored Events per case | 2 | 4 |
| Retrieval evidence | grounding metadata | FunctionTool response |
| Five-case grounded pass | 5/5 | 5/5 |

Managed model-visible request text was 200-220 characters. Explicit first
requests were 234-254; second requests were 247-858 depending on hit count.
Provider-side native retrieved context is not represented in the managed
request character count, so these values are not comparable token costs.

## Intentional Breaks

### Missing Principal Filter

Removing the native filter let a public user retrieve an internal service
bulletin and answer with `RST-44`.

Observed:

- access violations: 1;
- answer was fluent and cited;
- aggregate grounded result: false.

### Missing Provenance

The explicit adapter returned chunk text but removed document ID, version and
URI.

Observed:

- answer still contained the correct `80 kg`;
- answer correctness: true;
- citation recall: 0;
- aggregate grounded result: false.

### Stale Incremental Index

The bad ingestion retained Atlas v1 while adding v2.

Observed:

- answer cited current v2 and was correct;
- one stale hit was still model-visible;
- aggregate grounded result: false.

### Deletion Lag

The source snapshot removed `legacy-promotion`, but the bad index did not delete
its object.

Observed:

- retired `ORBIT15` was retrieved and answered;
- deleted hits: 1;
- aggregate grounded result: false.

## Corrections to Initial Thinking

1. **Managed and explicit are not merely two retriever APIs.**
   The larger difference is ingestion and lifecycle ownership.
2. **Correct answer text does not prove a correct RAG system.**
   Three broken runs returned plausible or correct-looking text.
3. **Idempotent create does not imply reconciliation.**
   Stable IDs and `AlreadyExists` handling do not delete obsolete chunks.
4. **Citations are data, not formatting.**
   Source identity must survive retrieval serialization before the model can
   cite it reliably.
5. **Native grounding is not free observability.**
   The application must persist and evaluate grounding metadata.
6. **Local character counts are not cost evidence.**
   Live usage, retrieval latency and monetary cost remain unmeasured.

## Architecture Decisions

- Require versioned source identity in every retrieval result.
- Apply trusted ACL filters before ranking/top-k.
- Evaluate expected document IDs before response quality.
- Fail on stale or deleted hits even if the final answer is current.
- Require citations to be a subset of the exact retrieved evidence.
- Keep managed and explicit adapters behind one normalized evaluation contract,
  not one leaky runtime abstraction.
- Treat ingestion, reconciliation and deletion as separate pipeline stages.
- Record native grounding and FunctionTool trajectories separately.

## Verification

```text
10 dependency-free tests
10 ADK-backed runtime tests
5 baseline query cases x 2 architectures
4 intentional breakages
20,460-byte deterministic trace bundle
```

Two trace renders were byte-identical.

## Limits

- The relevance function is deterministic lexical/vector simulation.
- The provider model and managed backend are scripted.
- No cloud credentials or live indexes were used.
- Provider token counts, latency and monetary cost were not measured.
- Streaming grounding aggregation was not exercised.
- Real connector/Vector Search deletion propagation was not measured.
- Chunking quality was not optimized against a large corpus.

## Roadmap Effect

Phase 6 should turn the Phase 5 metrics into a reusable evaluation system:

- datasets with expected retrieval and trajectory assertions;
- deterministic and judge-based metrics kept separate;
- CI thresholds that fail deliberate breakages;
- latency/cost/safety dimensions;
- comparison and regression reporting.

RAG architecture now has enough evidence to become an evaluation target rather
than another prompt demo.
