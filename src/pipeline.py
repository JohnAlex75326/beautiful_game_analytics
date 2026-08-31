from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv

from src.warehouse.pipeline_log import (
    complete_pipeline_run,
    fail_pipeline_run,
    start_pipeline_run,
    update_pipeline_stage,
)


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

COMPETITION_CODE = "PD"


def run_command(
    command: list[str],
    stage: str,
    run_id: str,
) -> None:
    """
    Run a pipeline command and fail immediately
    if the command exits unsuccessfully.
    """

    print()
    print(
        "=" * 70
    )
    print(
        f"STAGE: {stage}"
    )
    print(
        "=" * 70
    )
    print(
        "COMMAND:",
        " ".join(
            command
        ),
    )
    print()

    update_pipeline_stage(
        run_id=run_id,
        stage=stage,
    )

    subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        check=True,
    )


def run_pipeline() -> None:
    """
    Run the complete Beautiful Game Analytics
    production pipeline.

    SportsDB artwork is not refreshed here.
    It is maintained separately as seasonal
    reference data.
    """

    load_dotenv(
        PROJECT_ROOT
        / ".env"
    )

    run_id = (
        uuid4().hex
    )

    started_at = (
        start_pipeline_run(
            run_id=run_id,
            competition_code=(
                COMPETITION_CODE
            ),
        )
    )

    current_stage = (
        "STARTING"
    )

    print()
    print(
        "=" * 70
    )
    print(
        "BEAUTIFUL GAME ANALYTICS"
    )
    print(
        "PIPELINE START"
    )
    print(
        "=" * 70
    )
    print(
        f"Run ID: "
        f"{run_id}"
    )
    print(
        f"Competition: "
        f"{COMPETITION_CODE}"
    )


    try:

        # --------------------------------------------------
        # 1. football-data.org API ingestion
        # --------------------------------------------------

        current_stage = (
            "API_INGESTION"
        )

        run_command(
            [
                sys.executable,
                "-m",
                "src.ingest.football_api",
            ],
            stage=current_stage,
            run_id=run_id,
        )


        # --------------------------------------------------
        # 2. Python transformations
        #
        # Includes joining the committed SportsDB
        # seasonal reference dataset onto dim_team.
        # No SportsDB API request occurs here.
        # --------------------------------------------------

        current_stage = (
            "TRANSFORMATION"
        )

        run_command(
            [
                sys.executable,
                "-m",
                "src.transform.football",
            ],
            stage=current_stage,
            run_id=run_id,
        )


        # --------------------------------------------------
        # 3. DuckDB warehouse
        # --------------------------------------------------

        current_stage = (
            "WAREHOUSE_LOAD"
        )

        run_command(
            [
                sys.executable,
                "-m",
                "src.warehouse.load_duckdb",
            ],
            stage=current_stage,
            run_id=run_id,
        )


        # --------------------------------------------------
        # 4. dbt build
        # --------------------------------------------------

        current_stage = (
            "DBT_BUILD"
        )

        dbt_executable = (
            shutil.which(
                "dbt"
            )
        )

        if dbt_executable is None:

            raise RuntimeError(
                "dbt executable was not found. "
                "Ensure the virtual environment "
                "is active and dbt-duckdb "
                "is installed."
            )

        run_command(
            [
                dbt_executable,
                "build",
                "--project-dir",
                "dbt",
                "--profiles-dir",
                "dbt",
            ],
            stage=current_stage,
            run_id=run_id,
        )


        # --------------------------------------------------
        # Success
        # --------------------------------------------------

        complete_pipeline_run(
            run_id=run_id,
            started_at=(
                started_at
            ),
        )

        print()
        print(
            "=" * 70
        )
        print(
            "PIPELINE SUCCESS"
        )
        print(
            "=" * 70
        )
        print(
            f"Run ID: "
            f"{run_id}"
        )


    except Exception as exc:

        fail_pipeline_run(
            run_id=run_id,
            started_at=(
                started_at
            ),
            failed_stage=(
                current_stage
            ),
            error_message=(
                str(exc)
            ),
        )

        print()
        print(
            "=" * 70
        )
        print(
            "PIPELINE FAILED"
        )
        print(
            "=" * 70
        )
        print(
            f"Run ID: "
            f"{run_id}"
        )
        print(
            f"Failed Stage: "
            f"{current_stage}"
        )
        print(
            f"Error: "
            f"{exc}"
        )

        raise


if __name__ == "__main__":
    run_pipeline()