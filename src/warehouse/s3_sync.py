from __future__ import annotations

import os
import threading
import time
from pathlib import Path

import boto3

from src.config import DUCKDB_PATH


S3_BUCKET = os.getenv("S3_BUCKET")

S3_WAREHOUSE_KEY = os.getenv(
    "S3_WAREHOUSE_KEY",
    "warehouse/beautiful_game_analytics.duckdb",
)

AWS_REGION = os.getenv(
    "AWS_REGION",
    "ap-southeast-1",
)

SYNC_INTERVAL_SECONDS = int(
    os.getenv(
        "WAREHOUSE_SYNC_INTERVAL_SECONDS",
        "300",
    )
)


ETAG_PATH = DUCKDB_PATH.parent / ".warehouse_etag"

_SYNC_LOCK = threading.Lock()
_LAST_CHECK_AT = 0.0


def s3_sync_enabled() -> bool:
    """
    Return True when remote warehouse configuration exists.
    """

    return bool(S3_BUCKET)


def _read_local_etag() -> str | None:
    """
    Return the ETag of the locally cached S3 warehouse.
    """

    if not ETAG_PATH.exists():
        return None

    return ETAG_PATH.read_text(
        encoding="utf-8"
    ).strip()


def _write_local_etag(
    etag: str,
) -> None:
    """
    Persist the ETag associated with the local warehouse.
    """

    ETAG_PATH.write_text(
        etag,
        encoding="utf-8",
    )


def ensure_latest_warehouse(
    force: bool = False,
) -> bool:
    """
    Ensure the local DuckDB file matches the latest
    warehouse stored in S3.

    Returns True when a new warehouse was downloaded.
    """

    global _LAST_CHECK_AT

    # Local development mode.
    # If S3 is not configured, keep using the existing
    # local DuckDB file.
    if not s3_sync_enabled():

        if not DUCKDB_PATH.exists():
            raise FileNotFoundError(
                f"DuckDB warehouse not found at "
                f"{DUCKDB_PATH}"
            )

        return False


    current_time = time.monotonic()

    # Avoid hitting S3 on every Streamlit rerun/query.
    if (
        not force
        and DUCKDB_PATH.exists()
        and current_time - _LAST_CHECK_AT
        < SYNC_INTERVAL_SECONDS
    ):
        return False


    with _SYNC_LOCK:

        current_time = time.monotonic()

        if (
            not force
            and DUCKDB_PATH.exists()
            and current_time - _LAST_CHECK_AT
            < SYNC_INTERVAL_SECONDS
        ):
            return False


        s3 = boto3.client(
            "s3",
            region_name=AWS_REGION,
        )


        metadata = s3.head_object(
            Bucket=S3_BUCKET,
            Key=S3_WAREHOUSE_KEY,
        )


        remote_etag = (
            metadata["ETag"]
            .replace('"', "")
        )

        local_etag = _read_local_etag()


        # Already current.
        if (
            DUCKDB_PATH.exists()
            and local_etag == remote_etag
        ):

            _LAST_CHECK_AT = current_time

            return False


        DUCKDB_PATH.parent.mkdir(
            parents=True,
            exist_ok=True,
        )


        temp_path = (
            DUCKDB_PATH.parent
            / "beautiful_game_analytics.download.duckdb"
        )


        try:

            s3.download_file(
                S3_BUCKET,
                S3_WAREHOUSE_KEY,
                str(temp_path),
            )


            if (
                not temp_path.exists()
                or temp_path.stat().st_size == 0
            ):
                raise RuntimeError(
                    "Downloaded warehouse is empty."
                )


            # Atomic replacement:
            # users either see the previous known-good DB
            # or the fully downloaded new DB.
            os.replace(
                temp_path,
                DUCKDB_PATH,
            )


            _write_local_etag(
                remote_etag
            )


            _LAST_CHECK_AT = current_time

            return True


        finally:

            if temp_path.exists():
                temp_path.unlink()

def get_warehouse_sync_status() -> dict:
    """
    Return synchronization metadata for the published
    S3 warehouse and local DuckDB cache.
    """

    status = {
        "s3_enabled": s3_sync_enabled(),
        "bucket": S3_BUCKET,
        "key": S3_WAREHOUSE_KEY,
        "local_path": str(DUCKDB_PATH),
        "local_exists": DUCKDB_PATH.exists(),
        "local_etag": _read_local_etag(),
        "remote_etag": None,
        "remote_last_modified": None,
        "is_current": None,
    }

    if not s3_sync_enabled():
        return status

    s3 = boto3.client(
        "s3",
        region_name=AWS_REGION,
    )

    metadata = s3.head_object(
        Bucket=S3_BUCKET,
        Key=S3_WAREHOUSE_KEY,
    )

    remote_etag = (
        metadata["ETag"]
        .replace('"', "")
    )

    status["remote_etag"] = remote_etag
    status["remote_last_modified"] = metadata[
        "LastModified"
    ]

    status["is_current"] = (
        DUCKDB_PATH.exists()
        and status["local_etag"] == remote_etag
    )

    return status