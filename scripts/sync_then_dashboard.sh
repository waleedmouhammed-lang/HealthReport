#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="$PROJECT_DIR/.venv/bin/python"
STREAMLIT_BIN="$PROJECT_DIR/.venv/bin/streamlit"
DASHBOARD_PORT="${DASHBOARD_PORT:-8501}"
DASHBOARD_URL="http://localhost:${DASHBOARD_PORT}"
HEALTH_URL="${DASHBOARD_URL}/_stcore/health"

if [[ -x "$PROJECT_DIR/.venv/bin/python3" ]]; then
  PYTHON_BIN="$PROJECT_DIR/.venv/bin/python3"
elif [[ -x "$PROJECT_DIR/.venv-macbook/bin/python3" ]]; then
  PYTHON_BIN="$PROJECT_DIR/.venv-macbook/bin/python3"
elif [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="$(command -v python3)"
fi

if [[ -x "$PROJECT_DIR/.venv/bin/streamlit" ]]; then
  STREAMLIT_BIN="$PROJECT_DIR/.venv/bin/streamlit"
elif [[ -x "$PROJECT_DIR/.venv-macbook/bin/streamlit" ]]; then
  STREAMLIT_BIN="$PROJECT_DIR/.venv-macbook/bin/streamlit"
elif ! STREAMLIT_BIN="$(command -v streamlit 2>/dev/null)"; then
  echo "streamlit was not found. Install dependencies with: $PYTHON_BIN -m pip install -r requirements.txt" >&2
  exit 1
fi

mkdir -p "$PROJECT_DIR/logs"

cd "$PROJECT_DIR"
"$PYTHON_BIN" "$PROJECT_DIR/main.py"

if command -v curl >/dev/null 2>&1 && curl -fsS "$HEALTH_URL" >/dev/null 2>&1; then
  echo "Dashboard already running at $DASHBOARD_URL"
else
  nohup "$STREAMLIT_BIN" run "$PROJECT_DIR/walking_dashboard.py" \
    --server.port "$DASHBOARD_PORT" \
    --server.headless true \
    --browser.gatherUsageStats false \
    > "$PROJECT_DIR/logs/dashboard.log" 2>&1 &
  echo "Started dashboard at $DASHBOARD_URL"
  sleep 2
fi

if command -v open >/dev/null 2>&1; then
  open "$DASHBOARD_URL"
else
  echo "Open dashboard: $DASHBOARD_URL"
fi
