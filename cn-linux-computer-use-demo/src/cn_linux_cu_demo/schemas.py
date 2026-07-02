from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field


class StrEnum(str, Enum):
    pass


class ActionKind(StrEnum):
    LEFT_CLICK = "left_click"
    RIGHT_CLICK = "right_click"
    DOUBLE_CLICK = "double_click"
    MOUSE_MOVE = "mouse_move"
    DRAG = "drag"
    TYPE = "type"
    KEY = "key"
    SCROLL = "scroll"
    WAIT = "wait"
    SCREENSHOT = "screenshot"
    DONE = "done"
    FAIL = "fail"


class Coordinate(BaseModel):
    x: Union[int, float]
    y: Union[int, float]
    space: Literal["normalized", "absolute"] = "normalized"


class ComputerAction(BaseModel):
    kind: ActionKind
    coordinate: Optional[Coordinate] = None
    start_coordinate: Optional[Coordinate] = None
    text: Optional[str] = None
    keys: List[str] = Field(default_factory=list)
    direction: Optional[Literal["up", "down", "left", "right"]] = None
    amount: Optional[int] = None
    duration: Optional[float] = None
    raw: Dict[str, Any] = Field(default_factory=dict)


class Observation(BaseModel):
    screenshot_b64: str
    width: int
    height: int


class TaskStatus(StrEnum):
    WAITING = "waiting"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class TaskCreateRequest(BaseModel):
    instruction: str
    max_steps: Optional[int] = None


class TaskRecord(BaseModel):
    id: str
    instruction: str
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    steps: int = 0
    result: Optional[str] = None
    error: Optional[str] = None
