#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STREAMLIT_BIN="$PROJECT_DIR/.venv/bin/streamlit"
DASHBOARD_PORT="${DASHBOARD_PORT:-8501}"

if [[ -x "$PROJECT_DIR/.venv/bin/streamlit" ]]; then
  STREAMLIT_BIN="$PROJECT_DIR/.venv/bin/streamlit"
elif [[ -x "$PROJECT_DIR/.venv-macbook/bin/streamlit" ]]; then
  STREAMLIT_BIN="$PROJECT_DIR/.venv-macbook/bin/streamlit"
elif ! STREAMLIT_BIN="$(command -v streamlit 2>/dev/null)"; then
  echo "streamlit was not found. Install dependencies with: python3 -m pip install -r requirements.txt" >&2
  exit 1
fi

cd "$PROJECT_DIR"
"$STREAMLIT_BIN" run "$PROJECT_DIR/walking_dashboard.py" \
  --server.port "$DASHBOARD_PORT" \
  --server.headless false \
  --browser.gatherUsageStats false
