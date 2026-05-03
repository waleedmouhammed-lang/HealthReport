#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="$PROJECT_DIR/.venv/bin/python"

if [[ -x "$PROJECT_DIR/.venv/bin/python3" ]]; then
  PYTHON_BIN="$PROJECT_DIR/.venv/bin/python3"
elif [[ -x "$PROJECT_DIR/.venv-macbook/bin/python3" ]]; then
  PYTHON_BIN="$PROJECT_DIR/.venv-macbook/bin/python3"
elif [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="$(command -v python3)"
fi

mkdir -p "$PROJECT_DIR/logs"
cd "$PROJECT_DIR"
"$PYTHON_BIN" "$PROJECT_DIR/main.py"
