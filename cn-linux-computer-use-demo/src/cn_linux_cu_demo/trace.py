from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cn_linux_cu_demo.schemas import ComputerAction, Observation


class TraceRecorder:
    def __init__(self, root: str | Path, task_id: str) -> None:
        self.dir = Path(root) / task_id
        self.screenshot_dir = self.dir / "screenshots"
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        self.events_path = self.dir / "events.jsonl"

    def write_step(
        self,
        *,
        step: int,
        observation: Observation,
        model_response: str,
        actions: list[ComputerAction],
    ) -> None:
        screenshot_path = self.screenshot_dir / f"{step:04d}.png"
        screenshot_path.write_bytes(__import__("base64").b64decode(observation.screenshot_b64))
        self._append(
            {
                "type": "step",
                "step": step,
                "screenshot": str(screenshot_path),
                "screen": {"width": observation.width, "height": observation.height},
                "model_response": model_response,
                "actions": [action.model_dump(mode="json") for action in actions],
            }
        )

    def write_event(self, event_type: str, payload: dict[str, Any]) -> None:
        self._append({"type": event_type, **payload})

    def _append(self, payload: dict[str, Any]) -> None:
        payload["timestamp"] = datetime.now(timezone.utc).isoformat()
        with self.events_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
