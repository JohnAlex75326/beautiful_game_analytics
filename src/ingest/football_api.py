import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

from src.config import (
    FOOTBALL_DATA_API_TOKEN,
    FOOTBALL_DATA_BASE_URL,
    RAW_DATA_DIR,
    validate_config,
)


REQUEST_TIMEOUT_SECONDS = 30


def get_headers() -> dict[str, str]:
    """Return authenticated headers for football-data.org."""

    validate_config()

    return {
        "X-Auth-Token": FOOTBALL_DATA_API_TOKEN,
    }


def get_json(endpoint: str) -> dict[str, Any]:
    """
    Make an authenticated GET request to football-data.org
    and return the JSON response.
    """

    url = f"{FOOTBALL_DATA_BASE_URL}{endpoint}"

    response = requests.get(
        url,
        headers=get_headers(),
        timeout=REQUEST_TIMEOUT_SECONDS,
    )

    response.raise_for_status()

    return response.json()


def get_competition(
    competition_code: str,
) -> dict[str, Any]:
    """Fetch competition metadata."""

    return get_json(
        f"/competitions/{competition_code}"
    )


def get_teams(
    competition_code: str,
) -> dict[str, Any]:
    """Fetch teams for a competition."""

    return get_json(
        f"/competitions/{competition_code}/teams"
    )


def get_matches(
    competition_code: str,
) -> dict[str, Any]:
    """Fetch matches for a competition."""

    return get_json(
        f"/competitions/{competition_code}/matches"
    )


def get_standings(
    competition_code: str,
) -> dict[str, Any]:
    """Fetch current standings for a competition."""

    return get_json(
        f"/competitions/{competition_code}/standings"
    )


def get_snapshot_directory(
    competition_code: str,
) -> Path:
    """
    Return the raw snapshot directory for today's UTC date.
    """

    snapshot_date = datetime.now(
        timezone.utc
    ).strftime("%Y-%m-%d")

    snapshot_dir = (
        RAW_DATA_DIR
        / "football_data"
        / competition_code
        / snapshot_date
    )

    snapshot_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    return snapshot_dir


def save_json(
    data: dict[str, Any],
    filepath: Path,
) -> None:
    """Write API response to JSON."""

    with filepath.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False,
        )


def ingest_competition(
    competition_code: str,
) -> None:
    """
    Fetch all MVP football datasets for one competition
    and save them as raw JSON snapshots.
    """

    print(
        f"Starting ingestion for {competition_code}..."
    )

    snapshot_dir = get_snapshot_directory(
        competition_code
    )

    datasets = {
        "competition": get_competition(
            competition_code
        ),
        "teams": get_teams(
            competition_code
        ),
        "matches": get_matches(
            competition_code
        ),
        "standings": get_standings(
            competition_code
        ),
    }

    for dataset_name, dataset in datasets.items():

        filepath = (
            snapshot_dir
            / f"{dataset_name}.json"
        )

        save_json(
            dataset,
            filepath,
        )

        print(
            f"Saved {dataset_name:<12} -> {filepath}"
        )

    print()
    print("Ingestion complete.")


def main() -> None:

    print()
    print("Beautiful Game Analytics")
    print("------------------------")

    ingest_competition("PD")


if __name__ == "__main__":
    main()