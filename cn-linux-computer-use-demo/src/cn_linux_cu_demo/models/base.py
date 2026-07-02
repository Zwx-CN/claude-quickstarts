from __future__ import annotations

from abc import ABC, abstractmethod

from cn_linux_cu_demo.schemas import ComputerAction, Observation


class ComputerUseModel(ABC):
    @abstractmethod
    def predict(
        self,
        instruction: str,
        observation: Observation,
        history: list[ComputerAction],
    ) -> str:
        raise NotImplementedError
