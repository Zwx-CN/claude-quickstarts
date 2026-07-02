#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Show selected providers and deploy profile.")
    parser.add_argument("--profile", choices=["local-docker", "local-utm", "cloud-pod"], default=None)
    parser.add_argument("--provider", choices=["docker", "utm"], default=None, help="Legacy alias for --profile.")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    load_env(root / ".env")

    legacy_profile = f"local-{args.provider}" if args.provider else None
    profile = args.profile or legacy_profile or os.environ.get("CU_DEPLOY_PROFILE")
    if profile is None:
        legacy_provider = os.environ.get("CU_PROVIDER")
        desktop_provider = os.environ.get("CU_DESKTOP_PROVIDER") or legacy_provider or "docker"
        profile = "local-utm" if desktop_provider == "utm" else "local-docker"

    model_provider = os.environ.get("CU_MODEL_PROVIDER", "qwen")
    desktop_provider = os.environ.get("CU_DESKTOP_PROVIDER")
    if args.profile == "local-utm" or args.provider == "utm":
        desktop_provider = "utm"
    elif args.profile == "local-docker" or args.provider == "docker":
        desktop_provider = "docker"
    elif desktop_provider is None:
        desktop_provider = "utm" if profile == "local-utm" else "docker"

    print(f"model_provider={model_provider}")
    print(f"desktop_provider={desktop_provider}")
    print(f"deploy_profile={profile}")

    if profile == "local-docker":
        print("mode=Run Docker Compose directly on this Mac's Docker engine.")
        print("api=http://localhost:8000")
        print("novnc=http://localhost:6080/vnc.html")
        return _require("docker")

    if profile == "cloud-pod":
        print("mode=Run inside a cloud Linux pod. This demo does not provision cloud infra yet.")
        return 0

    print("mode=Run Docker Compose inside a visible Linux VM created with UTM.")
    print("api=http://<utm-vm-ip>:8000")
    print("novnc=http://<utm-vm-ip>:6080/vnc.html")
    ssh_target = os.environ.get("CU_UTM_SSH_TARGET", "")
    remote_dir = os.environ.get("CU_UTM_REMOTE_DIR", "~/cn-linux-computer-use-demo")
    print(f"ssh_target={ssh_target or '<unset>'}")
    print(f"remote_dir={remote_dir}")
    if not Path("/Applications/UTM.app").exists():
        print("missing=/Applications/UTM.app")
        return 1
    if shutil.which("utmctl") is None:
        print("missing=utmctl")
        return 1
    print("utm=installed")
    return 0


def _require(binary: str) -> int:
    if shutil.which(binary):
        print(f"{binary}=installed")
        return 0
    print(f"missing={binary}")
    return 1


def load_env(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


if __name__ == "__main__":
    sys.exit(main())
