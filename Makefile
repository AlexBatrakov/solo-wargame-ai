.DEFAULT_GOAL := help

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(PYTHON) -m pip
DEV_STAMP := $(VENV)/.dev-installed

.PHONY: help bootstrap test lint fmt clean-venv

help:
	@printf "%s\n" \
		"Available targets:" \
		"  help        Show this help message" \
		"  bootstrap   Create/update .venv and install dev dependencies" \
		"  test        Run the test suite via the project .venv" \
		"  lint        Run ruff checks via the project .venv" \
		"  fmt         Format the repository with ruff via the project .venv" \
		"  clean-venv  Remove the local virtual environment"

bootstrap: $(DEV_STAMP)

$(DEV_STAMP): pyproject.toml
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"
	touch $(DEV_STAMP)

test: $(DEV_STAMP)
	$(PYTHON) -m pytest

lint: $(DEV_STAMP)
	$(PYTHON) -m ruff check .

fmt: $(DEV_STAMP)
	$(PYTHON) -m ruff format .

clean-venv:
	rm -rf $(VENV)
