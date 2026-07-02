from __future__ import annotations

import os
from enum import Enum

from pydantic import BaseModel


class StrEnum(str, Enum):
    pass


class ModelProviderKind(StrEnum):
    QWEN = "qwen"
    MINIMAX = "minimax"
    GLM = "glm"


class DesktopProviderKind(StrEnum):
    DOCKER = "docker"
    UTM = "utm"
    CLOUD_POD = "cloud-pod"


class DeployProfileKind(StrEnum):
    LOCAL_DOCKER = "local-docker"
    LOCAL_UTM = "local-utm"
    CLOUD_POD = "cloud-pod"


class ProviderConfig(BaseModel):
    model_provider: ModelProviderKind = ModelProviderKind.QWEN
    desktop_provider: DesktopProviderKind = DesktopProviderKind.DOCKER
    deploy_profile: DeployProfileKind = DeployProfileKind.LOCAL_DOCKER
    api_port: int = 8000
    novnc_port: int = 6080
    vnc_port: int = 5900

    @classmethod
    def from_env(cls) -> "ProviderConfig":
        legacy_provider = os.environ.get("CU_PROVIDER")
        desktop_provider = os.environ.get("CU_DESKTOP_PROVIDER") or legacy_provider or DesktopProviderKind.DOCKER.value
        deploy_profile = os.environ.get("CU_DEPLOY_PROFILE")
        if deploy_profile is None:
            deploy_profile = "local-utm" if desktop_provider == DesktopProviderKind.UTM.value else "local-docker"

        return cls(
            model_provider=ModelProviderKind(os.environ.get("CU_MODEL_PROVIDER", ModelProviderKind.QWEN.value)),
            desktop_provider=DesktopProviderKind(desktop_provider),
            deploy_profile=DeployProfileKind(deploy_profile),
            api_port=int(os.environ.get("CU_API_PORT", "8000")),
            novnc_port=int(os.environ.get("CU_NOVNC_PORT", "6080")),
            vnc_port=int(os.environ.get("CU_VNC_PORT", "5900")),
        )

    @property
    def is_visible_vm(self) -> bool:
        return self.desktop_provider == DesktopProviderKind.UTM
