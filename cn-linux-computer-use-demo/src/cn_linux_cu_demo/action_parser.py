from __future__ import annotations

import json
import re
from typing import Any

from .schemas import ActionKind, ComputerAction, Coordinate


_TOOL_BLOCK_RE = re.compile(r"<tool_call>\s*(.*?)\s*</tool_call>", re.DOTALL)
_XML_FUNCTION_RE = re.compile(r"<function=([^>]+)>\s*(.*?)\s*</function>", re.DOTALL)
_XML_PARAM_RE = re.compile(r"<parameter=([^>]+)>\s*(.*?)\s*</parameter>", re.DOTALL)


class ActionParseError(ValueError):
    pass


def parse_actions(text: str) -> list[ComputerAction]:
    """Parse OSWorld-style tool calls into bounded internal actions.

    Supported shapes:
    - JSON: <tool_call>{"name":"computer","arguments":{"action":"left_click", ...}}</tool_call>
    - Qwen XML: <tool_call><function=computer_use><parameter=action>...</parameter></function></tool_call>

    Free-form pyautogui code is intentionally not executed by this demo.
    """

    if not text or not text.strip():
        raise ActionParseError("empty model response")

    if "[INFEASIBLE]" in text:
        return [ComputerAction(kind=ActionKind.FAIL, text="infeasible")]

    actions: list[ComputerAction] = []
    for block in _TOOL_BLOCK_RE.findall(text):
        payload = _parse_tool_block(block)
        if payload:
            actions.append(_payload_to_action(payload))

    if actions:
        return actions

    upper = text.strip().upper()
    if upper in {"DONE", "FAIL", "WAIT"}:
        return [_special_action(upper)]

    raise ActionParseError("no supported tool_call found")


def _parse_tool_block(block: str) -> dict[str, Any] | None:
    block = block.strip()
    if not block:
        return None

    try:
        obj = json.loads(block)
    except json.JSONDecodeError:
        obj = None

    if isinstance(obj, dict):
        name = obj.get("name") or obj.get("function")
        args = obj.get("arguments") or obj.get("input") or {}
        if name in {"computer", "computer_use"} and isinstance(args, dict):
            return args
        if "action" in obj:
            return obj

    function_match = _XML_FUNCTION_RE.search(block)
    if function_match and function_match.group(1).strip() == "computer_use":
        params: dict[str, Any] = {}
        for name, value in _XML_PARAM_RE.findall(function_match.group(2)):
            params[name.strip()] = _coerce_param(value.strip())
        return params

    return None


def _coerce_param(value: str) -> Any:
    if not value:
        return value
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        pass
    if "," in value:
        pieces = [piece.strip() for piece in value.split(",")]
        if len(pieces) == 2:
            try:
                return [float(pieces[0]), float(pieces[1])]
            except ValueError:
                return value
    return value


def _payload_to_action(payload: dict[str, Any]) -> ComputerAction:
    raw_action = str(payload.get("action") or payload.get("type") or "").strip().lower()
    if not raw_action:
        raise ActionParseError(f"missing action in payload: {payload}")

    aliases = {
        "click": ActionKind.LEFT_CLICK,
        "left_click": ActionKind.LEFT_CLICK,
        "right_click": ActionKind.RIGHT_CLICK,
        "double_click": ActionKind.DOUBLE_CLICK,
        "mouse_move": ActionKind.MOUSE_MOVE,
        "move": ActionKind.MOUSE_MOVE,
        "left_click_drag": ActionKind.DRAG,
        "drag": ActionKind.DRAG,
        "type": ActionKind.TYPE,
        "key": ActionKind.KEY,
        "hotkey": ActionKind.KEY,
        "scroll": ActionKind.SCROLL,
        "hscroll": ActionKind.SCROLL,
        "wait": ActionKind.WAIT,
        "screenshot": ActionKind.SCREENSHOT,
        "done": ActionKind.DONE,
        "answer": ActionKind.DONE,
        "terminate": _termination_kind(payload),
        "fail": ActionKind.FAIL,
    }
    kind = aliases.get(raw_action)
    if kind is None:
        raise ActionParseError(f"unsupported action: {raw_action}")

    return ComputerAction(
        kind=kind,
        coordinate=_parse_coordinate(payload.get("coordinate") or payload.get("point")),
        start_coordinate=_parse_coordinate(payload.get("start_coordinate")),
        text=_parse_text(payload),
        keys=_parse_keys(payload),
        direction=_parse_direction(payload),
        amount=_parse_amount(payload),
        duration=_parse_duration(payload),
        raw=payload,
    )


def _termination_kind(payload: dict[str, Any]) -> ActionKind:
    status = str(payload.get("status") or "success").strip().lower()
    return ActionKind.FAIL if status in {"fail", "failed", "failure", "error"} else ActionKind.DONE


def _parse_coordinate(value: Any) -> Coordinate | None:
    if value is None or value == "":
        return None
    if isinstance(value, dict):
        x = value.get("x")
        y = value.get("y")
        space = value.get("space", "normalized")
    elif isinstance(value, (list, tuple)) and len(value) >= 2:
        x, y = value[0], value[1]
        space = "normalized"
    elif isinstance(value, str):
        found = re.findall(r"-?\d+(?:\.\d+)?", value)
        if len(found) < 2:
            return None
        x, y = float(found[0]), float(found[1])
        space = "normalized"
    else:
        return None
    return Coordinate(x=x, y=y, space=space)


def _parse_text(payload: dict[str, Any]) -> str | None:
    value = payload.get("text")
    if value is None:
        value = payload.get("content")
    return None if value is None else str(value)


def _parse_keys(payload: dict[str, Any]) -> list[str]:
    keys = payload.get("keys") or payload.get("key") or payload.get("text")
    if not keys:
        return []
    if isinstance(keys, str):
        if "+" in keys:
            return [piece.strip().lower() for piece in keys.split("+") if piece.strip()]
        return [piece.strip().lower() for piece in keys.split() if piece.strip()]
    if isinstance(keys, list):
        return [str(key).strip().lower() for key in keys if str(key).strip()]
    return [str(keys).strip().lower()]


def _parse_direction(payload: dict[str, Any]) -> str | None:
    direction = payload.get("scroll_direction") or payload.get("direction")
    if direction:
        return str(direction).strip().lower()
    pixels = payload.get("pixels")
    if pixels is None:
        return None
    try:
        return "up" if int(float(pixels)) > 0 else "down"
    except ValueError:
        return None


def _parse_amount(payload: dict[str, Any]) -> int | None:
    for key in ("scroll_amount", "amount", "pixels"):
        if key in payload:
            try:
                return abs(int(float(payload[key])))
            except (TypeError, ValueError):
                return None
    return None


def _parse_duration(payload: dict[str, Any]) -> float | None:
    for key in ("duration", "time"):
        if key in payload:
            try:
                return float(payload[key])
            except (TypeError, ValueError):
                return None
    return None


def _special_action(token: str) -> ComputerAction:
    return {
        "DONE": ComputerAction(kind=ActionKind.DONE),
        "FAIL": ComputerAction(kind=ActionKind.FAIL),
        "WAIT": ComputerAction(kind=ActionKind.WAIT, duration=1),
    }[token]
