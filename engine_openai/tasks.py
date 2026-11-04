"""OpenAI's two shapes: images answer inline, video is a job plus a content fetch."""

from __future__ import annotations

import time
from collections.abc import Callable

from .transport import ProviderError

RequestFn = Callable[..., dict]
EmitFn = Callable[[str], None]

LIVE_STATES = frozenset({"queued", "in_progress", "processing", "starting"})
SUCCESS_STATES = frozenset({"completed", "succeeded", "success"})


def is_terminal(status: object) -> bool:
    return str(status or "") not in LIVE_STATES


def call_sync(request: RequestFn, path: str, body: dict, *,
              emit: EmitFn = lambda _msg: None, prefix: str = "") -> dict:
    """One request that is also the answer."""
    record = request("POST", path, body)
    if not isinstance(record, dict):
        raise ProviderError(200, "OpenAI returned an unreadable response")
    emit(f"{prefix} ✅ Response received")
    return record


def submit_video(request: RequestFn, path: str, fields: dict, *,
                 files: dict | None = None, emit: EmitFn = lambda _msg: None,
                 prefix: str = "") -> dict:
    """Create a video job. The endpoint takes a form, not JSON."""
    record = request("POST", path, fields, files=files or {})
    job_id = str(record.get("id") or "") if isinstance(record, dict) else ""
    if not job_id:
        raise ProviderError(200, "OpenAI accepted the video request but returned no job id")
    emit(f"{prefix} 🧾 Job {job_id} accepted ({record.get('status') or 'queued'})")
    return record


def await_video(request: RequestFn, job: dict, *, status_path: str, poll_interval: float,
                timeout: float, emit: EmitFn = lambda _msg: None, prefix: str = "") -> dict:
    job_id = str(job.get("id") or "")
    started = time.monotonic()
    last = str(job.get("status") or "")
    path = status_path.format(id=job_id)
    while True:
        if timeout and time.monotonic() - started > timeout:
            raise ProviderError(
                0,
                f"Video job {job_id} did not finish within {timeout:.0f}s — it keeps "
                f"running at OpenAI; collect it later",
            )
        if poll_interval:
            time.sleep(poll_interval)
        record = request("GET", path)
        status = str(record.get("status") or "")
        if status != last:
            last = status
            emit(f"{prefix} ⏳ Job {status}")
        if not is_terminal(status):
            continue
        if status not in SUCCESS_STATES:
            raise ProviderError(200, _failure(record, job_id))
        emit(f"{prefix} ✅ Job completed")
        return record


def assets_from(record: dict) -> list[dict]:
    """Normalise a finished response into ``{"url": ...}`` or ``{"b64": ...}``.

    A video record carries no file at all — the bytes live behind the content
    path — so it yields an empty list and the caller fetches them.
    """
    assets: list[dict] = []
    data = record.get("data")
    if isinstance(data, list):
        for item in data:
            if not isinstance(item, dict):
                continue
            if item.get("b64_json"):
                assets.append({"b64": str(item["b64_json"])})
            elif item.get("url"):
                assets.append({"url": str(item["url"])})
    output = record.get("output")
    if isinstance(output, list):
        assets.extend({"url": str(value)} for value in output if isinstance(value, str))
    return assets


def _failure(record: dict, job_id: str) -> str:
    error = record.get("error")
    detail = ""
    if isinstance(error, dict):
        detail = str(error.get("message") or error.get("code") or "")
    elif error:
        detail = str(error)
    text = f"Video job {job_id} ended as {record.get('status') or 'failed'}"
    return f"{text} — {detail}" if detail else text
