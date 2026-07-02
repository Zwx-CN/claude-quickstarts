from __future__ import annotations

import os

from cn_linux_cu_demo.action_parser import parse_actions
from cn_linux_cu_demo.backends.base import ComputerBackend
from cn_linux_cu_demo.models.base import ComputerUseModel
from cn_linux_cu_demo.schemas import ActionKind, ComputerAction
from cn_linux_cu_demo.trace import TraceRecorder


class AgentLoop:
    def __init__(
        self,
        *,
        backend: ComputerBackend,
        model: ComputerUseModel,
        trace_root: str | None = None,
    ) -> None:
        self.backend = backend
        self.model = model
        self.trace_root = trace_root or os.environ.get("CU_TRACE_DIR", "./experiments/traces")

    def run(self, task_id: str, instruction: str, max_steps: int) -> tuple[bool, str]:
        trace = TraceRecorder(self.trace_root, task_id)
        history: list[ComputerAction] = []
        trace.write_event("task_started", {"instruction": instruction, "max_steps": max_steps})

        for step in range(1, max_steps + 1):
            observation = self.backend.screenshot()
            response = self.model.predict(instruction, observation, history)
            actions = parse_actions(response)
            trace.write_step(
                step=step,
                observation=observation,
                model_response=response,
                actions=actions,
            )

            for action in actions:
                history.append(action)
                if action.kind == ActionKind.DONE:
                    trace.write_event("task_done", {"step": step})
                    return True, "done"
                if action.kind == ActionKind.FAIL:
                    trace.write_event("task_failed", {"step": step, "reason": action.text or "failed"})
                    return False, action.text or "failed"
                self.backend.execute(action)

        trace.write_event("task_failed", {"reason": "max_steps_exceeded"})
        return False, "max_steps_exceeded"
