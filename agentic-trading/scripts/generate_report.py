#!/usr/bin/env python3
"""Generate the deterministic public experiment status report."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

from repo_utils import ROOT, atomic_write_json, atomic_write_text, read_json, read_jsonl, read_yaml


STATUS_PATH = ROOT / "docs" / "STATUS.md"
ANALYTICS_PATH = ROOT / "docs" / "analytics" / "latest.json"


def fmt_money(value: float | None) -> str:
    return "Unavailable" if value is None else f"${value:,.2f}"


def load_trades(root: Path) -> list[dict[str, str]]:
    with (root / "agentic-trading" / "ledger" / "trades.csv").open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def build_payload(root: Path = ROOT) -> dict[str, Any]:
    snapshot = read_json(root / "agentic-trading" / "state" / "portfolio_snapshot.json")
    autonomy = read_yaml(root / "agentic-trading" / "config" / "autonomy_policy.yml")
    strategy = read_yaml(root / "agentic-trading" / "config" / "strategy_policy.yml")
    run_records = read_jsonl(root / "agentic-trading" / "logs" / "run_records.jsonl")
    incidents = read_jsonl(root / "agentic-trading" / "logs" / "incidents.jsonl")
    reconciliations = read_jsonl(root / "agentic-trading" / "evaluation" / "reconciliations.jsonl")
    benchmarks = read_jsonl(root / "agentic-trading" / "evaluation" / "benchmark_performance.jsonl")
    trades = load_trades(root)

    statuses: dict[str, int] = {}
    for record in run_records:
        statuses[record["status"]] = statuses.get(record["status"], 0) + 1
    completed = sum(statuses.get(value, 0) for value in ("succeeded", "no_action"))
    denominator = len(run_records)
    operating_rate = completed / denominator if denominator else None
    initial_capital = float(autonomy["account"]["expected_initial_capital_usd"])
    portfolio_value = float(snapshot["portfolio_value_usd"])

    return {
        "as_of": snapshot["updated_at"],
        "mode": autonomy["mode"],
        "stage": autonomy["active_stage"],
        "strategy_id": strategy["strategy_id"],
        "live_execution_enabled": bool(autonomy["live_execution"]["enabled"]),
        "portfolio": {
            "value_usd": portfolio_value,
            "cash_usd": float(snapshot["cash_usd"]),
            "buying_power_usd": float(snapshot["buying_power_usd"]),
            "simple_return_since_initial_capital": portfolio_value / initial_capital - 1,
            "positions": snapshot["positions"],
        },
        "operations": {
            "run_count": denominator,
            "statuses": statuses,
            "successful_or_no_action_rate": operating_rate,
            "incident_count": len(incidents),
            "open_incident_count": sum(1 for item in incidents if item.get("status") == "open"),
            "reconciliation_count": len(reconciliations),
        },
        "trading": {
            "fill_count": len(trades),
            "gross_filled_notional_usd": round(sum(float(row["dollar_amount"]) for row in trades), 2),
            "live_orders_since_audit": 0,
        },
        "benchmark_status": "available" if benchmarks else "insufficient_time_series",
        "limitations": [
            "The simple return uses $100 initial capital and is not yet a cash-flow-audited time-weighted return.",
            "Benchmark-relative performance is unavailable until common-date benchmark observations exist.",
            "The June 11 fills were imported from broker history; original intents and confirmations were not persisted.",
        ],
    }


def render_markdown(payload: dict[str, Any]) -> str:
    portfolio = payload["portfolio"]
    operations = payload["operations"]
    status_rows = "\n".join(
        f"| {key.replace('_', ' ').title()} | {value} |" for key, value in sorted(operations["statuses"].items())
    ) or "| No recorded statuses | 0 |"
    position_rows = "\n".join(
        f"| {position['symbol']} | {position['quantity']:.6f} | {fmt_money(position['market_value_usd'])} | {position['weight_pct']:.2f}% |"
        for position in portfolio["positions"]
    )
    simple_return = portfolio["simple_return_since_initial_capital"] * 100
    success = operations["successful_or_no_action_rate"]
    success_text = "Unavailable" if success is None else f"{success * 100:.1f}%"
    return f"""# Experiment Status

As of: {payload['as_of']}

Mode: `{payload['mode']}`

Stage: `{payload['stage']}`

Strategy: `{payload['strategy_id']}`

## Current Readout

| Metric | Value |
| --- | ---: |
| Portfolio value | {fmt_money(portfolio['value_usd'])} |
| Cash | {fmt_money(portfolio['cash_usd'])} |
| Buying power | {fmt_money(portfolio['buying_power_usd'])} |
| Simple return vs. $100 initial capital | {simple_return:.2f}% |
| Broker-confirmed fills | {payload['trading']['fill_count']} |
| Gross filled notional | {fmt_money(payload['trading']['gross_filled_notional_usd'])} |
| Live orders since July 9 audit | {payload['trading']['live_orders_since_audit']} |
| Live execution enabled | {'Yes' if payload['live_execution_enabled'] else 'No'} |

The simple return is a preliminary account-level figure, not yet a cash-flow-audited time-weighted return.

## Allocation

| Symbol | Quantity | Market value | Weight |
| --- | ---: | ---: | ---: |
{position_rows}

## Operating Evidence

| Run status | Count |
| --- | ---: |
{status_rows}

- Successful-or-valid-no-action rate: {success_text}
- Recorded incidents: {operations['incident_count']} ({operations['open_incident_count']} open)
- Reconciliation records: {operations['reconciliation_count']}
- Benchmark status: `{payload['benchmark_status']}`

## Evidence Limits

""" + "".join(f"- {item}\n" for item in payload["limitations"])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if committed report files are stale.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = build_payload()
    markdown = render_markdown(payload)
    analytics = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.check:
        mismatches: list[str] = []
        if not STATUS_PATH.exists() or STATUS_PATH.read_text(encoding="utf-8") != markdown:
            mismatches.append(str(STATUS_PATH.relative_to(ROOT)))
        if not ANALYTICS_PATH.exists() or ANALYTICS_PATH.read_text(encoding="utf-8") != analytics:
            mismatches.append(str(ANALYTICS_PATH.relative_to(ROOT)))
        if mismatches:
            print("stale generated report files: " + ", ".join(mismatches), file=sys.stderr)
            return 1
        print("generated report files are current")
        return 0
    atomic_write_text(STATUS_PATH, markdown)
    atomic_write_json(ANALYTICS_PATH, payload)
    print(f"wrote {STATUS_PATH.relative_to(ROOT)} and {ANALYTICS_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
