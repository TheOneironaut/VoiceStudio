"""Crash-resumable execution for provider-neutral TTS batch jobs."""
from __future__ import annotations

import asyncio
import functools
import hashlib
import random
import re
from pathlib import Path

from core.config import OUTPUTS_DIR
from core.failure import sanitize
from services import tts_batch_store as store
from services.plugin_sdk import ProviderBatchItem, TTSProviderError

_TASKS: dict[str, asyncio.Task] = {}
_SAFE_ID = re.compile(r"^[a-f0-9]{32}$")


def _relative_item_path(job_id: str, position: int) -> str:
    if not _SAFE_ID.fullmatch(job_id):
        raise ValueError("Invalid TTS batch id.")
    return f"tts_batches/{job_id}/item_{position:06d}.wav"


def _absolute_output(relative_path: str) -> Path:
    root = Path(OUTPUTS_DIR).resolve()
    output = (root / relative_path).resolve()
    if root != output and root not in output.parents:
        raise ValueError("TTS batch output path escapes the output directory.")
    return output


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _save_wav(path: str, audio, sample_rate: int) -> None:
    from services.audio_io import atomic_save_wav

    atomic_save_wav(path, audio, sample_rate)


async def _mark_audio(audio, sample_rate: int):
    from services.watermark import mark_synthetic_async

    return await mark_synthetic_async(
        audio,
        sample_rate,
        context="tts_batch.item",
    )


def _load_wav(path: str):
    import torchaudio

    return torchaudio.load(path)


def _resample(audio, source_rate: int, target_rate: int):
    import torchaudio.functional as audio_functional

    return audio_functional.resample(audio, source_rate, target_rate)


def _valid_completed_item(item: dict) -> bool:
    if item["status"] != "completed" or not item.get("output_path") or not item.get("checksum"):
        return False
    path = _absolute_output(item["output_path"])
    return path.is_file() and _sha256(path) == item["checksum"]


def _normalized_error(exc: BaseException) -> dict:
    if isinstance(exc, TTSProviderError):
        code = exc.code
        retryable = exc.retryable
        retry_after_s = exc.retry_after_s
    elif isinstance(exc, (TimeoutError, ConnectionError)):
        code, retryable, retry_after_s = "network", True, None
    else:
        code, retryable, retry_after_s = "generation_failed", False, None
    return {
        "code": code,
        "message": sanitize(str(exc)) or code,
        "retryable": retryable,
        "retry_after_s": retry_after_s,
    }


def _generation_settings(job: dict) -> dict:
    excluded = {"concurrency", "join_gap_ms", "provider_poll_interval_s"}
    return {key: value for key, value in (job.get("settings") or {}).items() if key not in excluded}


def _get_backend_class(engine_id: str):
    from services.tts_backend import get_backend_class

    return get_backend_class(engine_id)


def _get_engine_instance(engine_id: str):
    from services.tts_backend import get_engine_instance_for

    return get_engine_instance_for(engine_id)


def _load_backend(job: dict):
    cls = _get_backend_class(job["engine_id"])
    ok, reason = cls.is_available()
    if not ok:
        raise TTSProviderError(
            f"TTS engine {job['engine_id']!r} is unavailable: {reason}",
            code="engine_unavailable",
        )
    backend = _get_engine_instance(job["engine_id"])
    if job["execution_mode"] == "provider_batch" and not backend.supports_provider_batch:
        raise TTSProviderError(
            f"TTS engine {job['engine_id']!r} does not support provider batch execution.",
            code="unsupported_execution_mode",
        )
    return backend


async def _write_audio(item: dict, audio, sample_rate: int) -> None:
    from worker.async_utils import to_thread_and_drain_on_cancel

    audio = await _mark_audio(audio, sample_rate)
    relative = _relative_item_path(item["job_id"], item["position"])
    output = _absolute_output(relative)
    output.parent.mkdir(parents=True, exist_ok=True)
    await to_thread_and_drain_on_cancel(_save_wav, str(output), audio, sample_rate)
    checksum = await to_thread_and_drain_on_cancel(_sha256, output)
    store.set_item_result(
        item["id"], "completed", output_path=relative, checksum=checksum
    )


async def _generate_standard_item(job: dict, backend, item: dict) -> None:
    while True:
        current = store.get_job(job["id"])
        if current is None or current["status"] in {"paused", "cancelled"}:
            return
        latest = next(row for row in current["items"] if row["id"] == item["id"])
        if _valid_completed_item(latest):
            return
        if latest["status"] == "completed":
            store.set_item_result(latest["id"], "queued")
        if latest["attempt_count"] >= latest["max_attempts"]:
            return

        store.set_item_running(latest["id"])
        try:
            generate = functools.partial(
                backend.generate,
                latest["input_text"],
                voice_id=job.get("voice_id"),
                model_id=job.get("model_id"),
                **_generation_settings(job),
            )
            if backend.is_local:
                from services.model_manager import (
                    generate_timeout_s,
                    run_on_gpu_pool_guarded,
                )
                from worker.async_utils import drain_task

                generation_task = asyncio.create_task(
                    run_on_gpu_pool_guarded(
                        generate,
                        what="TTS batch generate",
                        timeout=generate_timeout_s(
                            latest["input_text"], engine=backend
                        ),
                    )
                )
                try:
                    audio = await asyncio.shield(generation_task)
                except asyncio.CancelledError:
                    # Local inference cannot be stopped safely once it owns the
                    # shared GPU worker. Drain it before shutdown unloads the
                    # model; the item is requeued by the outer handler.
                    await drain_task(generation_task)
                    raise
            else:
                from worker.async_utils import to_thread_and_drain_on_cancel

                audio = await to_thread_and_drain_on_cancel(generate)
            await _write_audio(latest, audio, backend.sample_rate)
            return
        except asyncio.CancelledError:
            store.set_item_result(latest["id"], "queued")
            raise
        except Exception as exc:  # noqa: BLE001 - normalized at provider boundary
            error = _normalized_error(exc)
            refreshed = store.get_job(job["id"])
            refreshed_item = next(row for row in refreshed["items"] if row["id"] == item["id"])
            can_retry = error["retryable"] and refreshed_item["attempt_count"] < refreshed_item["max_attempts"]
            store.set_item_result(latest["id"], "queued" if can_retry else "failed", error=error)
            if not can_retry:
                return
            delay = error["retry_after_s"]
            if delay is None:
                delay = min(30.0, 2 ** max(0, refreshed_item["attempt_count"] - 1))
                delay += random.uniform(0, delay * 0.2)
            await asyncio.sleep(max(0.0, float(delay)))


async def _run_standard(job: dict, backend) -> None:
    requested = int((job.get("settings") or {}).get("concurrency", 1))
    concurrency = max(1, min(requested, 8)) if not backend.is_local else 1
    semaphore = asyncio.Semaphore(concurrency)

    async def run(item: dict) -> None:
        async with semaphore:
            await _generate_standard_item(job, backend, item)

    await asyncio.gather(*(run(item) for item in job["items"] if item["status"] != "cancelled"))


async def _run_provider_batch(job: dict, backend) -> None:
    from worker.async_utils import to_thread_and_drain_on_cancel

    provider_batch_id = job.get("provider_batch_id")
    pending = [item for item in job["items"] if not _valid_completed_item(item)]
    if not pending:
        return
    if not provider_batch_id:
        request_items = [ProviderBatchItem(id=item["id"], text=item["input_text"]) for item in pending]
        submit = functools.partial(
            backend.submit_provider_batch,
            request_items,
            voice_id=job.get("voice_id"),
            model_id=job.get("model_id"),
            **_generation_settings(job),
        )
        provider_batch_id = await to_thread_and_drain_on_cancel(submit)
        store.set_job_status(job["id"], "running", provider_batch_id=provider_batch_id)
        for item in pending:
            store.set_item_running(item["id"])

    poll_interval = max(1.0, min(float((job.get("settings") or {}).get("provider_poll_interval_s", 10)), 300.0))
    poll_failures = 0
    max_poll_failures = min(item["max_attempts"] for item in pending)
    while True:
        current = store.get_job(job["id"])
        if current["status"] == "paused":
            return
        if current["status"] == "cancelled":
            await to_thread_and_drain_on_cancel(
                backend.cancel_provider_batch, provider_batch_id
            )
            return
        try:
            poll_request = functools.partial(
                backend.poll_provider_batch,
                provider_batch_id,
                item_ids=tuple(item["id"] for item in pending),
            )
            poll = await to_thread_and_drain_on_cancel(poll_request)
            poll_failures = 0
        except Exception as exc:  # noqa: BLE001 - provider errors are normalized below
            error = _normalized_error(exc)
            poll_failures += 1
            if not error["retryable"] or poll_failures >= max_poll_failures:
                raise
            delay = error["retry_after_s"]
            if delay is None:
                delay = min(30.0, 2 ** (poll_failures - 1))
            await asyncio.sleep(max(0.0, float(delay)))
            continue
        if poll.status in {"queued", "running"}:
            await asyncio.sleep(poll_interval)
            continue
        if poll.status == "cancelled":
            store.cancel_job(job["id"])
            return
        if poll.status == "failed":
            error = poll.error or {"code": "provider_batch_failed", "message": "Provider batch failed."}
            for item in pending:
                store.set_item_result(item["id"], "failed", error=error)
            return

        by_id = {result.id: result for result in poll.results}
        for item in pending:
            result = by_id.get(item["id"])
            if result is None or result.error or result.audio is None:
                error = result.error if result else {
                    "code": "missing_provider_result",
                    "message": "Provider batch returned no result for this item.",
                }
                store.set_item_result(item["id"], "failed", error=error)
                continue
            from services.tts_backend import _decode_plugin_audio

            audio = _decode_plugin_audio(result.audio)
            await _write_audio(item, audio, result.audio.sample_rate)
        return


async def _join_completed(job: dict, backend) -> str | None:
    from worker.async_utils import to_thread_and_drain_on_cancel

    completed = [item for item in job["items"] if _valid_completed_item(item)]
    if not completed:
        return None
    import torch
    pieces = []
    gap_ms = max(0, min(int((job.get("settings") or {}).get("join_gap_ms", 0)), 60_000))
    for index, item in enumerate(completed):
        audio, sample_rate = await to_thread_and_drain_on_cancel(
            _load_wav, str(_absolute_output(item["output_path"]))
        )
        if sample_rate != backend.sample_rate:
            audio = _resample(audio, sample_rate, backend.sample_rate)
        pieces.append(audio)
        if gap_ms and index < len(completed) - 1:
            pieces.append(torch.zeros((audio.shape[0], int(backend.sample_rate * gap_ms / 1000))))
    joined = torch.cat(pieces, dim=-1)
    relative = f"tts_batches/{job['id']}/joined.wav"
    output = _absolute_output(relative)
    await to_thread_and_drain_on_cancel(
        _save_wav, str(output), joined, backend.sample_rate
    )
    return relative


async def run_job(job_id: str) -> None:
    try:
        job = store.get_job(job_id)
        if job is None or job["status"] in {"paused", "cancelled", "completed"}:
            return
        backend = _load_backend(job)
        store.set_job_status(job_id, "running")
        if job["execution_mode"] == "provider_batch":
            await _run_provider_batch(job, backend)
        else:
            await _run_standard(job, backend)

        final = store.get_job(job_id)
        if final["status"] in {"paused", "cancelled"}:
            return
        completed = sum(item["status"] == "completed" for item in final["items"])
        failed = sum(item["status"] == "failed" for item in final["items"])
        joined_path = await _join_completed(final, backend) if completed else None
        if completed == len(final["items"]):
            status = "completed"
        elif completed:
            status = "partial"
        else:
            status = "failed"
        error = {"code": "items_failed", "count": failed} if failed else None
        store.set_job_status(job_id, status, error=error, output_path=joined_path)
    except asyncio.CancelledError:
        raise
    except Exception as exc:  # noqa: BLE001 - keep one bad provider isolated
        store.set_job_status(job_id, "failed", error=_normalized_error(exc))


def schedule(job_id: str) -> asyncio.Task:
    existing = _TASKS.get(job_id)
    if existing is not None and not existing.done():
        return existing
    task = asyncio.create_task(run_job(job_id), name=f"tts-batch-{job_id}")
    _TASKS[job_id] = task
    task.add_done_callback(lambda _task: _TASKS.pop(job_id, None))
    return task


def resume_pending() -> list[str]:
    job_ids = store.jobs_to_resume()
    for job_id in job_ids:
        schedule(job_id)
    return job_ids


async def shutdown() -> None:
    tasks = [task for task in _TASKS.values() if not task.done()]
    for task in tasks:
        task.cancel()
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)
    _TASKS.clear()
