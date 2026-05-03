#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

"$PROJECT_DIR/scripts/sync_only.sh"
"$PROJECT_DIR/scripts/run_dashboard.sh"
