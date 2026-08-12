# Observations

Date: 2026-08-12

## Baseline

Observed with Python 3.10.12:

- project verification and all 13 Lab 01 tests pass;
- contract inspection completes without importing Google ADK;
- known order lookup returns `ok: true` and a copied order record;
- input order IDs are trimmed and normalized to uppercase;
- unknown/empty IDs return stable error codes rather than prose-only failures;
- shipping cost is calculated from a fixed rate table;
- invalid zone, non-positive weight and weight above 50 kg are domain errors;
- Agent AST names both baseline tools and no mutation capability.

## Intentional Breaks

`handle_order_request(query)` collapses extraction, routing and domain behavior.
Its signature cannot require `order_id`, `destination_zone` or `weight_kg`
independently.

`get_order_status_or_raise("Z999")` raises `KeyError`. The corresponding
baseline call returns an inspectable `order_not_found` result.

These observations establish contract-level differences. They do not establish
that one prompt will always select the correct tool.

## Pinned ADK Runtime

Observed with `google-adk 2.6.3` from commit
`a56f6e13ae38296b608808c7a3b37efe4b8c862e`:

- all 8 ADK-backed runtime tests pass;
- `estimate_shipping` exposes required fields, numeric weight and a three-value
  destination enum;
- `ToolContext` is absent from the model-visible schema;
- success persists four events: user, function call, function response and
  final model message;
- the function-response event persists `last_order_id: A100`;
- a second invocation on the same Session sees prior history and state;
- a missing Session raises rather than being silently created;
- unhandled tool and before-agent callback exceptions persist error events and
  then propagate;
- `on_tool_error_callback` can translate an exception into a structured
  function response and allow the model loop to continue.

The first summarizer failed on `content=None` error events. Fixing it reinforced
that Event consumers must branch on event kind before reading message content.

## Pending Evidence

- Live-model selection accuracy for the four README prompts.
- Partial streaming and final-event consolidation.
- Durable session concurrency and process-loss recovery.
- Confirmation, credential, artifact and memory round trips.
- Latency, tokens and cost.

`uv` is not installed locally. The lab-local `.venv` contains the exact pinned
ADK source and does not require cloud credentials for scripted traces.
