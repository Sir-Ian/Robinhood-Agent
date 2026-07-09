.PHONY: validate test report check clean

validate:
	python3 agentic-trading/scripts/validate_repository.py

test:
	python3 -m unittest discover -s tests -v

report:
	python3 agentic-trading/scripts/generate_report.py

check: validate test report
	git diff --check

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
