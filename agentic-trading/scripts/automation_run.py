#!/usr/bin/env python3
"""Acquire run leases, record outcomes, and force the repository safe."""

from __future__ import annotations

import argparse
import json
import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from repo_utils import ROOT, append_jsonl, atomic_write_json, read_json, read_yaml
from validate_repository import validate


RUNTIME = ROOT / ".runtime" / "locks"
ACTIVE_LEASE = RUNTIME / "active.json"
RUN_RECORDS = ROOT / "agentic-trading" / "logs" / "run_records.jsonl"
INCIDENTS = ROOT / "agentic-trading" / "logs" / "incidents.jsonl"
KILL_SWITCH = ROOT / "agentic-trading" / "state" / "kill_switch.yml"


def now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def iso(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def load_lock(path: Path) -> dict[str, Any] | None:
    try:
        return read_json(path)
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        return None


def append_run(lock: dict[str, Any], status: str, summary: str, completed: datetime | None = None) -> None:
    completed = completed or now()
    started = datetime.fromisoformat(lock["started_at"].replace("Z", "+00:00"))
    append_jsonl(
        RUN_RECORDS,
        {
            "run_id": lock["run_id"],
            "automation": lock["automation"],
            "mode": lock["mode"],
            "stage": lock["stage"],
            "started_at": lock["started_at"],
            "completed_at": iso(completed),
            "duration_seconds": max(0, int((completed - started).total_seconds())),
            "status": status,
            "summary": summary,
            "evidence_class": "repository_recorded",
        },
    )


def begin(args: argparse.Namespace) -> int:
    errors = validate(ROOT)
    autonomy = read_yaml(ROOT / "agentic-trading" / "config" / "autonomy_policy.yml")
    matrix = read_yaml(ROOT / "agentic-trading" / "config" / "mvp_automation_matrix.yml")
    if args.automation not in matrix.get("automations", {}):
        raise SystemExit(f"unknown automation: {args.automation}")

    current = now()
    ttl = args.ttl_minutes or int(matrix["automations"][args.automation]["maximum_runtime_minutes"])
    lock = {
        "run_id": f"run-{current.strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}",
        "automation": args.automation,
        "mode": autonomy["mode"],
        "stage": autonomy["active_stage"],
        "started_at": iso(current),
        "expires_at": iso(current + timedelta(minutes=ttl)),
    }
    if errors:
        append_run(lock, "blocked", f"Repository validation failed with {len(errors)} issue(s).", current)
        print(json.dumps({"status": "blocked", "errors": errors, "run_id": lock["run_id"]}, indent=2))
        return 2

    RUNTIME.mkdir(parents=True, exist_ok=True)
    # All scheduled roles write overlapping ledgers and snapshots. A single
    # repository-wide lease prevents cross-role corruption, not merely duplicate
    # instances of the same role.
    path = ACTIVE_LEASE
    existing = load_lock(path)
    if existing:
        expiry = datetime.fromisoformat(existing["expires_at"].replace("Z", "+00:00"))
        if expiry > current:
            print(json.dumps({"status": "blocked", "reason": "active_run_lease", "active_run_id": existing["run_id"]}, indent=2))
            return 2
        append_run(existing, "abandoned", "Run lease expired before completion.", current)
        path.unlink(missing_ok=True)

    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    descriptor = os.open(path, flags, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        json.dump(lock, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps({"status": "started", **lock}, indent=2, sort_keys=True))
    return 0


def finish(args: argparse.Namespace) -> int:
    path = ACTIVE_LEASE
    lock = load_lock(path)
    if not lock:
        raise SystemExit(f"no active lease for {args.automation}")
    if lock.get("run_id") != args.run_id:
        raise SystemExit("run id does not own the active lease")
    append_run(lock, args.status, args.summary)
    path.unlink(missing_ok=True)
    print(json.dumps({"status": "recorded", "run_id": args.run_id, "outcome": args.status}, indent=2))
    return 0


def block(args: argparse.Namespace) -> int:
    import yaml

    kill = read_yaml(KILL_SWITCH)
    for key in ("trading_enabled", "buying_enabled", "selling_enabled", "live_order_review_enabled"):
        kill[key] = False
    kill["reason"] = args.reason
    kill["last_updated"] = iso(now())
    kill["last_updated_by"] = "automation_run.block"
    text = yaml.safe_dump(kill, sort_keys=False)
    KILL_SWITCH.write_text(text, encoding="utf-8")
    incident_id = f"incident-{now().strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:6]}"
    append_jsonl(
        INCIDENTS,
        {
            "incident_id": incident_id,
            "detected_at": iso(now()),
            "severity": "critical",
            "category": "automatic_fail_safe",
            "status": "open",
            "summary": args.reason,
            "evidence_class": "repository_recorded",
        },
    )
    print(json.dumps({"status": "blocked", "incident_id": incident_id}, indent=2))
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    start = sub.add_parser("begin")
    start.add_argument("--automation", required=True)
    start.add_argument("--ttl-minutes", type=int)
    start.set_defaults(func=begin)
    done = sub.add_parser("finish")
    done.add_argument("--automation", required=True)
    done.add_argument("--run-id", required=True)
    done.add_argument("--status", required=True, choices=["succeeded", "no_action", "blocked", "failed"])
    done.add_argument("--summary", required=True)
    done.set_defaults(func=finish)
    fail_safe = sub.add_parser("block")
    fail_safe.add_argument("--reason", required=True)
    fail_safe.set_defaults(func=block)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
