# Order Review And Paper Executor

Despite the compatibility filename, this scheduled task is not an autonomous trade executor. Scheduled tasks may never place orders.

1. Read `AGENTS.md`, active policies, kill switch, handoff, snapshots, intents, executions, and run records.
2. Begin a run lease with `automation_run.py begin --automation order_review`.
3. In `PAPER`, process only unexpired `paper_proposed` intents. Apply risk checks and append a `paper_simulated` execution or a rejection. Never call Robinhood order review or placement.
4. In a future `HUMAN_APPROVED_LIVE` stage, a scheduled task may prepare a candidate for interactive review but must stop before calling placement. The interactive user-facing task must obtain a fresh broker review, show the full required quote disclosure, and receive explicit confirmation after review.
5. Never treat a policy flag, standing instruction, prior approval, or scheduled-task prompt as order confirmation.
6. Never retry a failed or uncertain action. Duplicate idempotency keys are a hard stop.
7. Update handoff and finish the run lease with a sanitized outcome.

No order placement is permitted in this scheduled task under any stage.
