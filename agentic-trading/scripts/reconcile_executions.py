#!/usr/bin/env python3
"""Reconcile broker execution state against approved intents or bundles.

This script reads supplied JSON snapshots and local ledgers only. It does not
place, cancel, or retry trades. If reconciliation fails and --kill-switch is
provided, it atomically disables every live control.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from repo_utils import atomic_write_text


REQUIRED_VERSION_FIELDS = [
    "plan_version",
    "risk_policy_version",
    "autonomy_policy_version",
    "scoring_policy_version",
]


def utc_now_compact() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                records.append(json.loads(stripped))
    return records


def find_record(records: list[dict[str, Any]], key: str, value: str | None) -> dict[str, Any] | None:
    if not value:
        return None
    for record in records:
        if record.get(key) == value:
            return record
    return None


def unique_idempotency(records: list[dict[str, Any]], idempotency_key: str | None) -> bool:
    if not idempotency_key:
        return False
    return sum(1 for record in records if record.get("idempotency_key") == idempotency_key) <= 1


def validate_versions(record: dict[str, Any], label: str) -> list[str]:
    return [f"{label} missing {field}" for field in REQUIRED_VERSION_FIELDS if not record.get(field)]


def reconcile(
    execution: dict[str, Any],
    broker_snapshot: dict[str, Any],
    intents: list[dict[str, Any]],
    bundles: list[dict[str, Any]],
    executions: list[dict[str, Any]],
) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_versions(execution, "execution"))

    intent = find_record(intents, "intent_id", execution.get("intent_id"))
    bundle = find_record(bundles, "bundle_id", execution.get("bundle_id"))
    if not intent and not bundle:
        errors.append("intent or bundle did not exist")

    approved_record = intent or bundle or {}
    if approved_record and approved_record.get("status") != "risk_approved":
        errors.append("risk approval did not exist")

    idempotency_key = execution.get("idempotency_key") or approved_record.get("idempotency_key")
    if not unique_idempotency(executions, idempotency_key):
        errors.append("idempotency key was missing or duplicated")

    if execution.get("market_window_valid") is not True:
        errors.append("order was not marked as placed during a valid market window")

    broker_order = broker_snapshot.get("order", {})
    for field in ("symbol", "side"):
        if execution.get(field) != broker_order.get(field):
            errors.append(f"{field} did not match broker order")

    if broker_order.get("fill_status") not in {"filled", "partially_filled", "cancelled"}:
        errors.append("fill status was not verified")

    intended_amount = float(execution.get("dollar_amount", 0) or 0)
    filled_amount = float(broker_order.get("filled_amount", 0) or 0)
    if intended_amount <= 0 or filled_amount < 0 or filled_amount > intended_amount * 1.05:
        errors.append("fill amount was unreasonable")

    expected_price = float(execution.get("expected_price", 0) or 0)
    average_fill_price = float(broker_order.get("average_fill_price", 0) or 0)
    max_slippage_pct = float(execution.get("max_slippage_pct", 1.0) or 1.0)
    if expected_price <= 0 or average_fill_price <= 0:
        errors.append("average fill price could not be checked")
    else:
        slippage_pct = abs(average_fill_price - expected_price) / expected_price * 100
        if slippage_pct > max_slippage_pct:
            errors.append("average fill price exceeded slippage tolerance")

    for flag in (
        "buying_power_updated",
        "position_quantity_updated",
        "portfolio_weights_updated",
        "no_unexpected_new_positions",
        "no_duplicate_orders",
    ):
        if broker_snapshot.get(flag) is not True:
            errors.append(flag.replace("_", " ") + " check failed")

    return errors


def block_trading(kill_switch: Path, reason: str) -> None:
    value = yaml.safe_load(kill_switch.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("kill switch must be a YAML mapping")
    for key in ("trading_enabled", "buying_enabled", "selling_enabled", "live_order_review_enabled"):
        value[key] = False
    value["reason"] = reason
    value["last_updated"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    value["last_updated_by"] = "reconcile_executions.py"
    atomic_write_text(kill_switch, yaml.safe_dump(value, sort_keys=False))


def write_critical_log(log_dir: Path, errors: list[str], execution: dict[str, Any]) -> Path:
    log_dir.mkdir(parents=True, exist_ok=True)
    path = log_dir / f"{utc_now_compact()}-critical-reconciliation-failure.md"
    path.write_text(
        "# Critical Reconciliation Failure\n\n"
        f"Execution: `{execution.get('execution_id', 'unknown')}`\n\n"
        "## Failed Checks\n\n"
        + "\n".join(f"- {error}" for error in errors)
        + "\n\nTrading must remain disabled until reviewed.\n",
        encoding="utf-8",
    )
    return path


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reconcile execution against broker snapshot.")
    parser.add_argument("--execution", type=Path, required=True, help="Execution JSON file.")
    parser.add_argument("--broker-snapshot", type=Path, required=True, help="Broker state JSON file.")
    parser.add_argument("--order-intents", type=Path, default=Path("agentic-trading/orders/order_intents.jsonl"))
    parser.add_argument("--trade-bundles", type=Path, default=Path("agentic-trading/orders/trade_bundles.jsonl"))
    parser.add_argument("--executions", type=Path, default=Path("agentic-trading/orders/executions.jsonl"))
    parser.add_argument("--kill-switch", type=Path, default=Path("agentic-trading/state/kill_switch.yml"))
    parser.add_argument("--log-dir", type=Path, default=Path("agentic-trading/logs"))
    parser.add_argument("--append-to", type=Path, default=Path("agentic-trading/evaluation/reconciliations.jsonl"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    execution = load_json(args.execution)
    broker_snapshot = load_json(args.broker_snapshot)
    errors = reconcile(
        execution,
        broker_snapshot,
        iter_jsonl(args.order_intents),
        iter_jsonl(args.trade_bundles),
        iter_jsonl(args.executions),
    )

    result = {
        "reconciliation_id": f"recon-{utc_now_compact()}",
        "execution_id": execution.get("execution_id"),
        "checked_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": "failed" if errors else "passed",
        "errors": errors,
        "summary": "Reconciliation failed; all live controls were disabled." if errors else "Execution matched the supplied broker snapshot.",
        "evidence_class": "repository_recorded",
        **{field: execution.get(field) for field in REQUIRED_VERSION_FIELDS},
    }

    if errors:
        block_trading(args.kill_switch, "Reconciliation failed: " + "; ".join(errors))
        critical_log = write_critical_log(args.log_dir, errors, execution)
        result["critical_log"] = str(critical_log)
        append_jsonl(args.append_to, result)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 1

    append_jsonl(args.append_to, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
