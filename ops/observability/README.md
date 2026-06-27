# Observability

Per-product isolation is a first-class concern: every signal should carry the
`product_slug` (and `org_id` where available) so dashboards, logs, and traces
can be filtered per product.

## Logging

- Structured JSON logs. Always include `product_slug`, `user_id`, `org_id`
  when in a request context (read from `request.state.product_slug`).
- The audit trail (`mynd_shared.product_audit_logs`) is the durable,
  queryable record of significant actions — distinct from app logs.

## Metrics

- Onyx already exposes Prometheus metrics (`setup_prometheus_metrics`). Add a
  `product_slug` label to request metrics via the product-context middleware.
- Track per-product: request rate, latency, chat volume, LLM token usage by
  `llm_credential_scope` (user/org/system).

## Tracing

- Onyx tags every LLM call with an `LLMFlow` (see `core/CLAUDE.md`). Propagate
  `product_slug` as a span attribute so traces are filterable per product.

## What "good" looks like

A single dashboard variable `product_slug` filters logs, metrics, and traces
to one vertical, and the audit table answers "who did what, with whose key."
