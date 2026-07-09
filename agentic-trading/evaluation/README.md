# Evaluation Layer

This directory measures two different things:

1. **Operating quality** — scheduled-run completion, freshness, reconciliation, duplicate prevention, incident response, privacy, and required human confirmations.
2. **Investment quality** — return, drawdown, turnover, execution drag, benchmark-relative results, and shadow-strategy calibration.

Do not combine these into one success claim. A profitable portfolio can have broken controls, and reliable controls can operate a weak strategy.

The evaluation layer is read/write state only. It must not call order placement or enable live execution.

## Ledgers

- `benchmark_performance.jsonl`: common-date benchmark observations.
- `reconciliations.jsonl`: passed, failed, and historical-limitation records.
- `shadow_trades.jsonl`: hypothetical actions never submitted to the broker.
- `candidate_outcomes.jsonl`: 1-, 5-, 20-, and 60-session forward outcomes.
- `weekly_scorecard.md`: human-readable operating and investment review.

Missing observations remain null or absent. Never fill a gap with an estimate while labeling it as observed.
