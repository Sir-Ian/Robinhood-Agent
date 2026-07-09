#!/usr/bin/env python3
"""Validate policy consistency, record integrity, and public-repo safety."""

from __future__ import annotations

import csv
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

from repo_utils import ROOT, iter_public_files, read_json, read_jsonl, read_yaml


VERSION_FIELDS = (
    "plan_version",
    "risk_policy_version",
    "autonomy_policy_version",
    "scoring_policy_version",
)

DATA_SCHEMA_MAP = {
    "agentic-trading/discovery/candidate_pool.jsonl": "candidate.schema.json",
    "agentic-trading/discovery/signal_scores.jsonl": "signal_score.schema.json",
    "agentic-trading/evaluation/candidate_outcomes.jsonl": "candidate_outcome.schema.json",
    "agentic-trading/evaluation/shadow_trades.jsonl": "shadow_trade.schema.json",
    "agentic-trading/evaluation/benchmark_performance.jsonl": "benchmark_performance.schema.json",
    "agentic-trading/orders/trade_bundles.jsonl": "trade_bundle.schema.json",
    "agentic-trading/orders/order_intents.jsonl": "order_intent.schema.json",
    "agentic-trading/orders/executions.jsonl": "execution.schema.json",
    "agentic-trading/logs/run_records.jsonl": "run_record.schema.json",
    "agentic-trading/evaluation/reconciliations.jsonl": "reconciliation.schema.json",
}

SENSITIVE_KEY_RE = re.compile(
    r"(?i)(?:\"|')?(?:account_number|rhs_account_number|rhc_account_number|access_token|refresh_token|session_id|authorization|cookie|password)(?:\"|')?\s*[:=]"
)
TOKEN_RE = re.compile(r"(?:sk-(?:proj-)?[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9-]{10,})")
RAW_RESPONSE_RE = re.compile(r'\"(?:structuredContent|guide)\"\s*:')


def scan_sensitive_text(path: Path, text: str) -> list[str]:
    errors: list[str] = []
    if path.name == "validate_repository.py":
        return errors
    for label, pattern in (
        ("sensitive key assignment", SENSITIVE_KEY_RE),
        ("credential-like token", TOKEN_RE),
        ("raw connector response marker", RAW_RESPONSE_RE),
    ):
        match = pattern.search(text)
        if match:
            line = text.count("\n", 0, match.start()) + 1
            errors.append(f"{path}:{line}: {label} is not allowed in public files")
    return errors


def _type_matches(value: Any, expected: str) -> bool:
    return {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
        "null": value is None,
    }.get(expected, True)


def _resolve_ref(schema_root: dict[str, Any], reference: str) -> dict[str, Any]:
    if not reference.startswith("#/"):
        raise ValueError(f"unsupported schema reference: {reference}")
    value: Any = schema_root
    for part in reference[2:].split("/"):
        value = value[part.replace("~1", "/").replace("~0", "~")]
    if not isinstance(value, dict):
        raise ValueError(f"schema reference is not an object: {reference}")
    return value


def _validate_value(value: Any, schema: dict[str, Any], root: dict[str, Any], location: str) -> list[str]:
    errors: list[str] = []
    if "$ref" in schema:
        return _validate_value(value, _resolve_ref(root, schema["$ref"]), root, location)
    expected = schema.get("type")
    if expected:
        expected_types = expected if isinstance(expected, list) else [expected]
        if not any(_type_matches(value, item) for item in expected_types):
            return [f"{location}: expected type {expected!r}"]
    if "const" in schema and value != schema["const"]:
        errors.append(f"{location}: expected constant {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{location}: {value!r} is not an allowed value")
    if isinstance(value, dict):
        for field in schema.get("required", []):
            if field not in value:
                errors.append(f"{location}: missing required field {field}")
        for field, child_schema in schema.get("properties", {}).items():
            if field in value:
                errors.extend(_validate_value(value[field], child_schema, root, f"{location}.{field}"))
    if isinstance(value, list):
        if len(value) < int(schema.get("minItems", 0)):
            errors.append(f"{location}: requires at least {schema['minItems']} items")
        if "items" in schema:
            for index, item in enumerate(value):
                errors.extend(_validate_value(item, schema["items"], root, f"{location}[{index}]"))
    if isinstance(value, str):
        if len(value) < int(schema.get("minLength", 0)):
            errors.append(f"{location}: string is shorter than {schema['minLength']}")
        if "pattern" in schema and not re.search(schema["pattern"], value):
            errors.append(f"{location}: value does not match required pattern")
        try:
            if schema.get("format") == "date-time":
                datetime.fromisoformat(value.replace("Z", "+00:00"))
            elif schema.get("format") == "date":
                date.fromisoformat(value)
        except ValueError:
            errors.append(f"{location}: invalid {schema['format']} value")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{location}: must be at least {schema['minimum']}")
        if "exclusiveMinimum" in schema and value <= schema["exclusiveMinimum"]:
            errors.append(f"{location}: must be greater than {schema['exclusiveMinimum']}")
    return errors


def validate_schema(root: Path, data_path: str, schema_name: str) -> list[str]:
    errors: list[str] = []
    schema_path = root / "agentic-trading" / "schemas" / schema_name
    schema = read_json(schema_path)
    for index, record in enumerate(read_jsonl(root / data_path), start=1):
        for issue in _validate_value(record, schema, schema, "record"):
            errors.append(f"{data_path}:{index}:{issue}")
    return errors


def validate(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    config_dir = root / "agentic-trading" / "config"
    configs: dict[str, dict[str, Any]] = {}
    for path in sorted(config_dir.glob("*.yml")):
        try:
            configs[path.name] = read_yaml(path)
        except Exception as exc:  # noqa: BLE001 - validation must aggregate failures
            errors.append(str(exc))

    required_configs = {
        "autonomy_policy.yml",
        "risk_policy.yml",
        "strategy_policy.yml",
        "mvp_automation_matrix.yml",
    }
    missing = required_configs - configs.keys()
    errors.extend(f"missing config: {name}" for name in sorted(missing))
    if missing:
        return errors

    autonomy = configs["autonomy_policy.yml"]
    risk = configs["risk_policy.yml"]
    strategy = configs["strategy_policy.yml"]
    matrix = configs["mvp_automation_matrix.yml"]
    kill = read_yaml(root / "agentic-trading" / "state" / "kill_switch.yml")

    for label, value in (
        ("autonomy", autonomy.get("mode")),
        ("risk", risk.get("mode")),
        ("strategy", strategy.get("mode")),
        ("schedule", matrix.get("mode")),
        ("kill switch", kill.get("mode")),
    ):
        if value != "STAGED_AUTONOMY":
            errors.append(f"{label} mode must be STAGED_AUTONOMY, got {value!r}")

    stage = autonomy.get("active_stage")
    if stage not in autonomy.get("stages", {}):
        errors.append(f"active stage {stage!r} is not defined")
    if matrix.get("active_stage") != stage or kill.get("active_stage") != stage:
        errors.append("active stage is inconsistent across autonomy, schedule, and kill switch")

    if stage != "HUMAN_APPROVED_LIVE":
        if autonomy.get("live_execution", {}).get("enabled") is not False:
            errors.append("live execution must be false outside HUMAN_APPROVED_LIVE")
        for key in ("trading_enabled", "buying_enabled", "selling_enabled", "live_order_review_enabled"):
            if kill.get(key) is not False:
                errors.append(f"{key} must be false in {stage}")

    automations = matrix.get("automations", {})
    expected_automations = {
        "morning_manager",
        "order_review",
        "end_of_day_sync",
        "weekly_review",
        "public_report_publisher",
    }
    if set(automations) != expected_automations:
        errors.append(f"scheduled automation set must be {sorted(expected_automations)}")
    for name, settings in automations.items():
        if settings.get("may_place_orders") is not False:
            errors.append(f"scheduled automation {name} must not place orders")

    allowed = set(autonomy.get("live_trading_scope", {}).get("allowed_symbols", []))
    core = set(risk.get("core_universe", []))
    weights = strategy.get("target_weights_pct", {})
    if allowed != core or allowed != set(weights):
        errors.append("allowed symbols, risk core universe, and strategy weights must match")
    if abs(sum(float(value) for value in weights.values()) - 100.0) > 1e-9:
        errors.append("strategy target weights must sum to 100")

    json_paths = list((root / "agentic-trading").rglob("*.json"))
    for path in json_paths:
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{path.relative_to(root)}: invalid JSON: {exc}")

    for path in sorted((root / "agentic-trading").rglob("*.jsonl")):
        try:
            read_jsonl(path)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{path.relative_to(root)}: invalid JSONL: {exc}")

    for data_path, schema_name in DATA_SCHEMA_MAP.items():
        try:
            errors.extend(validate_schema(root, data_path, schema_name))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{data_path}: schema validation failed to run: {exc}")

    for data_path in (
        "agentic-trading/orders/order_intents.jsonl",
        "agentic-trading/orders/executions.jsonl",
        "agentic-trading/orders/trade_bundles.jsonl",
        "agentic-trading/evaluation/reconciliations.jsonl",
    ):
        for index, record in enumerate(read_jsonl(root / data_path), start=1):
            for field in VERSION_FIELDS:
                if not record.get(field):
                    errors.append(f"{data_path}:{index}: missing {field}")

    for data_path in ("agentic-trading/orders/order_intents.jsonl", "agentic-trading/orders/executions.jsonl"):
        seen: set[str] = set()
        for index, record in enumerate(read_jsonl(root / data_path), start=1):
            key = record.get("idempotency_key")
            if key and key in seen:
                errors.append(f"{data_path}:{index}: duplicate idempotency_key {key}")
            if key:
                seen.add(key)
            if record.get("symbol") and record["symbol"] not in allowed:
                errors.append(f"{data_path}:{index}: live/order symbol {record['symbol']} is outside allowed universe")

    trades_path = root / "agentic-trading" / "ledger" / "trades.csv"
    try:
        with trades_path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        if rows and not {"timestamp", "symbol", "side", "dollar_amount", "public_execution_id"}.issubset(rows[0]):
            errors.append("trades.csv is missing required columns")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"trades.csv: {exc}")

    for path in iter_public_files(root):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        errors.extend(scan_sensitive_text(path.relative_to(root), text))

    snapshot = read_json(root / "agentic-trading" / "state" / "portfolio_snapshot.json")
    if snapshot.get("account_alias") != autonomy.get("account", {}).get("alias"):
        errors.append("portfolio snapshot account alias does not match autonomy policy")

    return errors


def main() -> int:
    errors = validate()
    if errors:
        print(f"repository validation failed with {len(errors)} issue(s):", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("repository validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
