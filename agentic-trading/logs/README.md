# Run And Incident Logs

`run_records.jsonl` contains one sanitized durable record for every scheduled run, including `succeeded`, `no_action`, `blocked`, `failed`, and `abandoned` outcomes.

`incidents.jsonl` contains policy, reconciliation, privacy, and control incidents with their resolution status.

Detailed Markdown notes may be added when they materially aid investigation, but raw broker responses are forbidden. Never log account numbers, broker order identifiers when a local reference is sufficient, tokens, cookies, session IDs, authorization data, or tool response envelopes.
