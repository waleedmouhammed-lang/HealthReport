#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STREAMLIT_BIN="$PROJECT_DIR/.venv/bin/streamlit"
DASHBOARD_PORT="${DASHBOARD_PORT:-8501}"
DASHBOARD_URL="http://localhost:${DASHBOARD_PORT}"
HEALTH_URL="${DASHBOARD_URL}/_stcore/health"
IDLE_SHUTDOWN_SECONDS="${IDLE_SHUTDOWN_SECONDS:-20}"
CONNECT_TIMEOUT_SECONDS="${CONNECT_TIMEOUT_SECONDS:-120}"
STREAMLIT_PID=""

if [[ -x "$PROJECT_DIR/.venv/bin/streamlit" ]]; then
  STREAMLIT_BIN="$PROJECT_DIR/.venv/bin/streamlit"
elif [[ -x "$PROJECT_DIR/.venv-macbook/bin/streamlit" ]]; then
  STREAMLIT_BIN="$PROJECT_DIR/.venv-macbook/bin/streamlit"
elif ! STREAMLIT_BIN="$(command -v streamlit 2>/dev/null)"; then
  echo "streamlit was not found. Install dependencies with: python3 -m pip install -r requirements.txt" >&2
  exit 1
fi

cd "$PROJECT_DIR"

cleanup() {
  local exit_code=$?

  if [[ -n "${STREAMLIT_PID:-}" ]] && kill -0 "$STREAMLIT_PID" >/dev/null 2>&1; then
    echo "Stopping dashboard server on port $DASHBOARD_PORT..."
    kill "$STREAMLIT_PID" >/dev/null 2>&1 || true
    wait "$STREAMLIT_PID" >/dev/null 2>&1 || true
  fi

  exit "$exit_code"
}

trap cleanup EXIT INT TERM HUP TSTP

dashboard_is_healthy() {
  command -v curl >/dev/null 2>&1 && curl --max-time 2 -fsS "$HEALTH_URL" >/dev/null 2>&1
}

browser_has_connection() {
  command -v lsof >/dev/null 2>&1 && lsof -nP -iTCP:"$DASHBOARD_PORT" -sTCP:ESTABLISHED >/dev/null 2>&1
}

"$STREAMLIT_BIN" run "$PROJECT_DIR/walking_dashboard.py" \
  --server.port "$DASHBOARD_PORT" \
  --server.headless true \
  --browser.gatherUsageStats false &
STREAMLIT_PID=$!

for _ in $(seq 1 30); do
  if dashboard_is_healthy; then
    break
  fi
  if ! kill -0 "$STREAMLIT_PID" >/dev/null 2>&1; then
    echo "Dashboard server exited before becoming healthy." >&2
    exit 1
  fi
  sleep 1
done

if ! dashboard_is_healthy; then
  echo "Dashboard did not become healthy at $DASHBOARD_URL." >&2
  exit 1
fi

echo "Dashboard running at $DASHBOARD_URL"
if command -v open >/dev/null 2>&1; then
  open "$DASHBOARD_URL" >/dev/null 2>&1 || true
fi

connected_once=false
idle_started_at=""
started_at="$(date +%s)"

while kill -0 "$STREAMLIT_PID" >/dev/null 2>&1; do
  now="$(date +%s)"

  if browser_has_connection; then
    connected_once=true
    idle_started_at=""
  elif [[ "$connected_once" == true ]]; then
    if [[ -z "$idle_started_at" ]]; then
      idle_started_at="$now"
    elif (( now - idle_started_at >= IDLE_SHUTDOWN_SECONDS )); then
      echo "No active browser connection for ${IDLE_SHUTDOWN_SECONDS}s. Shutting down dashboard."
      exit 0
    fi
  elif (( now - started_at >= CONNECT_TIMEOUT_SECONDS )); then
    echo "No browser connected within ${CONNECT_TIMEOUT_SECONDS}s. Shutting down dashboard."
    exit 0
  fi

  sleep 2
done
