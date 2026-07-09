# Experiment Protocol

## Research Question

Can an AI-assisted workflow operate a small public-equity portfolio continuously with high audit quality, low human effort, and controlled risk—while respecting the broker's requirement for explicit confirmation on every live order?

## Separate Hypotheses

### H1: Operational autonomy

Read-only monitoring, paper decisioning, reconciliation, analytics, and reporting can run on schedule with at least a 95% successful-or-valid-no-action rate, no duplicate actions, no leaked private identifiers, and 100% reconciliation of any new fills.

### H2: Decision quality

Any proposed strategy change can be expressed as a falsifiable hypothesis and evaluated against fixed benchmarks without look-ahead bias or changing the comparison after outcomes are known.

### H3: Human-effort reduction

Normal operation requires no daily intervention when no live order is appropriate. When a live order is appropriate, the user receives one compact review request containing the broker-required disclosure and a clear approve/decline decision.

### H4: Investment performance

The portfolio may or may not outperform. Outperformance is not assumed. Performance is measured separately from operational quality.

## Baseline

- Inception orders: June 11, 2026.
- Initial contributed capital: $100.
- Basket: 35% SGOV, 30% VTI, 15% SCHD, 10% XLP, 5% IAU, 5% QQQM.
- Active action: hold and measure.
- External deposits: not allowed without a versioned protocol update.

The baseline weights were reconstructed from broker-confirmed dollar orders. Original local intent/approval records were absent and are explicitly marked as an evidence gap.

## Benchmarks

All comparisons use the same start timestamp, the same cash-flow assumptions, and total-return data when available:

- Cash/no trade.
- The unchanged original basket.
- 100% VTI.
- 70% VTI / 30% SGOV.
- 100% SGOV.

No benchmark-relative claim is valid until every benchmark has complete common-date observations.

## Operating Metrics

- Scheduled runs expected, completed, no-action, blocked, failed, and abandoned.
- Run timeliness and duration.
- Snapshot freshness.
- Reconciliation pass rate and unresolved evidence gaps.
- Duplicate-prevention events.
- Critical incidents and time to safe state.
- Number of live-review requests and explicit confirmations.
- Human interventions per week.
- Public-validation pass rate.

## Investment Metrics

- Time-weighted and money-weighted return when cash-flow data supports them.
- Benchmark-relative return.
- Maximum drawdown, adjusted for cash flows.
- Turnover and order count.
- Spread/slippage and fees.
- Allocation drift.
- Shadow-strategy hit rate and calibration.
- Decision quality by evidence grade, not merely outcome.

## Evidence Classes

- `broker_confirmed`: read-only fact returned by Robinhood.
- `repository_recorded`: durable record created at decision time.
- `computed`: deterministic calculation from cited inputs.
- `paper_simulated`: hypothetical action, never submitted.
- `historical_import`: broker fact imported after the event.
- `unavailable`: evidence that does not exist and must not be reconstructed.

## Promotion Rule

Stage advancement requires at least 20 successful paper sessions, 30 calendar days observed, 100% reconciliation, no critical incidents, no policy violations, passing public validation, no unresolved evidence gaps, and explicit user approval. Meeting the numbers makes the system eligible for review; it does not automatically advance it.

## Limitations

- A $100 account is too small for statistically strong performance conclusions.
- The starting basket was selected before this formal protocol, so selection bias is possible.
- Broker-confirmation requirements prevent fully unattended live execution.
- Public reports omit account identifiers and raw broker payloads, so some private audit detail is intentionally unavailable to readers.
- Short samples and favorable markets can make weak strategies look strong.
