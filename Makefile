.PHONY: test lint fmt

test:
	python -m pytest

lint:
	python -m ruff check .

fmt:
	python -m ruff format .

