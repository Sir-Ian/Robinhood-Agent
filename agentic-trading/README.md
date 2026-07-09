# Agentic Trading System

This directory is the durable operating system for the Robinhood Agent experiment. The current `PAPER` stage allows continuous read-only monitoring, paper decisions, reconciliation, analytics, and public reporting. It does not allow scheduled live order placement.

The six positions already in the account are treated as `baseline_basket_v1`. The portfolio is held and measured while the system proves that it can collect complete state, avoid duplicate actions, reconcile accurately, and publish a trustworthy record.

## Source Of Truth

- `config/autonomy_policy.yml`: stages, permissions, and promotion evidence.
- `config/strategy_policy.yml`: baseline weights and research rules.
- `config/risk_policy.yml`: freshness, order, portfolio, and failure limits.
- `state/kill_switch.yml`: immediate side-specific controls.
- `logs/run_records.jsonl`: one record for every scheduled run.
- `orders/*.jsonl`: intents and executions.
- `evaluation/*.jsonl`: reconciliation, benchmark, and outcome evidence.

## Recurring Flow

1. Morning Manager refreshes sanitized read-only state and may create a paper intent.
2. Order Review simulates paper execution. In a future authorized live stage, it may prepare a broker review for the user but may not place.
3. End-of-Day Sync reconciles broker facts with repository records and updates evaluation state.
4. Weekly Review scores operating quality and regenerates the public experiment report.

Each task must acquire a run lease with `automation_run.py`, record blocked/no-action outcomes, and release its lease on completion.

## Validation

From the repository root:

```bash
make validate
make test
make report
```

No secret or account identifier belongs in this directory. Raw broker payloads belong outside the repository or under the ignored `agentic-trading/private/` path.
