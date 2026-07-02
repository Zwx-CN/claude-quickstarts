#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List

import httpx
from dotenv import load_dotenv

from cn_linux_cu_demo.action_parser import parse_actions
from cn_linux_cu_demo.backends.pyautogui_x11 import PyAutoGUIX11Backend
from cn_linux_cu_demo.schemas import ActionKind


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    load_dotenv(ROOT / ".env")

    base_url = os.environ.get("QWEN_BASE_URL", "").rstrip("/")
    api_key = os.environ.get("QWEN_API_KEY", "")
    model = os.environ.get("QWEN_MODEL", "qwen3.7-plus")
    if not base_url or not api_key:
        raise RuntimeError("QWEN_BASE_URL and QWEN_API_KEY are required")

    print("== Step 1: ask LLM to request a screenshot action ==")
    planner_response = chat(
        base_url=base_url,
        api_key=api_key,
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a computer-use planner. The user wants visual information "
                    "about the current Linux desktop. You cannot see the desktop yet. "
                    "Request exactly one screenshot action using this format:\n"
                    "Action: take screenshot\n"
                    '<tool_call>{"name":"computer","arguments":{"action":"screenshot"}}</tool_call>'
                ),
            },
            {
                "role": "user",
                "content": (
                    "Please inspect the current desktop. First request a screenshot; "
                    "after the harness returns it, describe how many desktop shortcuts "
                    "or visible launcher icons there are and what they appear to be."
                ),
            },
        ],
    )
    print(planner_response)

    actions = parse_actions(planner_response)
    if len(actions) != 1 or actions[0].kind != ActionKind.SCREENSHOT:
        raise RuntimeError(f"Expected one screenshot action, got: {actions}")

    print("\n== Step 2: harness executes screenshot action ==")
    backend = PyAutoGUIX11Backend()
    observation = backend.screenshot()
    print(f"screenshot={observation.width}x{observation.height}, b64_chars={len(observation.screenshot_b64)}")

    print("\n== Step 3: send screenshot back to LLM for description ==")
    data_url = f"data:image/png;base64,{observation.screenshot_b64}"
    answer = chat(
        base_url=base_url,
        api_key=api_key,
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a careful visual inspector for a Linux desktop screenshot. "
                    "Answer in Chinese. Distinguish desktop shortcuts from panel or dock "
                    "launcher icons if possible. If an icon is unclear, say it is unclear."
                ),
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "请解释这张 Linux 桌面截图里能看到什么。重点回答："
                            "桌面区域有多少快捷方式？底部/面板可见多少 launcher 图标？"
                            "它们分别可能是什么？"
                        ),
                    },
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            },
        ],
    )
    print(answer)
    return 0


def chat(*, base_url: str, api_key: str, model: str, messages: List[Dict[str, Any]]) -> str:
    payload = {"model": model, "messages": messages, "temperature": 0}
    headers = {"Authorization": f"Bearer {api_key}"}
    with httpx.Client(timeout=120) as client:
        response = client.post(f"{base_url}/chat/completions", json=payload, headers=headers)
        response.raise_for_status()
        body = response.json()
    return body["choices"][0]["message"]["content"]


if __name__ == "__main__":
    raise SystemExit(main())
