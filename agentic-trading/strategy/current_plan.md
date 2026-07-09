# Current Plan

Plan version: 2
Mode: `STAGED_AUTONOMY`
Stage: `PAPER`

## Objective

Operate the existing $100-scale ETF account as a transparent experiment. Automate state collection, paper decisioning, reconciliation, analytics, and reporting. Minimize human involvement to the one action the broker contract requires: explicit confirmation after each live order review.

## Current Decision

`HOLD_AND_MEASURE`

The existing June 11 allocation is the baseline basket: 35% SGOV, 30% VTI, 15% SCHD, 10% XLP, 5% IAU, and 5% QQQM. No live rebalancing is authorized. Quarterly and 5-percentage-point drift checks are paper analyses only.

## Why This Is The Current Decision

- The allocation already exists, so changing it now would contaminate the baseline and add turnover without a tested edge.
- The prior design did not define a reproducible strategy or preserve its executed orders in the repository.
- Operational integrity must be proven before adaptive investing can be evaluated honestly.
- The basket is diversified enough to serve as a baseline, but its tilts are hypotheses—not established alpha.

## What Would Change The Decision

- A policy or risk breach: tighten controls and remain paper-only.
- A 5% account drawdown: block new live reviews and re-underwrite.
- A 10% drawdown or reconciliation uncertainty: hard stop.
- At least 20 successful paper sessions, 30 calendar days of observation, perfect reconciliation, no critical incidents, and no unresolved evidence gaps: eligible for a user decision on advancing stages.
- A strategy proposal with observable falsifiers, shadow evidence, turnover analysis, and benchmark/factor comparison: eligible for review, not automatic adoption.
