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

PROFILE="${1:-${CU_DEPLOY_PROFILE:-}}"
if [[ -z "$PROFILE" ]]; then
  if [[ "${CU_DESKTOP_PROVIDER:-${CU_PROVIDER:-docker}}" == "utm" ]]; then
    PROFILE="local-utm"
  else
    PROFILE="local-docker"
  fi
fi

case "$PROFILE" in
  docker|local-docker)
    python3 scripts/provider_info.py --profile local-docker
    exec docker compose up --build
    ;;
  utm|local-utm)
    python3 scripts/provider_info.py --profile local-utm
    cat <<'EOF'

UTM deploy profile is selected.

One-time VM setup:
1. Open UTM and create/start an ARM64 Ubuntu Desktop VM.
2. Inside the VM, enable SSH access:
   sudo apt-get update
   sudo apt-get install -y openssh-server rsync
   sudo systemctl enable --now ssh
3. Find the VM IP:
   hostname -I
4. From the Mac, sync this demo into the VM:
   scripts/sync_to_vm.sh --target ubuntu@<utm-vm-ip>
5. Inside the VM, install Docker:
   bash scripts/provision_ubuntu_vm.sh
6. Log out and back into the VM once.

Deploy from the Mac:
  scripts/sync_to_vm.sh --target ubuntu@<utm-vm-ip> --with-env --start

Then open:
  http://<utm-vm-ip>:6080/vnc.html
  http://<utm-vm-ip>:8000/health

EOF
    ;;
  cloud-pod)
    python3 scripts/provider_info.py --profile cloud-pod
    echo "Cloud pod provisioning is not implemented in this demo yet." >&2
    exit 2
    ;;
  *)
    echo "Unknown deploy profile: $PROFILE" >&2
    echo "Expected: local-docker, local-utm, or cloud-pod" >&2
    exit 2
    ;;
esac
