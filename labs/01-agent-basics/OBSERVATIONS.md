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

## Pending Runtime Evidence

- ADK `FunctionTool` declarations generated from both signatures.
- Fake-model tool call and full `Event` sequence.
- Session event persistence through `Runner`.
- Live-model selection accuracy for the four README prompts.
- Latency, tokens and cost.

Local environment at creation time has Python 3.10.12 but does not have `uv` or
`google-adk`, so runtime claims remain explicitly unverified.
