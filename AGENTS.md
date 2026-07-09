# Robinhood Agent Operating Rules

This repository operates a real-money brokerage experiment. Editing files, running validation, collecting read-only broker state, creating paper decisions, and generating reports are allowed. Never place, cancel, or modify an order while performing repository work.

## Active Mode

Mode is `STAGED_AUTONOMY`; active stage is `PAPER`.

The goal is continuous unattended monitoring, paper decisioning, reconciliation, analytics, and documentation. Robinhood requires every live order review to be shown to the user and explicitly confirmed before placement. A scheduled/background task therefore must never place an order.

## Non-Negotiable Rules

- Read `agentic-trading/config/autonomy_policy.yml`, `risk_policy.yml`, `strategy_policy.yml`, and `state/kill_switch.yml` before any broker-related action.
- Only use the broker account explicitly nicknamed `Agentic`; never persist its account number.
- Scheduled tasks may use read-only Robinhood tools. They may create paper intents and prepare a live review request only when policy allows. They may not place orders.
- Live placement requires `HUMAN_APPROVED_LIVE`, all repository flags enabled, a fresh broker review, the complete quote disclosure shown to the user, and explicit confirmation after that review.
- Never treat standing permission, a scheduled task, a policy file, or a prior confirmation as confirmation for a new order.
- Missing, stale, conflicting, or unverifiable data blocks action.
- Never retry a failed or uncertain order automatically.
- No agent may promote its own stage, enable live execution, loosen limits, or expand the live universe.
- Reconciliation uncertainty forces or keeps all live controls disabled.
- Prefer no action over an unlogged or policy-ambiguous action.

## Current Live Universe

- SGOV
- VTI
- SCHD
- XLP
- IAU
- QQQM

Outside-universe research is allowed only as candidate, thesis, score, shadow trade, or proposal records. It cannot become a live intent without explicit policy change by the user.

## Scheduled Roles

| Role | May do | Must not do |
| --- | --- | --- |
| Morning Manager | Read sanitized state and broker data, refresh snapshots, create paper intents, update handoff. | Place orders or create live intents. |
| Order Review | Simulate paper execution; in an authorized live stage, prepare a broker review for the user. | Place, retry, cancel, or silently approve orders. |
| End-of-Day Sync | Reconcile read-only state, update benchmarks and analytics, record incidents. | Place orders or loosen policy. |
| Weekly Review | Evaluate operations, performance, and proposals; regenerate the public report. | Place orders, enable live execution, or promote a strategy. |
| Public Report Publisher | Publish allowlisted sanitized evidence after validation and green CI. | Access the broker, change code/policy, publish non-allowlisted files, or bypass CI. |

## Durable State

Every run—including no-action, skipped, blocked, and failed runs—must append a sanitized record to `agentic-trading/logs/run_records.jsonl`. Every intent, execution, reconciliation, incident, and policy proposal must be written to its repository ledger. Chat memory is never the system of record.

Decision records must include:

- `plan_version`
- `risk_policy_version`
- `autonomy_policy_version`
- `scoring_policy_version`
- source/provenance and as-of time
- idempotency key where applicable

## Public Repository Safety

Never commit account numbers, tokens, cookies, session IDs, raw authorization material, unredacted broker responses, or private log dumps. Public state may include sanitized holdings, amounts, prices, weights, broker-confirmed fill facts, and stable local record IDs. Run `make validate` before staging or publishing.

## Failure Handling

On reconciliation failure, stale critical state, unexpected positions, duplicate orders, or uncertain broker state:

1. Keep or set all live flags to `false`.
2. Append a critical incident and reconciliation record.
3. Update `latest_handoff.md` with the exact uncertainty.
4. Do not attempt a corrective trade.
5. Require a later read-only recheck and explicit human decision.
