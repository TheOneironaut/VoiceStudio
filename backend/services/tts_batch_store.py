"""SQLite persistence for provider-neutral TTS batch jobs."""
from __future__ import annotations

import json
import re
import time
import uuid
from typing import Iterable, Optional

from core.db import db_conn

JOB_STATES = frozenset({"queued", "running", "paused", "completed", "partial", "failed", "cancelled"})
ITEM_STATES = frozenset({"queued", "running", "completed", "failed", "cancelled"})
_SECRET_KEY = re.compile(r"(?:api[_-]?key|token|secret|password|credential)", re.IGNORECASE)


def _validate_settings(settings: dict) -> None:
    def visit(value, path: str = "settings") -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if _SECRET_KEY.search(str(key)):
                    raise ValueError(f"Secrets are not allowed in TTS batch {path}.")
                visit(child, f"{path}.{key}")
        elif isinstance(value, (list, tuple)):
            for child in value:
                visit(child, path)

    visit(settings)
    encoded = json.dumps(settings, sort_keys=True)
    if len(encoded.encode("utf-8")) > 64 * 1024:
        raise ValueError("TTS batch settings exceed 64 KiB.")


def _decode(row) -> Optional[dict]:
    if row is None:
        return None
    result = dict(row)
    for key in ("settings_json", "error_json"):
        value = result.pop(key, None)
        result[key.removesuffix("_json")] = json.loads(value) if value else None
    return result


def create_job(
    *,
    engine_id: str,
    texts: Iterable[str],
    model_id: str | None = None,
    voice_id: str | None = None,
    settings: dict | None = None,
    execution_mode: str = "standard",
    max_attempts: int = 3,
    idempotency_key: str | None = None,
) -> dict:
    if execution_mode not in {"standard", "provider_batch"}:
        raise ValueError("execution_mode must be 'standard' or 'provider_batch'.")
    if max_attempts < 1 or max_attempts > 10:
        raise ValueError("max_attempts must be between 1 and 10.")
    normalized = [text.strip() for text in texts]
    if not normalized or any(not text for text in normalized):
        raise ValueError("A TTS batch requires one or more non-empty items.")
    settings = settings or {}
    _validate_settings(settings)

    now = time.time()
    job_id = uuid.uuid4().hex
    with db_conn() as conn:
        if idempotency_key:
            existing = conn.execute(
                "SELECT id FROM tts_batch_jobs WHERE idempotency_key = ?",
                (idempotency_key,),
            ).fetchone()
            if existing:
                return get_job(existing["id"])
        conn.execute(
            "INSERT INTO tts_batch_jobs "
            "(id, idempotency_key, engine_id, model_id, voice_id, settings_json, "
            "execution_mode, status, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, 'queued', ?, ?)",
            (
                job_id, idempotency_key, engine_id, model_id, voice_id,
                json.dumps(settings, sort_keys=True), execution_mode, now, now,
            ),
        )
        conn.executemany(
            "INSERT INTO tts_batch_items "
            "(id, job_id, position, input_text, max_attempts, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                (uuid.uuid4().hex, job_id, position, text, max_attempts, now, now)
                for position, text in enumerate(normalized)
            ],
        )
    return get_job(job_id)


def get_job(job_id: str, *, include_items: bool = True) -> Optional[dict]:
    with db_conn() as conn:
        row = conn.execute("SELECT * FROM tts_batch_jobs WHERE id = ?", (job_id,)).fetchone()
        items = []
        if row is not None and include_items:
            items = conn.execute(
                "SELECT * FROM tts_batch_items WHERE job_id = ? ORDER BY position",
                (job_id,),
            ).fetchall()
    job = _decode(row)
    if job is not None and include_items:
        job["items"] = [_decode(item) for item in items]
        total = len(job["items"])
        completed = sum(item["status"] == "completed" for item in job["items"])
        job["progress"] = {"completed": completed, "total": total, "fraction": completed / total}
    return job


def list_jobs(*, status: str | None = None, limit: int = 100) -> list[dict]:
    params: list[object] = []
    sql = (
        "SELECT j.*, COUNT(i.id) AS item_total, "
        "COALESCE(SUM(CASE WHEN i.status='completed' THEN 1 ELSE 0 END), 0) "
        "AS item_completed FROM tts_batch_jobs j "
        "LEFT JOIN tts_batch_items i ON i.job_id=j.id"
    )
    if status:
        if status not in JOB_STATES:
            raise ValueError(f"Unknown TTS batch status: {status!r}.")
        sql += " WHERE j.status = ?"
        params.append(status)
    sql += " GROUP BY j.id ORDER BY j.created_at DESC LIMIT ?"
    params.append(max(1, min(limit, 500)))
    with db_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
    jobs = []
    for row in rows:
        job = _decode(row)
        total = job.pop("item_total")
        completed = job.pop("item_completed")
        job["progress"] = {
            "completed": completed,
            "total": total,
            "fraction": completed / total if total else 0,
        }
        jobs.append(job)
    return jobs


def jobs_to_resume() -> list[str]:
    with db_conn() as conn:
        rows = conn.execute(
            "SELECT id FROM tts_batch_jobs WHERE status IN ('queued', 'running') "
            "ORDER BY created_at"
        ).fetchall()
        conn.execute(
            "UPDATE tts_batch_items SET status='queued', updated_at=? WHERE status='running'",
            (time.time(),),
        )
        conn.execute(
            "UPDATE tts_batch_jobs SET status='queued', updated_at=? WHERE status='running'",
            (time.time(),),
        )
    return [row["id"] for row in rows]


def set_job_status(
    job_id: str,
    status: str,
    *,
    error: dict | None = None,
    output_path: str | None = None,
    provider_batch_id: str | None = None,
) -> None:
    if status not in JOB_STATES:
        raise ValueError(f"Unknown TTS batch status: {status!r}.")
    now = time.time()
    finished_at = now if status in {"completed", "partial", "failed", "cancelled"} else None
    with db_conn() as conn:
        cur = conn.execute(
            "UPDATE tts_batch_jobs SET status=?, error_json=?, "
            "output_path=COALESCE(?, output_path), "
            "provider_batch_id=COALESCE(?, provider_batch_id), updated_at=?, finished_at=? "
            "WHERE id=?",
            (
                status, json.dumps(error, sort_keys=True) if error else None,
                output_path, provider_batch_id, now, finished_at, job_id,
            ),
        )
        if not cur.rowcount:
            raise KeyError(job_id)


def set_item_running(item_id: str) -> None:
    with db_conn() as conn:
        conn.execute(
            "UPDATE tts_batch_items SET status='running', attempt_count=attempt_count+1, "
            "error_json=NULL, updated_at=? WHERE id=?",
            (time.time(), item_id),
        )


def set_item_result(
    item_id: str,
    status: str,
    *,
    error: dict | None = None,
    output_path: str | None = None,
    checksum: str | None = None,
    provider_item_id: str | None = None,
) -> None:
    if status not in ITEM_STATES:
        raise ValueError(f"Unknown TTS batch item status: {status!r}.")
    now = time.time()
    finished_at = now if status in {"completed", "failed", "cancelled"} else None
    with db_conn() as conn:
        conn.execute(
            "UPDATE tts_batch_items SET status=?, error_json=?, output_path=?, checksum=?, "
            "provider_item_id=COALESCE(?, provider_item_id), updated_at=?, finished_at=? WHERE id=?",
            (
                status, json.dumps(error, sort_keys=True) if error else None,
                output_path, checksum, provider_item_id, now, finished_at, item_id,
            ),
        )


def cancel_job(job_id: str) -> None:
    set_job_status(job_id, "cancelled")
    with db_conn() as conn:
        conn.execute(
            "UPDATE tts_batch_items SET status='cancelled', updated_at=?, finished_at=? "
            "WHERE job_id=? AND status='queued'",
            (time.time(), time.time(), job_id),
        )


def pause_job(job_id: str) -> None:
    job = get_job(job_id, include_items=False)
    if job is None:
        raise KeyError(job_id)
    if job["status"] not in {"queued", "running"}:
        raise ValueError("Only queued or running TTS batches can be paused.")
    set_job_status(job_id, "paused")


def resume_job(job_id: str) -> None:
    job = get_job(job_id, include_items=False)
    if job is None:
        raise KeyError(job_id)
    if job["status"] != "paused":
        raise ValueError("Only paused TTS batches can be resumed.")
    set_job_status(job_id, "queued")


def retry_failed(job_id: str) -> int:
    job = get_job(job_id, include_items=False)
    if job is None:
        raise KeyError(job_id)
    now = time.time()
    with db_conn() as conn:
        cur = conn.execute(
            "UPDATE tts_batch_items SET status='queued', error_json=NULL, updated_at=?, "
            "finished_at=NULL, provider_item_id=NULL WHERE job_id=? AND status='failed' "
            "AND attempt_count < max_attempts",
            (now, job_id),
        )
        count = cur.rowcount
        if count:
            conn.execute(
                "UPDATE tts_batch_jobs SET status='queued', error_json=NULL, "
                "provider_batch_id=NULL, updated_at=?, finished_at=NULL WHERE id=?",
                (now, job_id),
            )
    return count
