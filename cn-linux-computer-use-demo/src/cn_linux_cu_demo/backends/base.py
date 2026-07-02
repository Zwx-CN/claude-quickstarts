from __future__ import annotations

from abc import ABC, abstractmethod

from cn_linux_cu_demo.schemas import ComputerAction, Observation


class ComputerBackend(ABC):
    @abstractmethod
    def screenshot(self) -> Observation:
        raise NotImplementedError

    @abstractmethod
    def execute(self, action: ComputerAction) -> None:
        raise NotImplementedError
