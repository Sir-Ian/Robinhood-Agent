#!/usr/bin/env python3
"""Validate swap-aware trade bundle records before risk review or execution.

This is a deterministic structural and policy sanity check. It does not call
Robinhood/MCP and does not approve or place trades.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


MIN_LEG_AMOUNT_USD = 2.0
EXECUTABLE_STATUS = "risk_approved"
REQUIRED_FIELDS = {
    "bundle_id",
    "created_at",
    "created_by",
    "bundle_type",
    "plan_version",
    "risk_policy_version",
    "autonomy_policy_version",
    "scoring_policy_version",
    "account_alias",
    "reason",
    "trigger",
    "sell_legs",
    "buy_legs",
    "funding_source",
    "expected_portfolio_impact",
    "expected_cash_after",
    "risk_checks_claimed",
    "idempotency_key",
    "requires_user_approval",
    "status",
}
SELL_LEG_FIELDS = {"symbol", "dollar_amount", "reason", "min_acceptable_proceeds"}
BUY_LEG_FIELDS = {"symbol", "dollar_amount", "reason", "max_acceptable_price_or_slippage"}


def iter_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                record = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"{path}:{line_number}: invalid JSON: {exc}") from exc
            records.append(record)
    return records


def load_bundle(value: str) -> list[dict[str, Any]]:
    if value == "-":
        return [json.load(sys.stdin)]
    path = Path(value)
    if path.exists():
        if path.suffix == ".jsonl":
            return iter_jsonl(path)
        return [json.loads(path.read_text(encoding="utf-8"))]
    return [json.loads(value)]


def require_fields(record: dict[str, Any], required: set[str], label: str) -> list[str]:
    missing = sorted(required - record.keys())
    return [f"{label} missing field: {field}" for field in missing]


def validate_leg(leg: dict[str, Any], required: set[str], label: str) -> list[str]:
    errors = require_fields(leg, required, label)
    amount = leg.get("dollar_amount")
    if not isinstance(amount, (int, float)) or amount < MIN_LEG_AMOUNT_USD:
        errors.append(f"{label} dollar_amount must be at least {MIN_LEG_AMOUNT_USD:g}")
    symbol = leg.get("symbol")
    if not isinstance(symbol, str) or not symbol:
        errors.append(f"{label} symbol must be a non-empty string")
    return errors


def validate_bundle(bundle: dict[str, Any], require_executable: bool) -> list[str]:
    errors = require_fields(bundle, REQUIRED_FIELDS, "bundle")
    if errors:
        return errors

    if bundle["requires_user_approval"] is not False:
        errors.append("bundle requires user approval and cannot be autonomous")

    if require_executable and bundle["status"] != EXECUTABLE_STATUS:
        errors.append(f"executable bundle status must be {EXECUTABLE_STATUS}")

    if not isinstance(bundle["buy_legs"], list) or not bundle["buy_legs"]:
        errors.append("bundle must include at least one buy leg")
    else:
        for index, leg in enumerate(bundle["buy_legs"], start=1):
            errors.extend(validate_leg(leg, BUY_LEG_FIELDS, f"buy_legs[{index}]"))

    if not isinstance(bundle["sell_legs"], list):
        errors.append("sell_legs must be a list")
    else:
        for index, leg in enumerate(bundle["sell_legs"], start=1):
            errors.extend(validate_leg(leg, SELL_LEG_FIELDS, f"sell_legs[{index}]"))

    risk_checks = bundle["risk_checks_claimed"]
    if not isinstance(risk_checks, list) or not risk_checks:
        errors.append("risk_checks_claimed must be a non-empty list")

    if not isinstance(bundle["idempotency_key"], str) or not bundle["idempotency_key"]:
        errors.append("idempotency_key must be a non-empty string")

    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate trade bundle JSON or JSONL records.")
    parser.add_argument("bundle", help="Bundle JSON object, .json/.jsonl file path, or '-' for stdin.")
    parser.add_argument(
        "--require-executable",
        action="store_true",
        help="Require status risk_approved for executor handoff.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    bundles = load_bundle(args.bundle)
    all_errors: list[str] = []
    for index, bundle in enumerate(bundles, start=1):
        errors = validate_bundle(bundle, args.require_executable)
        all_errors.extend(f"record {index}: {error}" for error in errors)

    if all_errors:
        for error in all_errors:
            print(error, file=sys.stderr)
        return 1

    print(f"validated {len(bundles)} trade bundle(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
