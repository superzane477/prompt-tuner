#!/bin/bash
set -e

echo "Building prompt-tuner..."

if ! command -v python3 &> /dev/null; then
  echo "Error: python3 is not installed"
  exit 1
fi

if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv .venv
fi

source .venv/bin/activate

echo "Installing dependencies..."
pip install -e ".[dev]"

echo "Running tests..."
python -m pytest tests/ -v

echo ""
echo "Build successful!"
echo ""
echo "Usage:"
echo "  source .venv/bin/activate"
echo "  prompt-tuner run examples/summarize.yaml"
