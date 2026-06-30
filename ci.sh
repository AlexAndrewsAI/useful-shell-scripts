#!/bin/bash
# Local CI script that mirrors the GitHub Actions workflow

set -e

echo "Running ruff..."
uv run ruff check .

echo "Running mypy..."
uv run mypy .

echo "Running pytest..."
uv run pytest

echo "All checks passed!"
