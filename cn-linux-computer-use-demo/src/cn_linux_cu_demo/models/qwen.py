from __future__ import annotations

import os

import httpx

from cn_linux_cu_demo.models.base import ComputerUseModel
from cn_linux_cu_demo.schemas import ComputerAction, Observation


QWEN_SYSTEM_PROMPT = """You are a Linux desktop computer-use agent.
You receive a screenshot and a user task. Output exactly one action as a tool call.

Coordinates must be normalized integers in [0, 1000], where (0,0) is the top-left
corner and (1000,1000) is the bottom-right corner.

Supported actions:
- left_click: {"action":"left_click","coordinate":[x,y]}
- right_click: {"action":"right_click","coordinate":[x,y]}
- double_click: {"action":"double_click","coordinate":[x,y]}
- mouse_move: {"action":"mouse_move","coordinate":[x,y]}
- left_click_drag: {"action":"left_click_drag","start_coordinate":[x,y],"coordinate":[x,y]}
- type: {"action":"type","text":"..."}
- key: {"action":"key","keys":["ctrl","s"]}
- scroll: {"action":"scroll","coordinate":[x,y],"scroll_direction":"up|down","scroll_amount":5}
- wait: {"action":"wait","duration":1}
- terminate: {"action":"terminate","status":"success|failure"}

Return exactly:
Action: <short imperative>
<tool_call>{"name":"computer","arguments":{...}}</tool_call>
"""


class Qwen37PlusAdapter(ComputerUseModel):
    """OpenAI-compatible Qwen adapter.

    Keep endpoint/model configurable because Qwen 3.7 Plus may be exposed through
    DashScope, an internal gateway, or another OpenAI-compatible proxy.
    """

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        timeout: float = 120,
    ) -> None:
        self.base_url = (base_url or os.environ.get("QWEN_BASE_URL") or "").rstrip("/")
        self.api_key = api_key or os.environ.get("QWEN_API_KEY")
        self.model = model or os.environ.get("QWEN_MODEL", "qwen3.7-plus")
        self.timeout = timeout
        if not self.base_url or not self.api_key:
            raise RuntimeError("QWEN_BASE_URL and QWEN_API_KEY are required")

    def predict(
        self,
        instruction: str,
        observation: Observation,
        history: list[ComputerAction],
    ) -> str:
        history_text = "\n".join(
            f"{idx + 1}. {action.kind.value} {action.model_dump(exclude={'raw'})}"
            for idx, action in enumerate(history[-8:])
        ) or "None"
        data_url = f"data:image/png;base64,{observation.screenshot_b64}"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": QWEN_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                f"Task: {instruction}\n"
                                f"Screen: {observation.width}x{observation.height}\n"
                                f"Previous actions:\n{history_text}\n"
                                "Decide the next single action."
                            ),
                        },
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                },
            ],
            "temperature": 0,
        }

        headers = {"Authorization": f"Bearer {self.api_key}"}
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(f"{self.base_url}/chat/completions", json=payload, headers=headers)
            response.raise_for_status()
            body = response.json()
        return body["choices"][0]["message"]["content"]
