#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -d ".venv" ]; then
  echo "Virtual environment not found. Run ./build.sh first."
  exit 1
fi

source .venv/bin/activate

if [ $# -eq 0 ]; then
  echo "Usage:"
  echo "  ./start.sh run examples/summarize.yaml              # Run a task"
  echo "  ./start.sh run examples/summarize.yaml -o report.json  # Export JSON"
  echo "  ./start.sh run examples/summarize.yaml --no-ai-scoring # Rules only"
  echo "  ./start.sh models                                    # List models"
  echo ""
  prompt-tuner --help
else
  prompt-tuner "$@"
fi
