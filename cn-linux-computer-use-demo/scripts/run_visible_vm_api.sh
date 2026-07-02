#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

REQUESTED_DISPLAY="${DISPLAY:-:0.0}"
REQUESTED_XAUTHORITY="${XAUTHORITY:-$HOME/.Xauthority}"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

export DISPLAY="$REQUESTED_DISPLAY"
export XAUTHORITY="$REQUESTED_XAUTHORITY"
export CU_SCREEN_WIDTH="${CU_SCREEN_WIDTH:-1280}"
export CU_SCREEN_HEIGHT="${CU_SCREEN_HEIGHT:-720}"
export CU_TRACE_DIR="${CU_TRACE_DIR:-./experiments/traces}"

. .venv/bin/activate
exec uvicorn cn_linux_cu_demo.server:app --host 0.0.0.0 --port "${CU_API_PORT:-8000}"
