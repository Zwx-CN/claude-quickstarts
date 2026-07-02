#!/usr/bin/env bash
set -euo pipefail

if [[ "$(uname -s)" != "Linux" ]]; then
  echo "This script is intended to run inside the Debian/Ubuntu VM." >&2
  exit 2
fi

if ! command -v apt-get >/dev/null 2>&1; then
  echo "This script currently supports Debian/Ubuntu VMs with apt-get." >&2
  exit 2
fi

if [[ "$(id -u)" -eq 0 ]]; then
  SUDO=()
  DEMO_USER="${DEMO_USER:-debian}"
else
  SUDO=(sudo)
  DEMO_USER="${DEMO_USER:-$USER}"
fi

PIP_INDEX_URL="${PIP_INDEX_URL:-https://pypi.tuna.tsinghua.edu.cn/simple}"

"${SUDO[@]}" apt-get update
"${SUDO[@]}" apt-get install -y \
  python3 \
  python3-pip \
  python3-tk \
  python3-venv \
  xclip \
  xdotool \
  scrot

if [[ "$(id -u)" -eq 0 ]]; then
  chown -R "$DEMO_USER:$DEMO_USER" .
  sudo -u "$DEMO_USER" python3 -m venv .venv
  sudo -u "$DEMO_USER" env PIP_INDEX_URL="$PIP_INDEX_URL" .venv/bin/python -m pip install --upgrade pip
  sudo -u "$DEMO_USER" env PIP_INDEX_URL="$PIP_INDEX_URL" .venv/bin/python -m pip install -e .
else
  python3 -m venv .venv
  PIP_INDEX_URL="$PIP_INDEX_URL" .venv/bin/python -m pip install --upgrade pip
  PIP_INDEX_URL="$PIP_INDEX_URL" .venv/bin/python -m pip install -e .
fi

cat <<'EOF'

Direct VM runtime is ready.

Start the API on the visible X11 desktop with:
  scripts/run_visible_vm_api.sh

This mode controls DISPLAY=:0.0, which is the UTM desktop you can see.
EOF
