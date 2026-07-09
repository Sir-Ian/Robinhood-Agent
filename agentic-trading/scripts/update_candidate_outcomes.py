#!/usr/bin/env python3
"""Append candidate outcome records from explicit observed prices.

This helper performs no market data lookup and places no trades. A future agent
must supply the observed forward returns or observed prices from approved data
sources.
"""

from __future__ import annotations

import argparse
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def parse_return(value: str | None, reference_price: float) -> float | None:
    if value is None:
        return None
    if value.endswith("%"):
        return float(value[:-1]) / 100.0
    observed_price = float(value)
    return (observed_price - reference_price) / reference_price


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a candidate outcome record.")
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--asset-type", choices=["etf", "stock", "other"], required=True)
    parser.add_argument(
        "--decision-status",
        choices=["promoted_traded", "promoted_shadow", "rejected", "watchlist", "closed"],
        required=True,
    )
    parser.add_argument("--reference-price", type=float, required=True)
    parser.add_argument("--return-1d", help="Return percent like 1.2%% or observed price.")
    parser.add_argument("--return-5d", help="Return percent like 1.2%% or observed price.")
    parser.add_argument("--return-20d", help="Return percent like 1.2%% or observed price.")
    parser.add_argument("--return-60d", help="Return percent like 1.2%% or observed price.")
    parser.add_argument("--outcome-notes", default="")
    parser.add_argument("--plan-version", required=True)
    parser.add_argument("--risk-policy-version", required=True)
    parser.add_argument("--autonomy-policy-version", required=True)
    parser.add_argument("--scoring-policy-version", required=True)
    parser.add_argument("--observed-at")
    parser.add_argument("--outcome-id")
    parser.add_argument("--append-to", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.reference_price <= 0:
        raise SystemExit("--reference-price must be positive")

    record: dict[str, Any] = {
        "outcome_id": args.outcome_id or f"outcome-{uuid.uuid4()}",
        "candidate_id": args.candidate_id,
        "symbol": args.symbol.upper(),
        "asset_type": args.asset_type,
        "decision_status": args.decision_status,
        "reference_price": args.reference_price,
        "observed_at": args.observed_at or utc_now(),
        "return_1d": parse_return(args.return_1d, args.reference_price),
        "return_5d": parse_return(args.return_5d, args.reference_price),
        "return_20d": parse_return(args.return_20d, args.reference_price),
        "return_60d": parse_return(args.return_60d, args.reference_price),
        "outcome_notes": args.outcome_notes,
        "plan_version": args.plan_version,
        "risk_policy_version": args.risk_policy_version,
        "autonomy_policy_version": args.autonomy_policy_version,
        "scoring_policy_version": args.scoring_policy_version,
    }

    if args.append_to:
        append_jsonl(args.append_to, record)
    print(json.dumps(record, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
