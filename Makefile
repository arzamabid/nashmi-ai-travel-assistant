.PHONY: check lint format test

check: lint format-check test

lint:
	ruff check .

format-check:
	ruff format --check .

test:
	pytest
