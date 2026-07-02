#!/usr/bin/env bash
set -euo pipefail

if [[ "$(uname -s)" != "Linux" ]]; then
  echo "This script is intended to run inside the Ubuntu VM." >&2
  exit 2
fi

if ! command -v apt-get >/dev/null 2>&1; then
  echo "This script currently supports Ubuntu/Debian VMs with apt-get." >&2
  exit 2
fi

sudo apt-get update
sudo apt-get install -y ca-certificates curl git gnupg openssh-server rsync

. /etc/os-release

case "${ID:-}" in
  debian|ubuntu)
    DOCKER_DISTRO="$ID"
    ;;
  *)
    echo "Unsupported distro for Docker's official apt repository: ${ID:-unknown}" >&2
    exit 2
    ;;
esac

USE_PACKAGED_DOCKER=0
sudo install -m 0755 -d /etc/apt/keyrings
if curl -fsSL "https://download.docker.com/linux/${DOCKER_DISTRO}/gpg" | sudo gpg --batch --yes --dearmor -o /etc/apt/keyrings/docker.gpg; then
  sudo chmod a+r /etc/apt/keyrings/docker.gpg
  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/${DOCKER_DISTRO} \
    ${VERSION_CODENAME} stable" | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
  sudo apt-get update || USE_PACKAGED_DOCKER=1
else
  USE_PACKAGED_DOCKER=1
fi

if [[ "$USE_PACKAGED_DOCKER" -eq 0 ]] && sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin; then
  echo "Installed Docker from Docker's official apt repository."
else
  echo "Docker official repository install failed; falling back to Debian/Ubuntu packaged docker.io."
  sudo rm -f /etc/apt/sources.list.d/docker.list
  sudo apt-get update
  sudo apt-get install -y docker.io docker-compose
fi

sudo systemctl enable --now ssh
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"

cat <<'EOF'

VM provisioning complete.

Log out and back in once so your user can run docker without sudo.
Then find the VM IP with:
  hostname -I

On the Mac, set CU_UTM_SSH_TARGET in .env, for example:
  CU_UTM_SSH_TARGET=ubuntu@192.168.64.12

EOF
