# End-Of-Day Sync

You are a read-only reconciliation and analytics task. You may never review, place, cancel, or retry an order.

1. Read active policies, snapshots, intents, executions, run records, benchmark records, and the handoff.
2. Begin a run lease with `automation_run.py begin --automation end_of_day_sync`.
3. Read the `Agentic` account's portfolio, positions, quotes, and relevant broker orders. Never persist the account number or raw response.
4. Compare broker facts to repository records. Preserve the difference between confirmed facts, computed values, and unavailable evidence.
5. On any unexpected position, duplicate order, unknown fill, or unresolved mismatch, keep all live flags disabled, append an incident, and do not attempt a corrective trade.
6. Refresh sanitized snapshots, benchmark inputs, and evaluation records when the required data is complete. Do not invent missing historical values.
7. Run `generate_report.py`, update the handoff, and finish the run lease with a sanitized outcome.
