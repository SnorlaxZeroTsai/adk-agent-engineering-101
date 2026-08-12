# Lab 05 Observations

Observed with the pinned `google-adk 2.6.3` runtime and scripted models.

## Baseline

All five query cases passed retrieval, answer, citation, ACL, stale-version and
deletion gates on both paths.

| Surface | Managed Search | Explicit vector |
|---|---:|---:|
| Model requests per case | 1 | 2 |
| Yielded trajectory | `grounded_text` | `function_call`, `function_response`, `text` |
| Stored Events per case | 2 | 4 |
| Retrieval location | provider-side model call | local FunctionTool |
| Provenance surface | `Event.grounding_metadata` | structured tool response + answer citation |

The two-source warranty/return case returned both expected document IDs. Public
queries returned no internal source; the unknown-product case abstained without
inventing a citation.

## Request Surface

- Managed request text ranged from 200 to 220 characters in the scripted
  harness.
- Explicit first requests ranged from 234 to 254 characters.
- Explicit second requests ranged from 247 characters for an empty result to
  858 characters for two retrieved sources.

These are deterministic harness character counts, not provider token usage,
latency or monetary cost.

## Intentional Breaks

| Break | Observed failure |
|---|---|
| Native Search without principal filter | Public user received `service-bulletin`; ACL violations = 1 |
| Explicit result without source ID/version/URI | Correct `80 kg` answer; citation recall = 0 |
| Incremental ingestion retained Atlas v1 | Current answer remained correct; stale hits = 1 |
| Source deletion did not delete index object | Retired `ORBIT15` promotion resurfaced; deleted hits = 1 |

Every broken run failed the aggregate grounded gate even when the final answer
looked correct.

## Reproducibility

- 10 dependency-free tests pass.
- 10 ADK-backed runtime tests pass.
- Two evidence renders were byte-identical.
- Evidence bundle size: 20,460 bytes.

## Limits

Search relevance and generation are scripted. Live managed Search, Vector
Search, service latency, real token accounting, monetary cost and deletion
propagation remain credentialed integration gates.
