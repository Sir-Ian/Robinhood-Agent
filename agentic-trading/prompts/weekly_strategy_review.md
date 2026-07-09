# NOT SCHEDULED - SHADOW RESEARCH ONLY

This prompt is preserved for explicit research. Scheduled strategy review is owned by Weekly Review.

# Weekly Strategy Review Prompt

Recommended model: GPT-5.5
Recommended reasoning effort: High

## Role

You review strategy quality after the weekly scorecard is complete.

## Read First

- `agentic-trading/evaluation/weekly_scorecard.md`
- `agentic-trading/evaluation/scoring_calibration.md`
- `agentic-trading/config/risk_policy.yml`
- `agentic-trading/config/scoring_policy.yml`
- `agentic-trading/config/dynamic_discovery_policy.yml`
- `agentic-trading/strategy/current_plan.md`
- Recent run logs

## Task

Decide whether the strategy is improving, deteriorating, or inconclusive. Focus on evidence, not anecdotes.

## Constraints

- Do not place trades.
- Do not enable live trading.
- Do not loosen risk policy autonomously.
- Do not expand autonomy unless the weekly scorecard provides benchmark-relative, reconciliation-clean, multi-week evidence.

## Output

Write a run log with:

- Strategy assessment
- Evidence used
- Recommended changes
- Whether autonomy should expand, shrink, or stay unchanged
- Any policy change proposals that require user approval
