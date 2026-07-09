#!/usr/bin/env python3
"""Create and validate signal score records for discovery candidates.

This helper does not research securities and does not place trades. It turns
explicit analyst/agent inputs into a JSONL-ready score record and labels whether
the score clears the mechanical scoring thresholds.
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MAX_SCORES = {
    "momentum_score": 20,
    "quality_score": 15,
    "catalyst_score": 20,
    "liquidity_score": 15,
    "portfolio_fit_score": 15,
    "risk_score": 15,
}

PROMOTION_THRESHOLDS = {
    "total_score": 75,
    "liquidity_score": 10,
    "risk_score": 10,
    "portfolio_fit_score": 10,
    "reward_risk_multiple": 2.0,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json_arg(value: str) -> dict[str, Any]:
    if value == "-":
        return json.load(sys.stdin)
    path = Path(value)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return json.loads(value)


def reward_risk_multiple(value: str) -> float:
    try:
        reward, risk = value.split(":", 1)
        risk_float = float(risk)
        if risk_float <= 0:
            raise ValueError
        return float(reward) / risk_float
    except ValueError as exc:
        raise argparse.ArgumentTypeError("reward/risk must look like 2:1") from exc


def require_score_range(name: str, value: int) -> None:
    max_value = MAX_SCORES[name]
    if value < 0 or value > max_value:
        raise SystemExit(f"{name} must be between 0 and {max_value}")


def status_for_score(record: dict[str, Any]) -> str:
    rr_multiple = reward_risk_multiple(record["reward_risk_estimate"])
    if (
        record["total_score"] >= PROMOTION_THRESHOLDS["total_score"]
        and record["liquidity_score"] >= PROMOTION_THRESHOLDS["liquidity_score"]
        and record["risk_score"] >= PROMOTION_THRESHOLDS["risk_score"]
        and record["portfolio_fit_score"] >= PROMOTION_THRESHOLDS["portfolio_fit_score"]
        and rr_multiple >= PROMOTION_THRESHOLDS["reward_risk_multiple"]
    ):
        return "promotion_eligible"
    return "scored"


def build_record(args: argparse.Namespace, candidate: dict[str, Any]) -> dict[str, Any]:
    score_values = {
        "momentum_score": args.momentum_score,
        "quality_score": args.quality_score,
        "catalyst_score": args.catalyst_score,
        "liquidity_score": args.liquidity_score,
        "risk_score": args.risk_score,
        "portfolio_fit_score": args.portfolio_fit_score,
    }
    for name, value in score_values.items():
        require_score_range(name, value)

    total_score = sum(score_values.values())
    record: dict[str, Any] = {
        "score_id": args.score_id or f"score-{uuid.uuid4()}",
        "candidate_id": candidate["candidate_id"],
        "symbol": candidate["symbol"],
        "scored_at": args.scored_at or utc_now(),
        "scored_by": args.scored_by,
        "model": args.model,
        "reasoning_effort": args.reasoning_effort,
        **score_values,
        "total_score": total_score,
        "reward_risk_estimate": args.reward_risk_estimate,
        "confidence": args.confidence,
        "evidence_summary": args.evidence_summary,
        "data_sources": args.data_sources,
        "status": "scored",
        "plan_version": args.plan_version,
        "risk_policy_version": args.risk_policy_version,
        "autonomy_policy_version": args.autonomy_policy_version,
        "scoring_policy_version": args.scoring_policy_version,
    }
    record["status"] = status_for_score(record)
    return record


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a discovery signal score record.")
    parser.add_argument("--candidate", required=True, help="Candidate JSON object, file path, or '-' for stdin.")
    parser.add_argument("--scored-by", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--reasoning-effort", choices=["Low", "Medium", "High"], required=True)
    parser.add_argument("--momentum-score", type=int, required=True)
    parser.add_argument("--quality-score", type=int, required=True)
    parser.add_argument("--catalyst-score", type=int, required=True)
    parser.add_argument("--liquidity-score", type=int, required=True)
    parser.add_argument("--risk-score", type=int, required=True)
    parser.add_argument("--portfolio-fit-score", type=int, required=True)
    parser.add_argument("--reward-risk-estimate", required=True, type=str)
    parser.add_argument("--confidence", choices=["low", "medium", "high"], required=True)
    parser.add_argument("--evidence-summary", required=True)
    parser.add_argument("--data-source", action="append", dest="data_sources", required=True)
    parser.add_argument("--plan-version", required=True)
    parser.add_argument("--risk-policy-version", required=True)
    parser.add_argument("--autonomy-policy-version", required=True)
    parser.add_argument("--scoring-policy-version", required=True)
    parser.add_argument("--score-id")
    parser.add_argument("--scored-at")
    parser.add_argument("--append-to", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    reward_risk_multiple(args.reward_risk_estimate)
    candidate = load_json_arg(args.candidate)
    for field in ("candidate_id", "symbol"):
        if field not in candidate:
            raise SystemExit(f"candidate is missing required field: {field}")

    record = build_record(args, candidate)
    if args.append_to:
        append_jsonl(args.append_to, record)
    print(json.dumps(record, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
