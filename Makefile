.PHONY: venv install dev test clean

venv:
	python -m venv .venv

install: venv
	. .venv/bin/activate && python -m pip install --upgrade pip && pip install -e ".[dev]"

dev: install

test:
	. .venv/bin/activate && pytest

clean:
	rm -rf .venv
	find . -name "__pycache__" -type d -exec rm -rf {} +
