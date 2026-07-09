#!/usr/bin/env python3
"""Create benchmark comparison records from supplied values.

This helper does not fetch prices. It computes relative performance from
explicit portfolio and benchmark values supplied by an evaluation agent.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


BENCHMARKS = [
    "cash_no_trade",
    "original_etf_basket",
    "vti_100",
    "vti_70_sgov_30",
    "sgov_100",
]


def append_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create benchmark performance records.")
    parser.add_argument("--date", required=True, help="YYYY-MM-DD")
    parser.add_argument("--portfolio-value", type=float, required=True)
    parser.add_argument("--max-drawdown", type=float, required=True)
    parser.add_argument("--notes", default="")
    for benchmark in BENCHMARKS:
        parser.add_argument(f"--{benchmark.replace('_', '-')}", type=float, required=True)
    parser.add_argument("--append-to", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.portfolio_value < 0:
        raise SystemExit("--portfolio-value must be non-negative")

    records: list[dict[str, Any]] = []
    for benchmark in BENCHMARKS:
        value = getattr(args, benchmark)
        if value < 0:
            raise SystemExit(f"--{benchmark.replace('_', '-')} must be non-negative")
        records.append(
            {
                "date": args.date,
                "portfolio_value": args.portfolio_value,
                "benchmark_name": benchmark,
                "benchmark_value": value,
                "relative_performance": args.portfolio_value - value,
                "max_drawdown": args.max_drawdown,
                "notes": args.notes,
            }
        )

    if args.append_to:
        append_jsonl(args.append_to, records)
    print(json.dumps(records, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
