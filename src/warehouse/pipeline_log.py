from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

import duckdb

from src.config import DUCKDB_PATH


def _utc_now() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc)


def ensure_pipeline_log_table() -> None:
    """Create the pipeline run log table if it does not exist."""

    DUCKDB_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with duckdb.connect(str(DUCKDB_PATH)) as connection:

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS main.pipeline_run_log (
                run_id VARCHAR PRIMARY KEY,
                competition_code VARCHAR,
                started_at TIMESTAMPTZ NOT NULL,
                finished_at TIMESTAMPTZ,
                status VARCHAR NOT NULL,
                current_stage VARCHAR,
                failed_stage VARCHAR,
                duration_seconds DOUBLE,
                error_message VARCHAR
            )
            """
        )


def start_pipeline_run(
    run_id: str,
    competition_code: str,
) -> datetime:
    """Insert a new RUNNING pipeline record."""

    ensure_pipeline_log_table()

    started_at = _utc_now()

    with duckdb.connect(str(DUCKDB_PATH)) as connection:

        connection.execute(
            """
            INSERT INTO main.pipeline_run_log (
                run_id,
                competition_code,
                started_at,
                status,
                current_stage
            )
            VALUES (?, ?, ?, 'RUNNING', 'STARTING')
            """,
            [
                run_id,
                competition_code,
                started_at,
            ],
        )

    return started_at


def update_pipeline_stage(
    run_id: str,
    stage: str,
) -> None:
    """Update the currently executing pipeline stage."""

    with duckdb.connect(str(DUCKDB_PATH)) as connection:

        connection.execute(
            """
            UPDATE main.pipeline_run_log

            SET current_stage = ?

            WHERE run_id = ?
            """,
            [
                stage,
                run_id,
            ],
        )


def complete_pipeline_run(
    run_id: str,
    started_at: datetime,
) -> None:
    """Mark the pipeline run as successful."""

    finished_at = _utc_now()

    duration_seconds = (
        finished_at - started_at
    ).total_seconds()

    with duckdb.connect(str(DUCKDB_PATH)) as connection:

        connection.execute(
            """
            UPDATE main.pipeline_run_log

            SET
                finished_at = ?,
                status = 'SUCCESS',
                current_stage = 'COMPLETE',
                duration_seconds = ?

            WHERE run_id = ?
            """,
            [
                finished_at,
                duration_seconds,
                run_id,
            ],
        )


def fail_pipeline_run(
    run_id: str,
    started_at: datetime,
    failed_stage: str,
    error_message: Optional[str],
) -> None:
    """Mark the pipeline run as failed."""

    finished_at = _utc_now()

    duration_seconds = (
        finished_at - started_at
    ).total_seconds()

    with duckdb.connect(str(DUCKDB_PATH)) as connection:

        connection.execute(
            """
            UPDATE main.pipeline_run_log

            SET
                finished_at = ?,
                status = 'FAILED',
                current_stage = 'FAILED',
                failed_stage = ?,
                duration_seconds = ?,
                error_message = ?

            WHERE run_id = ?
            """,
            [
                finished_at,
                failed_stage,
                duration_seconds,
                error_message,
                run_id,
            ],
        )