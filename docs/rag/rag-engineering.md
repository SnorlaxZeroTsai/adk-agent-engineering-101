# RAG Engineering: Retrieval Ownership and Evidence

Research snapshot: 2026-08-12. Runtime conclusions are pinned to
`google/adk-python@a56f6e1`; recipe conclusions are pinned to
`google/adk-samples@4b5dd77`.

## Question

Managed Search and explicit Vector Search can both return relevant text. The
engineering question is not merely which API retrieves documents:

> Who owns ingestion, document identity, access control, version replacement,
> deletion, provenance and the evidence that proves an answer is grounded?

## Hypothesis

> A RAG architecture is acceptable only when every answer can be traced to an
> authorized, current and non-deleted source version. Final-response quality is
> insufficient evidence without retrieval and citation gates.

## Three Retrieval Surfaces

### Native Vertex AI Search

`VertexAiSearchTool` is a Gemini built-in tool. It does not expose a normal
FunctionTool declaration or execute a local Python search function. During
`process_llm_request` it adds:

```text
GenerateContentConfig.tools[]
  -> Retrieval
     -> VertexAISearch
        -> datastore or engine
        -> filter
        -> max_results
```

The provider performs retrieval inside the model request. The response can
carry `grounding_metadata`, including retrieval queries and retrieved-context
chunks. In Lab 05 this produced one model request and one grounded model Event.

`VertexAiSearchTool._build_vertex_ai_search_config` receives a
`ReadonlyContext`. A subclass can therefore derive a server-side filter from
trusted Session state. The filter is part of the authorization boundary, not a
prompt suggestion.

### Discovery Engine FunctionTool

The pinned runtime has a behavior-changing compatibility path. If an Agent has
multiple tools and `VertexAiSearchTool.bypass_multi_tools_limit=True`,
`LlmAgent` replaces the native tool with `DiscoveryEngineSearchTool`.

That replacement:

- makes an explicit Discovery Engine API call in Python;
- exposes a normal `query` FunctionTool contract;
- returns parsed `title`, `url` and `content`;
- emits FunctionTool call/response Events instead of native grounding alone;
- handles `CHUNKS` and `DOCUMENTS` result modes;
- changes auth, latency, error and citation handling responsibilities.

`bypass_multi_tools_limit` therefore does not merely remove a validation
restriction. It can change the execution and observability model.

### Explicit Vector Retrieval

The `rag-vector-search` recipe does not use an ADK retrieval class. It defines a
normal `retrieve_docs` FunctionTool around
`vectorsearch_v1beta.SearchDataObjectsRequest`.

The recipe owns:

- source extraction;
- HTML-to-Markdown conversion;
- chunk size and overlap;
- deterministic chunk IDs;
- BigQuery incremental and deduplicated staging tables;
- Collection data/vector schema symmetry;
- ingestion retries and `AlreadyExists` behavior;
- fields returned by semantic search;
- result serialization sent back to the model.

Vector Search 2.0 generates embeddings server-side in this recipe. "Explicit
Vector Search" means explicit ingestion and retrieval ownership; it does not
necessarily mean application-side embedding computation.

## Ingestion Ownership

| Concern | Agent Platform Search recipe | Vector Search recipe |
|---|---|---|
| Source handoff | Files uploaded to GCS | Source query transformed by KFP |
| Parsing | Managed connector | Application pipeline |
| Chunking | Managed | `RecursiveCharacterTextSplitter` |
| Chunk identity | Managed | `question_id__<index>` |
| Embedding | Managed | Collection auto-embedding |
| Staging/dedup | Managed service | BigQuery incremental + dedup tables |
| Index schema | Data store schema | Explicit Collection data/vector schema |
| Runtime retrieval | Native built-in Search | FunctionTool calling semantic search |
| Source metadata returned | Provider grounding metadata | Selected output fields |
| Delete path | Connector/collection lifecycle | Application/index lifecycle |

Managed ingestion reduces application code, but it does not remove platform
work. The managed recipe still needs Terraform, connector setup and deletion
scripts, long-running-operation polling, generated data-store discovery and
sync control.

Explicit ingestion increases code and operational ownership. It also makes
chunking, IDs, staging and re-ingestion behavior inspectable and replaceable.

## Source Identity Contract

Every retrievable unit should carry at least:

```text
document_id
document_version
chunk_id
source_uri
visibility / authorization attributes
content
index or embedding version
```

The model does not need every field in prose, but the retrieval and evaluation
layers need stable identity. A formatted string containing only `<Document 0>`
and chunk text cannot prove:

- which document version supported the answer;
- whether the source was authorized;
- whether a cited URI was actually retrieved;
- whether a deleted object remained in the index;
- whether two chunks came from the same source.

The pinned Vector Search recipe asks the service for `question_id`,
`text_chunk` and `full_text_md`, but its formatter sends only `text_chunk` to
the Agent. Lab 05 intentionally reproduces this provenance loss and shows that
an answer can remain correct while citation recall becomes zero.

## Evaluation Contract

Lab 05 holds one versioned corpus and five query cases constant across both
architectures. Every case defines:

- principal role;
- expected document IDs;
- expected answer fragments;
- whether abstention is required.

The gate evaluates independent dimensions.

### Retrieval

- **Recall:** were all expected documents retrieved?
- **Precision:** did retrieval avoid unrelated documents?
- **ACL violations:** did a public principal receive an internal source?
- **Stale hits:** did an obsolete version remain retrievable?
- **Deleted hits:** did a source-deleted document remain in the index?

### Answer and Citation

- Does an answerable case contain the required facts?
- Does an unanswerable case abstain?
- Does each citation identify a source actually returned by retrieval?
- Are all expected supporting documents cited?
- Is the cited version current and non-deleted?

The aggregate `grounded` gate passes only when all applicable checks pass.
This prevents a correct-looking final answer from hiding a retrieval lifecycle
failure.

## Baseline Runtime Evidence

All five cases passed on both paths.

| Surface | Native managed Search | Explicit vector FunctionTool |
|---|---:|---:|
| Model requests per case | 1 | 2 |
| Yielded Events | 1 grounded text | function call, function response, text |
| Stored Events | 2 | 4 |
| Retrieval evidence | `grounding_metadata` | structured tool response |
| Query/result control | provider config | application code |

The explicit second model request includes retrieved content. Its size ranged
from 247 characters for no hits to 858 characters for two sources in the
scripted harness. Managed request text ranged from 200 to 220 characters, but
provider-side retrieved context is not visible in this local request count.

Those character counts are architecture evidence, not a cost comparison.
Live service usage metadata, latency and monetary cost were not measured.

## ACL Break

Baseline native Search derives this filter from trusted principal state:

```text
public   -> visibility = "public"
internal -> visibility IN ("public", "internal")
```

The broken variant uses an unfiltered native tool. A public query for the
Atlas-7 reset code receives the internal `service-bulletin`, returns `RST-44`
and records one ACL violation.

This demonstrates:

- prompt wording is not an authorization mechanism;
- filtering must happen before retrieval results become model-visible;
- a correct citation to an unauthorized source is still a security failure;
- the principal-to-filter mapping must be tested independently of response
  quality.

## Stale-Version Break

The explicit bad ingestion run:

1. indexes Atlas specification v1;
2. indexes v2 without replacing prior version objects;
3. retrieves both versions for the current-payload query.

The final answer still says `80 kg` and cites v2. A response-only evaluator
would pass. The retrieval gate detects one stale hit and fails the run.

The sample's deterministic chunk IDs and `AlreadyExists` skip make repeated
ingestion idempotent only for unchanged IDs. The recipe itself notes that when
chunk count shrinks, old chunks can remain. Idempotent creation is not the same
as version replacement or deletion reconciliation.

## Deletion-Lag Break

The bad explicit index first ingests a promotion document, then removes it from
the source snapshot without deleting its index objects. A later query retrieves
the retired `ORBIT15` promotion.

The answer is fluent, cited and supported by the stale index object. It is
nevertheless wrong with respect to current source lifecycle.

A production delete contract must name:

- source-of-truth deletion signal;
- connector or pipeline reconciliation behavior;
- index-object deletion owner;
- cache invalidation;
- maximum propagation delay;
- audit evidence that the object is no longer retrievable.

## Citation Handling

Native grounding and explicit citations are different evidence surfaces.

For native Search:

- persist `Event.grounding_metadata`;
- preserve retrieved-context URI/title or provider chunk identity;
- map answer spans to grounding chunks when supports are available;
- test streaming aggregation separately.

For explicit retrieval:

- return structured source identity beside text;
- keep the structure through FunctionTool serialization;
- have the answer cite stable source/version IDs;
- verify citations against the exact tool response, not against the entire
  corpus.

Never ask the model to invent URLs or copy source identity from an unrelated
prompt section.

## Sample Eval Gap

Both pinned RAG recipes use the same evaluation configuration:

- an LLM-judged `custom_response_quality` score from 1 to 5;
- an `agent_turn_count` function;
- no enforced minimum score.

Their basic dataset asks a greeting and a generic knowledge-base question. It
does not assert document identity, retrieval relevance, citation fidelity, ACL,
stale versions or deletion.

This is useful as a runnability/demo eval, not a RAG regression gate.

## Decision Guide

Choose managed Agent Platform Search when:

- supported connectors and managed chunking are acceptable;
- reducing ingestion code is more important than custom transforms;
- provider grounding metadata fits the citation requirement;
- connector sync/deletion behavior can meet governance requirements.

Choose explicit Vector Search when:

- parsing and chunking must be domain-specific;
- stable chunk IDs and metadata are first-class requirements;
- ingestion, staging, re-indexing and delete reconciliation need custom policy;
- retrieval output needs application-defined fields or ranking logic.

Use neither architecture until:

- identity and ACL metadata survive ingestion and retrieval;
- the same query dataset evaluates retrieval before generation;
- stale and deleted sources have tested failure paths;
- cost and latency are measured in the intended deployment environment.

## Engineering Checklist

- Version the raw source, parser, chunker, embedding/index schema and eval set.
- Apply authorization filters before top-k truncation.
- Preserve document ID, version, chunk ID and source URI in every hit.
- Separate ingestion success from index reconciliation success.
- Test no-hit behavior and require explicit abstention.
- Evaluate retrieval IDs independently of answer text.
- Verify every citation is present in the current request's retrieved evidence.
- Include stale-version, deletion-lag and cross-principal cases.
- Record model requests, tool Events and native grounding Events separately.
- Measure live retrieval latency, model usage and monetary cost before choosing
  an operational architecture.

## Evidence Classification

**Source fact**

- Native `VertexAiSearchTool` mutates the model request.
- Multi-tool bypass can replace it with `DiscoveryEngineSearchTool`.
- Managed recipe ingestion uses a GCS connector.
- Vector recipe owns KFP chunking/staging and uses server auto-embedding.
- Both recipe evals omit retrieval-specific gates.

**Runtime observation**

- Native baseline used one model request and stored grounding metadata.
- Explicit baseline used two model requests and a FunctionTool round trip.
- All five baseline cases passed the deterministic aggregate gate.
- Each intentional break failed a distinct retrieval/citation invariant.

**Open integration question**

- How do live services compare on relevance, latency and cost for this corpus?
- What are actual connector and Vector Search deletion propagation bounds?
- How stable are provider grounding identities across re-indexing?
- Which metadata filters are supported consistently across data-store schemas?
