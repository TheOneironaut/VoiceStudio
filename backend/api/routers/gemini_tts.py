"""Persistent Gemini TTS batch API."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from api.dependencies import require_admin
from services import gemini_tts_batch
from services.gemini_tts import DEFAULT_VOICE, VOICES

router = APIRouter(prefix="/batch/gemini-tts", tags=["gemini-tts"])


class CreateGeminiBatchRequest(BaseModel):
    text: str = Field(min_length=1)
    voice: str = DEFAULT_VOICE
    instruct: str | None = None
    mode: Literal["immediate", "provider_batch"] = "immediate"
    max_chars: int = Field(default=1800, ge=100, le=8000)


@router.get("/voices")
def voices() -> dict[str, object]:
    return {"default": DEFAULT_VOICE, "voices": list(VOICES)}


@router.get("/jobs", dependencies=[Depends(require_admin)])
def jobs() -> list[dict]:
    return gemini_tts_batch.list_jobs()


@router.post("/jobs", dependencies=[Depends(require_admin)])
def create_job(
    request: CreateGeminiBatchRequest, background_tasks: BackgroundTasks
) -> dict:
    try:
        job = gemini_tts_batch.create_job(
            request.text,
            voice=request.voice,
            instruct=request.instruct,
            mode=request.mode,
            max_chars=request.max_chars,
        )
        if request.mode == "immediate":
            background_tasks.add_task(gemini_tts_batch.run_immediate, job["id"])
        else:
            job = gemini_tts_batch.submit_provider_batch(job["id"])
        return job
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/jobs/{job_id}", dependencies=[Depends(require_admin)])
def get_job(job_id: str, refresh: bool = True) -> dict:
    try:
        job = gemini_tts_batch.load_job(job_id)
        if refresh and job["mode"] == "provider_batch" and job["status"] == "submitted":
            job = gemini_tts_batch.refresh_provider_batch(job_id)
        return job
    except KeyError as exc:
        raise HTTPException(
            status_code=404, detail="Gemini batch job not found."
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/jobs/{job_id}/retry", dependencies=[Depends(require_admin)])
def retry_job(job_id: str, background_tasks: BackgroundTasks) -> dict:
    try:
        job = gemini_tts_batch.load_job(job_id)
        if job["mode"] != "immediate":
            raise ValueError("Only immediate jobs support local retry.")
        background_tasks.add_task(gemini_tts_batch.run_immediate, job_id)
        return job
    except KeyError as exc:
        raise HTTPException(
            status_code=404, detail="Gemini batch job not found."
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/jobs/{job_id}/cancel", dependencies=[Depends(require_admin)])
def cancel_job(job_id: str) -> dict:
    try:
        return gemini_tts_batch.cancel_provider_batch(job_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=404, detail="Gemini batch job not found."
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/jobs/{job_id}/audio", dependencies=[Depends(require_admin)])
def download_audio(job_id: str) -> FileResponse:
    try:
        job = gemini_tts_batch.load_job(job_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=404, detail="Gemini batch job not found."
        ) from exc
    if job["status"] != "completed" or not job["output_file"]:
        raise HTTPException(status_code=409, detail="Gemini batch audio is not ready.")
    path = gemini_tts_batch.JOBS_DIR / job_id / job["output_file"]
    return FileResponse(path, media_type="audio/wav", filename=f"gemini-{job_id}.wav")
