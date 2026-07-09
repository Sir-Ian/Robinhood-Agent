# Robinhood Agent

An open, auditable experiment in operating a small brokerage account with an AI-assisted workflow.

The repository is designed to answer a practical question: **how much of investment operations can run continuously and safely when an AI agent prepares decisions, while the broker still requires a human to approve each live order?**

The current account began with approximately $100. It holds a six-ETF baseline portfolio and is now in the `PAPER` stage of a staged-autonomy program. Monitoring, paper decisions, reconciliation, analytics, and experiment reporting may run unattended. Live order placement is disabled in repository policy and requires a fresh Robinhood order review plus explicit user confirmation.

> This is an educational experiment, not investment advice. It may lose money. Do not copy its allocations or decisions without doing your own research.

## Current Status

| Area | Status |
| --- | --- |
| Broker connectivity | Read-only connection verified July 9, 2026 |
| Existing portfolio | Six ETF positions; sanitized snapshot checked in |
| Unattended monitoring | Ready to schedule |
| Paper decisions | Enabled |
| Live order placement | Disabled; per-order human confirmation required |
| Public-repo safety | Automated validation and secret-pattern scan included |
| Historical audit trail | June 11 fills backfilled from broker data; missing original intents documented as an evidence gap |

## Operating Model

```text
Robinhood read-only data
        |
        v
snapshot -> deterministic policy checks -> paper intent / live review request
        |                                      |
        v                                      v
reconciliation -> analytics -> public report   human confirmation required
```

The active mode is `STAGED_AUTONOMY`:

1. `OBSERVE` — read-only connectivity and state validation.
2. `PAPER` — unattended paper intents and simulated execution; current stage.
3. `HUMAN_APPROVED_LIVE` — every order still requires a fresh broker review and explicit confirmation.
4. `ADAPTIVE_RESEARCH` — broader ideas remain shadow-only until evidence and explicit policy approval justify promotion.

Stage advancement is evidence-based. An agent cannot promote itself, enable live trading, or loosen risk limits.

## Baseline Portfolio

The June 11, 2026 portfolio was initialized as:

| Symbol | Target | Role |
| --- | ---: | --- |
| SGOV | 35% | Treasury-bill ballast |
| VTI | 30% | Broad U.S. equity core |
| SCHD | 15% | Dividend/quality tilt |
| XLP | 10% | Defensive equity tilt |
| IAU | 5% | Gold diversifier |
| QQQM | 5% | Growth tilt |

This basket is a documented baseline, not a proven source of alpha. The experiment measures it against cash, 100% VTI, 70% VTI / 30% SGOV, 100% SGOV, and the unchanged original basket. Candidate strategy changes are tested in shadow before they can affect live policy.

## Repository Map

- [`agentic-trading/config`](agentic-trading/config): operating, strategy, risk, scoring, and schedule policies.
- [`agentic-trading/prompts`](agentic-trading/prompts): bounded instructions for recurring Codex tasks.
- [`agentic-trading/state`](agentic-trading/state): sanitized shared state and fail-safe controls.
- [`agentic-trading/orders`](agentic-trading/orders): append-only intent and execution records.
- [`agentic-trading/evaluation`](agentic-trading/evaluation): benchmark, reconciliation, and outcome records.
- [`agentic-trading/scripts`](agentic-trading/scripts): deterministic validation, run control, reporting, and reconciliation tools.
- [`docs/EXPERIMENT.md`](docs/EXPERIMENT.md): research questions, hypotheses, and evaluation plan.
- [`docs/OPERATIONS.md`](docs/OPERATIONS.md): runbook, schedules, incident response, and stage gates.
- [`docs/DESIGN_REVIEW.md`](docs/DESIGN_REVIEW.md): critique of the original agent design and the resulting changes.
- [`docs/PRIVACY.md`](docs/PRIVACY.md): what may and may not be published.

## Local Validation

Python 3.11+ is recommended.

```bash
python3 -m pip install -r requirements-dev.txt
make validate
make test
make report
```

`make validate` checks policy consistency, JSON/JSONL validity, record versions, symbol restrictions, duplicate idempotency keys, public-repo secret patterns, and the live-execution fail-safe.

## Safety Invariants

- No scheduled task may place an order.
- No live order may be placed without a fresh Robinhood review and explicit user confirmation.
- Account numbers, tokens, session IDs, cookies, and raw broker responses must never be committed.
- Missing or stale data blocks action; it is not silently replaced with a guess.
- Every run gets a durable run record, including no-action and failed runs.
- Reconciliation uncertainty keeps or forces trading disabled.
- Strategy changes are proposals until explicitly approved in policy.

## License

MIT. See [`LICENSE`](LICENSE).
