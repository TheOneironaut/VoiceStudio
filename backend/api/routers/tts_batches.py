"""Provider-neutral durable TTS batch API."""
from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

from api.dependencies import require_desktop
from services import tts_batch_runner, tts_batch_store
from services.tts_backend import get_backend_class

router = APIRouter(prefix="/tts/batches", tags=["tts-batches"])


class TTSBatchItemRequest(BaseModel):
    text: str = Field(min_length=1, max_length=100_000)

    @field_validator("text")
    @classmethod
    def text_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("text must not be blank")
        return value


class TTSBatchCreateRequest(BaseModel):
    engine_id: str = Field(min_length=1, max_length=100)
    model_id: str | None = Field(default=None, max_length=200)
    voice_id: str | None = Field(default=None, max_length=200)
    settings: dict[str, Any] = Field(default_factory=dict)
    execution_mode: Literal["standard", "provider_batch"] = "standard"
    max_attempts: int = Field(default=3, ge=1, le=10)
    idempotency_key: str | None = Field(default=None, min_length=1, max_length=200)
    items: list[TTSBatchItemRequest] = Field(min_length=1, max_length=5_000)


def _job_or_404(job_id: str) -> dict:
    job = tts_batch_store.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="TTS batch job not found.")
    return job


@router.post("", dependencies=[Depends(require_desktop)], status_code=202)
async def create_tts_batch(request: TTSBatchCreateRequest):
    try:
        backend_cls = get_backend_class(request.engine_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if request.execution_mode == "provider_batch" and not backend_cls.supports_provider_batch:
        raise HTTPException(
            status_code=422,
            detail=f"TTS engine {request.engine_id!r} does not support provider batch execution.",
        )
    job = tts_batch_store.create_job(
        engine_id=request.engine_id,
        texts=[item.text for item in request.items],
        model_id=request.model_id or backend_cls.default_model_id,
        voice_id=request.voice_id or backend_cls.default_voice_id,
        settings=request.settings,
        execution_mode=request.execution_mode,
        max_attempts=request.max_attempts,
        idempotency_key=request.idempotency_key,
    )
    tts_batch_runner.schedule(job["id"])
    return job


@router.get("")
def list_tts_batches(
    status: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
):
    try:
        return tts_batch_store.list_jobs(status=status, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{job_id}")
def get_tts_batch(job_id: str):
    return _job_or_404(job_id)


@router.post("/{job_id}/pause", dependencies=[Depends(require_desktop)])
def pause_tts_batch(job_id: str):
    _job_or_404(job_id)
    try:
        tts_batch_store.pause_job(job_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return tts_batch_store.get_job(job_id)


@router.post("/{job_id}/resume", dependencies=[Depends(require_desktop)], status_code=202)
async def resume_tts_batch(job_id: str):
    _job_or_404(job_id)
    try:
        tts_batch_store.resume_job(job_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    tts_batch_runner.schedule(job_id)
    return tts_batch_store.get_job(job_id)


@router.post("/{job_id}/cancel", dependencies=[Depends(require_desktop)])
def cancel_tts_batch(job_id: str):
    _job_or_404(job_id)
    tts_batch_store.cancel_job(job_id)
    return tts_batch_store.get_job(job_id)


@router.post("/{job_id}/retry-failed", dependencies=[Depends(require_desktop)], status_code=202)
async def retry_failed_tts_batch(job_id: str):
    _job_or_404(job_id)
    count = tts_batch_store.retry_failed(job_id)
    if not count:
        raise HTTPException(status_code=409, detail="No failed TTS batch items can be retried.")
    tts_batch_runner.schedule(job_id)
    return {"retried": count, "job": tts_batch_store.get_job(job_id)}

