from __future__ import annotations

import os
import threading
import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

from cn_linux_cu_demo.agent_loop import AgentLoop
from cn_linux_cu_demo.backends.pyautogui_x11 import PyAutoGUIX11Backend
from cn_linux_cu_demo.models.qwen import Qwen37PlusAdapter
from cn_linux_cu_demo.schemas import ComputerAction, Observation, TaskCreateRequest, TaskRecord, TaskStatus

load_dotenv()

app = FastAPI(title="CN Linux Computer Use Demo")
tasks: dict[str, TaskRecord] = {}
lock = threading.Lock()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _backend() -> PyAutoGUIX11Backend:
    return PyAutoGUIX11Backend()


@app.get("/health")
def health() -> dict:
    return {
        "ok": True,
        "display": os.environ.get("DISPLAY"),
        "desktop_ready": bool(os.environ.get("DISPLAY")),
    }


@app.get("/screenshot", response_model=Observation)
def screenshot() -> Observation:
    return _backend().screenshot()


@app.post("/actions")
def action(action: ComputerAction) -> dict:
    _backend().execute(action)
    return {"ok": True}


@app.post("/tasks", response_model=TaskRecord)
def create_task(req: TaskCreateRequest) -> TaskRecord:
    task_id = str(uuid.uuid4())
    record = TaskRecord(
        id=task_id,
        instruction=req.instruction,
        status=TaskStatus.WAITING,
        created_at=_now(),
        updated_at=_now(),
    )
    with lock:
        tasks[task_id] = record

    thread = threading.Thread(
        target=_run_task,
        args=(task_id, req.instruction, req.max_steps or int(os.environ.get("CU_MAX_STEPS", "30"))),
        daemon=True,
    )
    thread.start()
    return record


@app.get("/tasks/{task_id}", response_model=TaskRecord)
def get_task(task_id: str) -> TaskRecord:
    with lock:
        record = tasks.get(task_id)
    if record is None:
        raise HTTPException(status_code=404, detail="task not found")
    return record


def _run_task(task_id: str, instruction: str, max_steps: int) -> None:
    _update_task(task_id, status=TaskStatus.RUNNING)
    try:
        loop = AgentLoop(backend=_backend(), model=Qwen37PlusAdapter())
        ok, result = loop.run(task_id, instruction, max_steps)
        _update_task(
            task_id,
            status=TaskStatus.DONE if ok else TaskStatus.FAILED,
            result=result if ok else None,
            error=None if ok else result,
            steps=max_steps,
        )
    except Exception as exc:
        _update_task(task_id, status=TaskStatus.FAILED, error=repr(exc))


def _update_task(task_id: str, **updates) -> None:
    with lock:
        record = tasks[task_id]
        data = record.model_dump()
        data.update(updates)
        data["updated_at"] = _now()
        tasks[task_id] = TaskRecord(**data)
