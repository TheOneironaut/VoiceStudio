"""Provider-neutral durable TTS batch jobs.

Revision ID: 0011_tts_batch_jobs
Revises: 0010_remote_worker_schema
"""
from typing import Sequence, Union

from alembic import op


revision: str = "0011_tts_batch_jobs"
down_revision: Union[str, None] = "0010_remote_worker_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS tts_batch_jobs (
            id TEXT PRIMARY KEY, idempotency_key TEXT, engine_id TEXT NOT NULL,
            model_id TEXT, voice_id TEXT, settings_json TEXT NOT NULL DEFAULT '{}',
            execution_mode TEXT NOT NULL DEFAULT 'standard',
            status TEXT NOT NULL DEFAULT 'queued', provider_batch_id TEXT,
            output_path TEXT, error_json TEXT, created_at REAL NOT NULL,
            updated_at REAL NOT NULL, finished_at REAL
        )
    """)
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_tts_batch_jobs_idem "
        "ON tts_batch_jobs(idempotency_key) WHERE idempotency_key IS NOT NULL"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_tts_batch_jobs_status "
        "ON tts_batch_jobs(status, created_at)"
    )
    op.execute("""
        CREATE TABLE IF NOT EXISTS tts_batch_items (
            id TEXT PRIMARY KEY, job_id TEXT NOT NULL, position INTEGER NOT NULL,
            input_text TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'queued',
            attempt_count INTEGER NOT NULL DEFAULT 0,
            max_attempts INTEGER NOT NULL DEFAULT 3, error_json TEXT,
            output_path TEXT, checksum TEXT, provider_item_id TEXT,
            created_at REAL NOT NULL, updated_at REAL NOT NULL, finished_at REAL,
            FOREIGN KEY (job_id) REFERENCES tts_batch_jobs(id) ON DELETE CASCADE,
            UNIQUE (job_id, position)
        )
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_tts_batch_items_job_status "
        "ON tts_batch_items(job_id, status, position)"
    )


def downgrade() -> None:
    op.drop_table("tts_batch_items")
    op.drop_table("tts_batch_jobs")

