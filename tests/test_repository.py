from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "agentic-trading" / "scripts"
sys.path.insert(0, str(SCRIPTS))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validate_repository = load_module("validate_repository_test", SCRIPTS / "validate_repository.py")
generate_report = load_module("generate_report_test", SCRIPTS / "generate_report.py")


class RepositoryValidationTests(unittest.TestCase):
    def test_repository_is_internally_consistent(self) -> None:
        self.assertEqual(validate_repository.validate(ROOT), [])

    def test_sensitive_key_assignment_is_rejected(self) -> None:
        sensitive = '{"account_' + 'number": "forbidden"}'
        errors = validate_repository.scan_sensitive_text(Path("state.json"), sensitive)
        self.assertTrue(errors)

    def test_documentation_phrase_is_not_a_false_positive(self) -> None:
        errors = validate_repository.scan_sensitive_text(Path("README.md"), "Never persist an account number.")
        self.assertEqual(errors, [])


class ReportTests(unittest.TestCase):
    def test_payload_uses_sanitized_baseline(self) -> None:
        payload = generate_report.build_payload(ROOT)
        self.assertEqual(payload["stage"], "PAPER")
        self.assertFalse(payload["live_execution_enabled"])
        self.assertEqual(payload["trading"]["fill_count"], 6)
        self.assertEqual(payload["trading"]["gross_filled_notional_usd"], 100.0)

    def test_render_is_deterministic(self) -> None:
        payload = generate_report.build_payload(ROOT)
        first = generate_report.render_markdown(payload)
        second = generate_report.render_markdown(json.loads(json.dumps(payload)))
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
