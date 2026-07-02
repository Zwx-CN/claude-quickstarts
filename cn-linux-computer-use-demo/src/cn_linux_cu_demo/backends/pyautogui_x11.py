from __future__ import annotations

import base64
import io
import time

from PIL import Image

from cn_linux_cu_demo.backends.base import ComputerBackend
from cn_linux_cu_demo.schemas import ActionKind, ComputerAction, Coordinate, Observation


class PyAutoGUIX11Backend(ComputerBackend):
    """X11 backend for the MVP.

    Imports pyautogui lazily so tests can import the package on machines without
    an active X server.
    """

    def __init__(self, pause: float = 0.1) -> None:
        import pyautogui

        self.pyautogui = pyautogui
        self.pyautogui.PAUSE = pause

    def screenshot(self) -> Observation:
        try:
            import mss

            with mss.mss() as sct:
                monitor = sct.monitors[1]
                shot = sct.grab(monitor)
                image = Image.frombytes("RGB", shot.size, shot.rgb)
        except Exception:
            image = self.pyautogui.screenshot()

        buf = io.BytesIO()
        image.save(buf, format="PNG")
        return Observation(
            screenshot_b64=base64.b64encode(buf.getvalue()).decode("ascii"),
            width=image.width,
            height=image.height,
        )

    def execute(self, action: ComputerAction) -> None:
        if action.kind == ActionKind.WAIT:
            time.sleep(action.duration or 1)
            return
        if action.kind in {ActionKind.DONE, ActionKind.FAIL, ActionKind.SCREENSHOT}:
            return

        width, height = self.pyautogui.size()
        xy = self._xy(action.coordinate, width, height)

        if action.kind == ActionKind.LEFT_CLICK:
            self.pyautogui.click(*xy)
        elif action.kind == ActionKind.RIGHT_CLICK:
            self.pyautogui.rightClick(*xy)
        elif action.kind == ActionKind.DOUBLE_CLICK:
            self.pyautogui.doubleClick(*xy)
        elif action.kind == ActionKind.MOUSE_MOVE:
            self.pyautogui.moveTo(*xy)
        elif action.kind == ActionKind.DRAG:
            if action.start_coordinate:
                self.pyautogui.moveTo(*self._xy(action.start_coordinate, width, height))
            self.pyautogui.dragTo(*xy, duration=action.duration or 0.4)
        elif action.kind == ActionKind.TYPE:
            self.pyautogui.typewrite(action.text or "")
        elif action.kind == ActionKind.KEY:
            if len(action.keys) > 1:
                self.pyautogui.hotkey(*action.keys)
            elif action.keys:
                self.pyautogui.press(action.keys[0])
        elif action.kind == ActionKind.SCROLL:
            amount = action.amount or 5
            direction = action.direction or "down"
            if xy:
                self.pyautogui.moveTo(*xy)
            delta = amount if direction == "up" else -amount
            self.pyautogui.scroll(delta)

    @staticmethod
    def _xy(coordinate: Coordinate | None, width: int, height: int) -> tuple[int, int]:
        if coordinate is None:
            return (width // 2, height // 2)
        if coordinate.space == "absolute":
            return int(round(coordinate.x)), int(round(coordinate.y))
        return (
            int(round(float(coordinate.x) / 1000 * width)),
            int(round(float(coordinate.y) / 1000 * height)),
        )
