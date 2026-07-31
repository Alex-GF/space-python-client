.PHONY: install dev test clean

install:
	uv sync --extra dev

dev: install

test:
	uv run pytest

clean:
	rm -rf .venv
	find . -name "__pycache__" -type d -exec rm -rf {} +
