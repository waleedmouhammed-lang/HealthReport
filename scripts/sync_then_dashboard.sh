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

dashboard_is_healthy() {
  command -v curl >/dev/null 2>&1 && curl --max-time 3 -fsS "$HEALTH_URL" >/dev/null 2>&1
}

stop_stale_dashboard() {
  local pids
  pids="$(pgrep -f "streamlit run .*walking_dashboard.py" || true)"
  if [[ -n "$pids" ]]; then
    echo "Stopping stale dashboard process: $pids"
    kill $pids || true
    sleep 2

    pids="$(pgrep -f "streamlit run .*walking_dashboard.py" || true)"
    if [[ -n "$pids" ]]; then
      echo "Force-stopping stale dashboard process: $pids"
      kill -9 $pids || true
      sleep 1
    fi
  fi
}

if dashboard_is_healthy; then
  echo "Dashboard already running at $DASHBOARD_URL"
else
  stop_stale_dashboard
  nohup "$STREAMLIT_BIN" run "$PROJECT_DIR/walking_dashboard.py" \
    --server.port "$DASHBOARD_PORT" \
    --server.headless true \
    --browser.gatherUsageStats false \
    > "$PROJECT_DIR/logs/dashboard.log" 2>&1 < /dev/null &
  dashboard_pid=$!
  disown "$dashboard_pid" 2>/dev/null || true
  echo "Started dashboard at $DASHBOARD_URL"
  sleep 4

  if ! dashboard_is_healthy; then
    echo "Dashboard did not become healthy. Check $PROJECT_DIR/logs/dashboard.log" >&2
    exit 1
  fi
fi

if command -v open >/dev/null 2>&1; then
  echo "Opening dashboard in browser: $DASHBOARD_URL"
  open "$DASHBOARD_URL" || echo "Could not open browser automatically. Open $DASHBOARD_URL manually."
else
  echo "Open dashboard: $DASHBOARD_URL"
fi
