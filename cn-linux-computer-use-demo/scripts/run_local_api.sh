#!/usr/bin/env bash
set -euo pipefail

export DISPLAY="${DISPLAY:-:99}"
export CU_SCREEN_WIDTH="${CU_SCREEN_WIDTH:-1280}"
export CU_SCREEN_HEIGHT="${CU_SCREEN_HEIGHT:-720}"

uvicorn cn_linux_cu_demo.server:app --host 0.0.0.0 --port 8000 --reload
