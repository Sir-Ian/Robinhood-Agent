# Operations Runbook

## Schedules

All times are America/Chicago and market-day aware.

| Task | Schedule | Normal outcome |
| --- | --- | --- |
| Morning Manager | Weekdays 07:50 | Fresh sanitized snapshot and no-action/paper intent |
| Order Review | Weekdays 08:45 | Paper simulation or blocked/no-action |
| End-of-Day Sync | Weekdays 15:15 | Reconciliation, benchmark inputs, report refresh |
| Weekly Review | Friday 15:45 | Operating scorecard and strategy proposals |

The schedules intentionally do not place orders. On holidays, tasks should record `no_action` with `market_closed` rather than fail.

## Run Lifecycle

```bash
python3 agentic-trading/scripts/automation_run.py begin --automation morning_manager
python3 agentic-trading/scripts/automation_run.py finish \
  --automation morning_manager \
  --run-id RUN_ID \
  --status no_action \
  --summary "Market closed; snapshots refreshed."
```

`begin` validates the repository and acquires an expiring lease under the ignored `.runtime/` directory. A concurrent run is blocked. An expired lease is recorded as abandoned before a new lease starts.

## Normal Daily Checks

- Correct account is selected by nickname, never by a persisted number.
- Account, buying power, positions, quotes, and tradability are fresh.
- Broker orders match local execution records.
- All live flags remain false in `PAPER`.
- No unexpected symbols or asset classes are present.
- Every result is recorded, including no action.

## Live Review Procedure

Live review is unavailable in the active stage. If a later user-approved policy changes the stage:

1. Run the task interactively, never as a schedule.
2. Re-read policies and acquire current account/position/quote state.
3. Verify the unexpired intent and idempotency key.
4. Call Robinhood order review.
5. Show the user the complete broker-required quote disclosure and any alert.
6. Ask for explicit approval of that exact reviewed order.
7. Place only after approval; a changed order requires a new review and confirmation.
8. Reconcile immediately. Never retry uncertainty.

## Incident Response

For an unexpected position, unknown order, duplicate idempotency key, stale state, or reconciliation mismatch:

```bash
python3 agentic-trading/scripts/automation_run.py block \
  --reason "Concise sanitized reason"
```

This command disables all live controls and appends an incident. The agent must update the handoff, stop, and wait for a later read-only investigation. It must not place a “corrective” order.

## Publication

Run:

```bash
make check
git status --short
```

Inspect every staged file. Do not publish raw broker payloads, private logs, account identifiers, authentication material, or a report that claims unavailable benchmark evidence.
