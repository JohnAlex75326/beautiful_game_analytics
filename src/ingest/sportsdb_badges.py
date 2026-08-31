from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

from src.config import (
    RAW_DATA_DIR,
    REFERENCE_DATA_DIR,
)


# ============================================================
# Configuration
# ============================================================

COMPETITION_CODE = "PD"

SPORTSDB_BASE_URL = (
    "https://www.thesportsdb.com/api/v1/json/123"
)

REQUEST_TIMEOUT_SECONDS = 20

# TheSportsDB free tier is rate limited.
# Because this process runs only once per season,
# being deliberately slow is preferable to hitting 429s.
REQUEST_DELAY_SECONDS = 2.2

SPORTSDB_MAX_RETRIES = 3
SPORTSDB_BACKOFF_SECONDS = 5


# ============================================================
# Known football-data.org -> TheSportsDB mappings
# ============================================================
#
# These mappings were manually verified during the
# 2026/27 La Liga reference-data setup.
#
# New/promoted teams that do not exist here will fall back
# to name search and must be manually reviewed before the
# generated reference file is committed.
#
# Format:
#
# football-data.org team_id : TheSportsDB team_id
#

SPORTSDB_TEAM_ID_MAP: dict[int, str] = {
    77: "133727",     # Athletic Club
    78: "133729",     # Atlético Madrid
    79: "133730",     # Osasuna
    80: "133734",     # Espanyol
    81: "133739",     # Barcelona
    82: "133731",     # Getafe
    84: "133736",     # Málaga
    86: "133738",     # Real Madrid
    87: "133728",     # Rayo Vallecano
    88: "133732",     # Levante
    90: "133722",     # Real Betis
    92: "133724",     # Real Sociedad
    94: "133740",     # Villarreal
    95: "133725",     # Valencia
    263: "134221",    # Deportivo Alavés
    285: "134384",    # Elche
    558: "133937",    # Celta Vigo
    559: "133735",    # Sevilla
    560: "133816",    # Deportivo de A Coruña
    5335: "133726",   # Racing de Santander
}


# Optional search aliases for future teams whose
# football-data.org names do not search cleanly.
#
# Example:
#
# SEARCH_NAME_OVERRIDES = {
#     "Source Team Name": "SportsDB Search Name",
# }
#

SEARCH_NAME_OVERRIDES: dict[str, str] = {}


# ============================================================
# File helpers
# ============================================================

def get_latest_snapshot_directory(
    competition_code: str,
) -> Path:
    """
    Return the latest football-data.org raw
    snapshot directory for a competition.
    """

    competition_dir = (
        RAW_DATA_DIR
        / "football_data"
        / competition_code
    )

    if not competition_dir.exists():

        raise FileNotFoundError(
            "No football-data.org raw directory found "
            f"for {competition_code}: "
            f"{competition_dir}"
        )

    snapshot_dirs = [
        path
        for path in competition_dir.iterdir()
        if path.is_dir()
    ]

    if not snapshot_dirs:

        raise FileNotFoundError(
            "No football-data.org snapshots found "
            f"for {competition_code}."
        )

    return max(
        snapshot_dirs
    )


def load_json(
    filepath: Path,
) -> dict[str, Any]:
    """
    Load a JSON file from disk.
    """

    with filepath.open(
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(
            file
        )


def write_json(
    payload: dict[str, Any],
    filepath: Path,
) -> None:
    """
    Write JSON with consistent formatting.
    """

    filepath.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    filepath.write_text(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


# ============================================================
# SportsDB HTTP helper
# ============================================================

def request_json(
    session: requests.Session,
    endpoint: str,
    params: dict[str, str],
) -> dict[str, Any]:
    """
    Perform a TheSportsDB API request.

    HTTP 429 responses are retried with exponential
    backoff. Other HTTP errors fail immediately.
    """

    url = (
        f"{SPORTSDB_BASE_URL}/{endpoint}"
    )

    for attempt in range(
        SPORTSDB_MAX_RETRIES + 1
    ):

        response = session.get(
            url,
            params=params,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )

        if response.status_code != 429:

            response.raise_for_status()

            return response.json()

        if attempt >= SPORTSDB_MAX_RETRIES:

            response.raise_for_status()

        retry_after_header = (
            response.headers.get(
                "Retry-After"
            )
        )

        if retry_after_header:

            try:

                wait_seconds = float(
                    retry_after_header
                )

            except ValueError:

                wait_seconds = (
                    SPORTSDB_BACKOFF_SECONDS
                    * (2 ** attempt)
                )

        else:

            wait_seconds = (
                SPORTSDB_BACKOFF_SECONDS
                * (2 ** attempt)
            )

        print()
        print(
            "TheSportsDB rate limit reached. "
            f"Retrying in {wait_seconds:.0f}s..."
        )

        time.sleep(
            wait_seconds
        )

    raise RuntimeError(
        "TheSportsDB request retry loop "
        "terminated unexpectedly."
    )


# ============================================================
# SportsDB lookup helpers
# ============================================================

def lookup_team_by_id(
    session: requests.Session,
    sportsdb_team_id: str,
) -> dict[str, Any] | None:
    """
    Retrieve one exact TheSportsDB team by ID.
    """

    payload = request_json(
        session=session,
        endpoint="lookupteam.php",
        params={
            "id": sportsdb_team_id,
        },
    )

    teams = payload.get(
        "teams"
    )

    if not teams:
        return None

    return teams[0]


def search_team(
    session: requests.Session,
    team_name: str,
) -> dict[str, Any] | None:
    """
    Search TheSportsDB for a football team.

    Only Soccer records are accepted.

    This path is primarily intended for newly promoted
    clubs that do not yet exist in SPORTSDB_TEAM_ID_MAP.
    """

    search_name = (
        SEARCH_NAME_OVERRIDES.get(
            team_name,
            team_name,
        )
    )

    payload = request_json(
        session=session,
        endpoint="searchteams.php",
        params={
            "t": search_name,
        },
    )

    teams = payload.get(
        "teams"
    )

    if not teams:
        return None

    soccer_teams = [
        team
        for team in teams
        if team.get(
            "strSport"
        ) == "Soccer"
    ]

    if not soccer_teams:
        return None

    spanish_teams = [
        team
        for team in soccer_teams
        if str(
            team.get(
                "strCountry",
                ""
            )
        ).casefold() == "spain"
    ]

    candidates = (
        spanish_teams
        if spanish_teams
        else soccer_teams
    )

    return candidates[0]


def resolve_team(
    session: requests.Session,
    football_data_team_id: int,
    football_data_team_name: str,
) -> tuple[
    dict[str, Any] | None,
    str,
]:
    """
    Resolve a football-data.org team against TheSportsDB.

    Resolution order:

    1. Known exact SportsDB ID mapping.
    2. Name search fallback.

    The fallback must be manually reviewed before
    committing the annual reference dataset.
    """

    known_sportsdb_id = (
        SPORTSDB_TEAM_ID_MAP.get(
            football_data_team_id
        )
    )

    if known_sportsdb_id:

        team = lookup_team_by_id(
            session=session,
            sportsdb_team_id=(
                known_sportsdb_id
            ),
        )

        return (
            team,
            "ID_OVERRIDE",
        )

    team = search_team(
        session=session,
        team_name=(
            football_data_team_name
        ),
    )

    return (
        team,
        "NAME_SEARCH",
    )


# ============================================================
# Record helper
# ============================================================

def build_reference_record(
    football_data_team_id: int,
    football_data_team_name: str,
    sportsdb_team: dict[str, Any] | None,
    resolution_method: str,
    fetched_at: datetime,
) -> dict[str, Any]:
    """
    Normalize one team reference record.
    """

    if sportsdb_team is None:

        return {
            "football_data_team_id":
                football_data_team_id,

            "football_data_team_name":
                football_data_team_name,

            "sportsdb_team_id":
                None,

            "sportsdb_team_name":
                None,

            "sportsdb_badge_url":
                None,

            "sportsdb_source":
                "TheSportsDB",

            "sportsdb_resolution_method":
                resolution_method,

            "sportsdb_fetched_at":
                fetched_at.isoformat(),
        }

    return {
        "football_data_team_id":
            football_data_team_id,

        "football_data_team_name":
            football_data_team_name,

        "sportsdb_team_id":
            sportsdb_team.get(
                "idTeam"
            ),

        "sportsdb_team_name":
            sportsdb_team.get(
                "strTeam"
            ),

        "sportsdb_badge_url":
            sportsdb_team.get(
                "strBadge"
            ),

        "sportsdb_source":
            "TheSportsDB",

        "sportsdb_resolution_method":
            resolution_method,

        "sportsdb_fetched_at":
            fetched_at.isoformat(),
    }


# ============================================================
# Validation
# ============================================================

def validate_reference_records(
    records: list[dict[str, Any]],
    expected_team_count: int,
) -> None:
    """
    Validate a candidate SportsDB reference dataset.

    The persistent reference file must never be replaced
    with incomplete or ambiguous data.
    """

    if len(records) != expected_team_count:

        raise ValueError(
            "SportsDB reference row count does not "
            "match the football-data.org team count."
        )

    football_team_ids = [
        record[
            "football_data_team_id"
        ]
        for record in records
    ]

    if len(
        set(
            football_team_ids
        )
    ) != len(
        football_team_ids
    ):

        raise ValueError(
            "Duplicate football-data.org team IDs "
            "found in SportsDB reference records."
        )

    missing_team_ids = [
        record[
            "football_data_team_name"
        ]
        for record in records
        if not record.get(
            "sportsdb_team_id"
        )
    ]

    if missing_team_ids:

        raise ValueError(
            "SportsDB team resolution incomplete for: "
            f"{missing_team_ids}"
        )

    missing_badges = [
        record[
            "football_data_team_name"
        ]
        for record in records
        if not record.get(
            "sportsdb_badge_url"
        )
    ]

    if missing_badges:

        raise ValueError(
            "SportsDB badge coverage incomplete for: "
            f"{missing_badges}"
        )

    sportsdb_team_ids = [
        str(
            record[
                "sportsdb_team_id"
            ]
        )
        for record in records
    ]

    if len(
        set(
            sportsdb_team_ids
        )
    ) != len(
        sportsdb_team_ids
    ):

        raise ValueError(
            "Multiple football-data.org teams resolved "
            "to the same TheSportsDB team ID."
        )


# ============================================================
# Annual reference refresh
# ============================================================

def refresh_team_badge_reference(
    competition_code: str,
) -> Path:
    """
    Generate the annual/seasonal SportsDB team badge
    reference dataset.

    This command should normally be run only when the
    competition membership changes for a new season.

    The existing approved reference file is replaced
    only if the new candidate passes full validation.
    """

    snapshot_dir = (
        get_latest_snapshot_directory(
            competition_code
        )
    )

    teams_path = (
        snapshot_dir
        / "teams.json"
    )

    raw_teams = load_json(
        teams_path
    )

    source_teams = raw_teams.get(
        "teams",
        []
    )

    if not source_teams:

        raise ValueError(
            "football-data.org teams.json "
            "contains zero teams."
        )

    football_team_ids = [
        team.get(
            "id"
        )
        for team in source_teams
    ]

    if any(
        team_id is None
        for team_id in football_team_ids
    ):

        raise ValueError(
            "football-data.org teams.json "
            "contains null team IDs."
        )

    if len(
        set(
            football_team_ids
        )
    ) != len(
        football_team_ids
    ):

        raise ValueError(
            "football-data.org teams.json "
            "contains duplicate team IDs."
        )


    fetched_at = datetime.now(
        timezone.utc
    )

    records: list[
        dict[str, Any]
    ] = []

    unresolved: list[str] = []


    print()
    print(
        "Beautiful Game Analytics"
    )
    print(
        "------------------------"
    )
    print(
        "TheSportsDB Seasonal Reference Refresh"
    )
    print()
    print(
        f"Competition      : "
        f"{competition_code}"
    )
    print(
        f"Source snapshot  : "
        f"{snapshot_dir.name}"
    )
    print(
        f"Teams            : "
        f"{len(source_teams)}"
    )
    print()


    with requests.Session() as session:

        for index, team in enumerate(
            source_teams
        ):

            football_data_team_id = int(
                team.get(
                    "id"
                )
            )

            football_data_team_name = str(
                team.get(
                    "name"
                )
            )


            print(
                f"Resolving: "
                f"{football_data_team_name} ... ",
                end="",
                flush=True,
            )


            resolved_team: (
                dict[str, Any]
                | None
            ) = None

            resolution_method = (
                "UNKNOWN"
            )


            try:

                (
                    resolved_team,
                    resolution_method,
                ) = resolve_team(
                    session=session,
                    football_data_team_id=(
                        football_data_team_id
                    ),
                    football_data_team_name=(
                        football_data_team_name
                    ),
                )


            except requests.RequestException as exc:

                print(
                    f"ERROR ({exc})"
                )

                unresolved.append(
                    football_data_team_name
                )


            if resolved_team is None:

                if (
                    football_data_team_name
                    not in unresolved
                ):

                    print(
                        "NOT FOUND"
                    )

                    unresolved.append(
                        football_data_team_name
                    )

            else:

                sportsdb_team_id = (
                    resolved_team.get(
                        "idTeam"
                    )
                )

                sportsdb_team_name = (
                    resolved_team.get(
                        "strTeam"
                    )
                )

                sportsdb_sport = (
                    resolved_team.get(
                        "strSport"
                    )
                )

                badge_url = (
                    resolved_team.get(
                        "strBadge"
                    )
                )


                if sportsdb_sport != "Soccer":

                    print(
                        "REJECTED -> "
                        f"{sportsdb_team_name} "
                        f"[{sportsdb_team_id}] "
                        f"is {sportsdb_sport}"
                    )

                    unresolved.append(
                        football_data_team_name
                    )

                    resolved_team = None

                elif not badge_url:

                    print(
                        "FOUND — NO BADGE -> "
                        f"{sportsdb_team_name} "
                        f"[{sportsdb_team_id}] "
                        f"via {resolution_method}"
                    )

                    unresolved.append(
                        football_data_team_name
                    )

                else:

                    print(
                        "FOUND -> "
                        f"{sportsdb_team_name} "
                        f"[{sportsdb_team_id}] "
                        f"via {resolution_method}"
                    )


            records.append(
                build_reference_record(
                    football_data_team_id=(
                        football_data_team_id
                    ),
                    football_data_team_name=(
                        football_data_team_name
                    ),
                    sportsdb_team=(
                        resolved_team
                    ),
                    resolution_method=(
                        resolution_method
                    ),
                    fetched_at=(
                        fetched_at
                    ),
                )
            )


            # Keep the free-tier API comfortably below
            # its burst/rate threshold.
            if index < (
                len(source_teams) - 1
            ):

                time.sleep(
                    REQUEST_DELAY_SECONDS
                )


    # --------------------------------------------------
    # Candidate audit snapshot
    # --------------------------------------------------

    resolved_count = sum(
        1
        for record in records
        if record.get(
            "sportsdb_team_id"
        )
    )

    badge_count = sum(
        1
        for record in records
        if record.get(
            "sportsdb_badge_url"
        )
    )

    candidate_payload = {
        "competition_code":
            competition_code,

        "source_snapshot_date":
            snapshot_dir.name,

        "refreshed_at":
            fetched_at.isoformat(),

        "team_count":
            len(source_teams),

        "resolved_count":
            resolved_count,

        "badge_count":
            badge_count,

        "teams":
            records,
    }


    candidate_path = (
        RAW_DATA_DIR
        / "sportsdb"
        / competition_code
        / snapshot_dir.name
        / "team_badges_candidate.json"
    )

    write_json(
        candidate_payload,
        candidate_path,
    )


    print()
    print(
        "SportsDB Reference Summary"
    )
    print(
        "--------------------------"
    )
    print(
        f"Teams               : "
        f"{len(source_teams)}"
    )
    print(
        f"Teams resolved      : "
        f"{resolved_count}/{len(source_teams)}"
    )
    print(
        f"Badges resolved     : "
        f"{badge_count}/{len(source_teams)}"
    )
    print(
        f"Candidate snapshot  : "
        f"{candidate_path}"
    )


    if unresolved:

        print()
        print(
            "Teams requiring review:"
        )

        for team_name in unresolved:

            print(
                f"  - {team_name}"
            )


    # --------------------------------------------------
    # Strong validation BEFORE persistent replacement
    # --------------------------------------------------

    validate_reference_records(
        records=records,
        expected_team_count=(
            len(source_teams)
        ),
    )


    # --------------------------------------------------
    # Publish approved candidate locally
    # --------------------------------------------------

    reference_path = (
        REFERENCE_DATA_DIR
        / "sportsdb"
        / competition_code
        / "team_badges.json"
    )

    reference_payload = {
        "competition_code":
            competition_code,

        "source_snapshot_date":
            snapshot_dir.name,

        "refreshed_at":
            fetched_at.isoformat(),

        "team_count":
            len(source_teams),

        "badge_count":
            badge_count,

        "teams":
            records,
    }


    reference_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = (
        reference_path.with_suffix(
            ".json.tmp"
        )
    )

    write_json(
        reference_payload,
        temporary_path,
    )

    temporary_path.replace(
        reference_path
    )


    print()
    print(
        "SportsDB reference validation: PASSED"
    )
    print(
        f"Reference file       : "
        f"{reference_path}"
    )
    print()
    print(
        "IMPORTANT: Review all resolved club identities "
        "before committing this reference file to Git."
    )
    print()


    return reference_path


# ============================================================
# Entry point
# ============================================================

def main() -> None:
    """
    Refresh La Liga SportsDB reference data.
    """

    refresh_team_badge_reference(
        COMPETITION_CODE
    )


if __name__ == "__main__":
    main()