# Design Review: Original Agent Framework

Review date: July 9, 2026

## Executive Finding

The original framework had good instincts—small capital, a kill switch, a restricted ETF universe, append-only ledgers, benchmarks, and separation between planning and execution. It was not operationally ready, and its most important claim was wrong: the scheduled executor could not legally or technically operate without a user because the connected Robinhood order-review contract requires the review disclosure to be shown and explicitly confirmed before every placement.

The live audit also contradicted the repository's stated status. Six agentic market orders totaling $100 had filled on June 11, yet the repository still described itself as “setup only” and contained no intents, executions, fills, snapshots, run logs, or reconciliation evidence.

## What Was Directionally Right

- Small capital and a conservative default kill switch.
- A bounded ETF universe with no options, margin, crypto, leverage, or short selling.
- Durable files intended to replace chat memory.
- Benchmark and shadow-trade concepts.
- Explicit reconciliation and fail-closed language.
- Separation of disabled future research prompts from the active schedule.

## Material Problems

### 1. The execution model violated the broker interaction contract

The prompt told a background “trade executor” to review and place orders autonomously. Robinhood's tool contract requires the review output and quote disclosure to be presented to the user and requires explicit confirmation after review. Standing permission is not a substitute. The revised system makes scheduled placement impossible by policy and turns the role into paper execution plus live-review preparation.

### 2. Repository truth and broker truth had diverged

The broker showed six filled agentic orders and a live six-position portfolio. Every local execution ledger was empty. This defeated auditability, idempotency, performance attribution, and incident reconstruction. The revised system backfills only broker-confirmed facts and labels the missing intent/approval trail as unavailable rather than inventing it.

### 3. The “strategy” was an asset list, not a decision rule

The prior files named six ETFs but did not define target weights, rebalance thresholds, timing, expected edge, falsifiers, or the no-trade condition. “Create intents if appropriate” gave an LLM excessive discretion. The revised strategy documents the existing 35/30/15/10/5/5 basket, defaults to `HOLD_AND_MEASURE`, and permits only paper analysis until explicit evidence gates are met.

### 4. One agent could originate and approve its own intents

The Morning Manager was told to create and approve orders. That is not meaningful separation of duties. The revised workflow produces `paper_proposed` intents and requires deterministic checks; no scheduled role can approve or place a live order.

### 5. Risk limits were incomplete or internally inconsistent

There was no precise quote-age limit, intent expiry, daily order count, daily notional cap, experiment capital cap, or account-cash-flow-adjusted drawdown definition. A 15% maximum trade also conflicted with an undocumented 35% SGOV initial allocation. Version 2 makes these constraints explicit and treats any missing input as blocking.

### 6. Evaluation was not reproducible

The benchmark script accepted manually supplied portfolio and benchmark values, so it could faithfully compute differences between invented inputs. The “original ETF basket” had no weights. The revised policy defines every benchmark weight and the report refuses to claim benchmark-relative performance until a common-date price series exists.

### 7. There was no continuous-operation control plane

Natural-language schedules existed only in YAML. There were no actual scheduled tasks, concurrency leases, abandoned-run detection, durable run records, CI, or public-safety checks. The revised repository adds those components and schedules only after local validation passes.

### 8. Public publication was not safe by design

There was no `.gitignore`, license, CI, security policy, privacy boundary, or secret scan. Raw broker responses could easily have entered logs. The revised system separates sanitized public facts from forbidden raw/private data and validates that boundary before publication.

## Investment-Critique Conclusion

The baseline basket is defensible as a conservative learning portfolio, not as a demonstrated alpha strategy. SGOV provides ballast; VTI provides broad beta; SCHD and XLP add overlapping defensive/value exposure; QQQM adds growth concentration; IAU adds a small diversifier. At a $100 scale, fractional trading makes six positions technically feasible, but the tilts add complexity and factor overlap without a documented variant view.

The least destructive response is not to rebalance immediately. It is to preserve the existing basket as a pre-registered baseline, measure it honestly, and test alternative rules in shadow. Operational autonomy and investment alpha are separate hypotheses and must be scored separately.

## Resulting Architecture

- `PAPER` is active; the live portfolio is observed but not automatically changed.
- All scheduled tasks are non-trading.
- A live order can occur only in an interactive task after fresh review and explicit confirmation.
- The broker nickname identifies the intended account; account identifiers are never persisted.
- Every scheduled run records success, no-action, blocked, failed, or abandoned status.
- Stage promotion requires evidence and explicit user approval.
- The public report states missing evidence instead of smoothing it over.
