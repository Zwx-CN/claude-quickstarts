#!/usr/bin/env bash
set -euo pipefail

export DISPLAY="${DISPLAY:-:99}"
export CU_SCREEN_WIDTH="${CU_SCREEN_WIDTH:-1280}"
export CU_SCREEN_HEIGHT="${CU_SCREEN_HEIGHT:-720}"

Xvfb "$DISPLAY" -screen 0 "${CU_SCREEN_WIDTH}x${CU_SCREEN_HEIGHT}x24" -ac +extension RANDR &
sleep 1

openbox >/tmp/openbox.log 2>&1 &
x11vnc -display "$DISPLAY" -forever -shared -nopw -rfbport 5900 >/tmp/x11vnc.log 2>&1 &
websockify --web=/usr/share/novnc 6080 localhost:5900 >/tmp/websockify.log 2>&1 &

exec uvicorn cn_linux_cu_demo.server:app --host 0.0.0.0 --port 8000
