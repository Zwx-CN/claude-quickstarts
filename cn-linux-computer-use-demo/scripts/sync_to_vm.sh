#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

WITH_ENV=0
START=0
TARGET="${CU_UTM_SSH_TARGET:-}"
REMOTE_DIR="${CU_UTM_REMOTE_DIR:-~/cn-linux-computer-use-demo}"

usage() {
  cat <<'EOF'
Usage:
  scripts/sync_to_vm.sh --target ubuntu@<vm-ip> [--remote-dir ~/cn-linux-computer-use-demo] [--with-env] [--start]

Options:
  --target       SSH target for the UTM VM, for example ubuntu@192.168.64.12.
  --remote-dir   Directory on the VM. Defaults to CU_UTM_REMOTE_DIR or ~/cn-linux-computer-use-demo.
  --with-env     Copy .env to the VM. Use this only for a VM you trust.
  --start        Run docker compose up --build -d on the VM after syncing.

This script does not call any LLM endpoint. Starting the API is local only; POST /tasks is what calls the model.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      TARGET="${2:-}"
      shift 2
      ;;
    --remote-dir)
      REMOTE_DIR="${2:-}"
      shift 2
      ;;
    --with-env)
      WITH_ENV=1
      shift
      ;;
    --start)
      START=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "$TARGET" ]]; then
  echo "Missing --target or CU_UTM_SSH_TARGET." >&2
  usage >&2
  exit 2
fi

if ! command -v rsync >/dev/null 2>&1; then
  echo "Missing rsync on the Mac." >&2
  exit 1
fi

ssh "$TARGET" "mkdir -p $REMOTE_DIR"

RSYNC_EXCLUDES=(
  "--exclude=.git/"
  "--exclude=.venv/"
  "--exclude=__pycache__/"
  "--exclude=.pytest_cache/"
  "--exclude=.ruff_cache/"
  "--exclude=*.egg-info/"
  "--exclude=experiments/traces/"
)

if [[ "$WITH_ENV" -eq 0 ]]; then
  RSYNC_EXCLUDES+=("--exclude=.env")
fi

rsync -az --delete "${RSYNC_EXCLUDES[@]}" ./ "$TARGET:$REMOTE_DIR/"

if [[ "$WITH_ENV" -eq 1 ]]; then
  ssh "$TARGET" "chmod 600 $REMOTE_DIR/.env"
fi

if [[ "$START" -eq 1 ]]; then
  ssh "$TARGET" "cd $REMOTE_DIR && if docker compose version >/dev/null 2>&1; then docker compose up --build -d; else docker-compose up --build -d; fi"
fi

cat <<EOF
Synced demo to:
  $TARGET:$REMOTE_DIR

Next commands:
  ssh $TARGET
  cd $REMOTE_DIR
  docker compose up --build

After it starts, open from the Mac:
  http://<vm-ip>:6080/vnc.html
  http://<vm-ip>:8000/health
EOF
