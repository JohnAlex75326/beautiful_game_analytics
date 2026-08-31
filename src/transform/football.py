import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from src.config import (
    PROCESSED_DATA_DIR,
    RAW_DATA_DIR,
    REFERENCE_DATA_DIR,
)


# ============================================================
# Generic helpers
# ============================================================

def get_latest_snapshot_directory(
    competition_code: str,
) -> Path:
    """
    Return the latest raw snapshot directory
    for a competition.
    """

    competition_dir = (
        RAW_DATA_DIR
        / "football_data"
        / competition_code
    )

    if not competition_dir.exists():

        raise FileNotFoundError(
            "No raw data directory found for "
            f"{competition_code}: "
            f"{competition_dir}"
        )

    snapshot_dirs = [
        path
        for path in competition_dir.iterdir()
        if path.is_dir()
    ]

    if not snapshot_dirs:

        raise FileNotFoundError(
            f"No snapshots found for "
            f"{competition_code}"
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


def save_parquet(
    dataframe: pd.DataFrame,
    filepath: Path,
) -> None:
    """
    Write a DataFrame to Parquet.
    """

    filepath.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    dataframe.to_parquet(
        filepath,
        index=False,
    )


# ============================================================
# SportsDB reference data
# ============================================================

def load_sportsdb_reference(
    competition_code: str,
) -> tuple[
    pd.DataFrame,
    Path,
]:
    """
    Load the manually reviewed SportsDB reference
    dataset for a competition.
    """

    reference_path = (
        REFERENCE_DATA_DIR
        / "sportsdb"
        / competition_code
        / "team_badges.json"
    )

    if not reference_path.exists():

        raise FileNotFoundError(
            "SportsDB reference file not found: "
            f"{reference_path}. "
            "Run "
            "'python -m src.ingest.sportsdb_badges' "
            "and review the mappings before running "
            "the normal pipeline."
        )

    payload = load_json(
        reference_path
    )

    reference_competition = (
        payload.get(
            "competition_code"
        )
    )

    if (
        reference_competition
        != competition_code
    ):

        raise ValueError(
            "SportsDB reference competition mismatch. "
            f"Expected {competition_code}, "
            f"received {reference_competition}."
        )

    records = payload.get(
        "teams",
        []
    )

    reference = pd.DataFrame(
        records
    )

    if reference.empty:

        raise ValueError(
            "SportsDB reference file contains "
            "zero team records."
        )

    required_columns = {
        "football_data_team_id",
        "football_data_team_name",
        "sportsdb_team_id",
        "sportsdb_team_name",
        "sportsdb_badge_url",
        "sportsdb_source",
        "sportsdb_resolution_method",
        "sportsdb_fetched_at",
    }

    missing_columns = (
        required_columns
        - set(
            reference.columns
        )
    )

    if missing_columns:

        raise ValueError(
            "SportsDB reference file is missing "
            "required columns: "
            f"{sorted(missing_columns)}"
        )

    reference[
        "football_data_team_id"
    ] = (
        pd.to_numeric(
            reference[
                "football_data_team_id"
            ],
            errors="raise",
        )
        .astype(
            "Int64"
        )
    )

    if (
        reference[
            "football_data_team_id"
        ]
        .duplicated()
        .any()
    ):

        raise ValueError(
            "SportsDB reference contains duplicate "
            "football-data.org team IDs."
        )

    reference[
        "sportsdb_team_id"
    ] = (
        reference[
            "sportsdb_team_id"
        ]
        .astype(
            "string"
        )
    )

    reference[
        "sportsdb_team_name"
    ] = (
        reference[
            "sportsdb_team_name"
        ]
        .astype(
            "string"
        )
    )

    reference[
        "sportsdb_badge_url"
    ] = (
        reference[
            "sportsdb_badge_url"
        ]
        .astype(
            "string"
        )
    )

    reference[
        "sportsdb_source"
    ] = (
        reference[
            "sportsdb_source"
        ]
        .astype(
            "string"
        )
    )

    reference[
        "sportsdb_resolution_method"
    ] = (
        reference[
            "sportsdb_resolution_method"
        ]
        .astype(
            "string"
        )
    )

    reference[
        "sportsdb_fetched_at"
    ] = pd.to_datetime(
        reference[
            "sportsdb_fetched_at"
        ],
        utc=True,
    )

    return (
        reference,
        reference_path,
    )


def enrich_teams_with_reference(
    dim_team: pd.DataFrame,
    competition_code: str,
) -> tuple[
    pd.DataFrame,
    Path,
]:
    """
    Merge the manually approved SportsDB artwork
    reference into the current team dimension.

    The current competition membership and reference
    membership must match exactly.

    This deliberately causes the normal pipeline to fail
    at the beginning of a new season if promoted/relegated
    teams have not yet been reviewed.
    """

    (
        reference,
        reference_path,
    ) = load_sportsdb_reference(
        competition_code
    )

    current_team_ids = set(
        dim_team[
            "team_id"
        ]
        .dropna()
        .astype(int)
        .tolist()
    )

    reference_team_ids = set(
        reference[
            "football_data_team_id"
        ]
        .dropna()
        .astype(int)
        .tolist()
    )

    missing_from_reference = (
        current_team_ids
        - reference_team_ids
    )

    obsolete_reference_teams = (
        reference_team_ids
        - current_team_ids
    )

    if (
        missing_from_reference
        or obsolete_reference_teams
    ):

        missing_names = (
            dim_team.loc[
                dim_team[
                    "team_id"
                ]
                .isin(
                    missing_from_reference
                ),
                "team_name",
            ]
            .tolist()
        )

        raise ValueError(
            "SportsDB seasonal reference does not "
            "match the current competition membership. "
            f"Missing current teams: {missing_names}. "
            "Obsolete reference team IDs: "
            f"{sorted(obsolete_reference_teams)}. "
            "Refresh and manually review the SportsDB "
            "reference dataset for the new season."
        )

    reference_for_merge = (
        reference[
            [
                "football_data_team_id",
                "sportsdb_team_id",
                "sportsdb_team_name",
                "sportsdb_badge_url",
                "sportsdb_source",
                "sportsdb_resolution_method",
                "sportsdb_fetched_at",
            ]
        ]
        .rename(
            columns={
                "football_data_team_id":
                    "team_id",
            }
        )
    )

    enriched = dim_team.merge(
        reference_for_merge,
        on="team_id",
        how="left",
        validate="one_to_one",
    )

    required_enrichment_columns = [
        "sportsdb_team_id",
        "sportsdb_team_name",
        "sportsdb_badge_url",
        "sportsdb_source",
        "sportsdb_resolution_method",
        "sportsdb_fetched_at",
    ]

    missing_enrichment = (
        enriched[
            required_enrichment_columns
        ]
        .isna()
        .any(
            axis=1
        )
    )

    if missing_enrichment.any():

        missing_teams = (
            enriched.loc[
                missing_enrichment,
                "team_name",
            ]
            .tolist()
        )

        raise ValueError(
            "SportsDB reference enrichment is "
            "incomplete for teams: "
            f"{missing_teams}"
        )

    if (
        enriched[
            "sportsdb_team_id"
        ]
        .duplicated()
        .any()
    ):

        raise ValueError(
            "Multiple competition teams resolve to "
            "the same SportsDB team ID."
        )

    invalid_sources = (
        enriched.loc[
            enriched[
                "sportsdb_source"
            ]
            != "TheSportsDB",
            "sportsdb_source",
        ]
        .dropna()
        .unique()
        .tolist()
    )

    if invalid_sources:

        raise ValueError(
            "Unexpected SportsDB reference sources: "
            f"{invalid_sources}"
        )

    return (
        enriched,
        reference_path,
    )


# ============================================================
# Team transformation
# ============================================================

def transform_teams(
    raw_teams: dict[str, Any],
    competition_code: str,
) -> pd.DataFrame:
    """
    Flatten football-data.org team records
    into the base dim_team structure.
    """

    loaded_at = datetime.now(
        timezone.utc
    )

    records = []

    for team in raw_teams.get(
        "teams",
        [],
    ):

        records.append(
            {
                "team_id":
                    team.get(
                        "id"
                    ),

                "team_name":
                    team.get(
                        "name"
                    ),

                "short_name":
                    team.get(
                        "shortName"
                    ),

                "tla":
                    team.get(
                        "tla"
                    ),

                "country":
                    (
                        team.get(
                            "area",
                            {},
                        )
                        .get(
                            "name"
                        )
                    ),

                "venue_name":
                    team.get(
                        "venue"
                    ),

                "founded":
                    team.get(
                        "founded"
                    ),

                "club_colors":
                    team.get(
                        "clubColors"
                    ),

                # Retained as source metadata.
                # The public UI will use the separately
                # reviewed SportsDB badge URL.
                "crest_url":
                    team.get(
                        "crest"
                    ),

                "competition_code":
                    competition_code,

                "loaded_at":
                    loaded_at,
            }
        )

    dataframe = pd.DataFrame(
        records
    )

    if dataframe.empty:

        raise ValueError(
            "Team transformation produced "
            "zero rows."
        )

    if (
        dataframe[
            "team_id"
        ]
        .isna()
        .any()
    ):

        raise ValueError(
            "Null team IDs found."
        )

    dataframe[
        "team_id"
    ] = (
        dataframe[
            "team_id"
        ]
        .astype(
            "Int64"
        )
    )

    if (
        dataframe[
            "team_id"
        ]
        .duplicated()
        .any()
    ):

        duplicate_ids = (
            dataframe.loc[
                dataframe[
                    "team_id"
                ]
                .duplicated(),
                "team_id",
            ]
            .tolist()
        )

        raise ValueError(
            "Duplicate team IDs found: "
            f"{duplicate_ids}"
        )

    return dataframe


# ============================================================
# Match transformation
# ============================================================

def transform_matches(
    raw_matches: dict[str, Any],
    competition_code: str,
    source_snapshot_date: str,
) -> pd.DataFrame:
    """
    Flatten football-data.org match records
    into the fact_match structure.

    Grain:
        One row per match.
    """

    loaded_at = datetime.now(
        timezone.utc
    )

    result_mapping = {
        "HOME_TEAM": "H",
        "AWAY_TEAM": "A",
        "DRAW": "D",
    }

    records = []

    for match in raw_matches.get(
        "matches",
        [],
    ):

        competition = match.get(
            "competition",
            {},
        )

        season = match.get(
            "season",
            {},
        )

        home_team = match.get(
            "homeTeam",
            {},
        )

        away_team = match.get(
            "awayTeam",
            {},
        )

        score = match.get(
            "score",
            {},
        )

        full_time = score.get(
            "fullTime",
            {},
        )

        winner = score.get(
            "winner"
        )

        records.append(
            {
                "match_id":
                    match.get(
                        "id"
                    ),

                "competition_id":
                    competition.get(
                        "id"
                    ),

                "competition_code":
                    competition_code,

                "season_id":
                    season.get(
                        "id"
                    ),

                "matchday":
                    match.get(
                        "matchday"
                    ),

                "stage":
                    match.get(
                        "stage"
                    ),

                "utc_date":
                    match.get(
                        "utcDate"
                    ),

                "status":
                    match.get(
                        "status"
                    ),

                "home_team_id":
                    home_team.get(
                        "id"
                    ),

                "away_team_id":
                    away_team.get(
                        "id"
                    ),

                "home_score":
                    full_time.get(
                        "home"
                    ),

                "away_score":
                    full_time.get(
                        "away"
                    ),

                "result":
                    result_mapping.get(
                        winner
                    ),

                "source_last_updated":
                    match.get(
                        "lastUpdated"
                    ),

                "source_snapshot_date":
                    source_snapshot_date,

                "loaded_at":
                    loaded_at,
            }
        )

    dataframe = pd.DataFrame(
        records
    )

    if dataframe.empty:

        raise ValueError(
            "Match transformation produced "
            "zero rows."
        )

    dataframe[
        "utc_date"
    ] = pd.to_datetime(
        dataframe[
            "utc_date"
        ],
        utc=True,
    )

    dataframe[
        "source_last_updated"
    ] = pd.to_datetime(
        dataframe[
            "source_last_updated"
        ],
        utc=True,
    )

    dataframe[
        "matchday"
    ] = (
        dataframe[
            "matchday"
        ]
        .astype(
            "Int64"
        )
    )

    dataframe[
        "home_score"
    ] = (
        dataframe[
            "home_score"
        ]
        .astype(
            "Int64"
        )
    )

    dataframe[
        "away_score"
    ] = (
        dataframe[
            "away_score"
        ]
        .astype(
            "Int64"
        )
    )

    dataframe[
        "result"
    ] = (
        dataframe[
            "result"
        ]
        .astype(
            "string"
        )
    )

    if (
        dataframe[
            "match_id"
        ]
        .isna()
        .any()
    ):

        raise ValueError(
            "Null match IDs found."
        )

    if (
        dataframe[
            "match_id"
        ]
        .duplicated()
        .any()
    ):

        duplicate_ids = (
            dataframe.loc[
                dataframe[
                    "match_id"
                ]
                .duplicated(),
                "match_id",
            ]
            .tolist()
        )

        raise ValueError(
            "Duplicate match IDs found: "
            f"{duplicate_ids}"
        )

    same_team = (
        dataframe[
            "home_team_id"
        ]
        == dataframe[
            "away_team_id"
        ]
    )

    if same_team.any():

        invalid_matches = (
            dataframe.loc[
                same_team,
                "match_id",
            ]
            .tolist()
        )

        raise ValueError(
            "Home and away team are identical "
            "for matches: "
            f"{invalid_matches}"
        )

    return dataframe


# ============================================================
# Standings transformation
# ============================================================

def transform_standings(
    raw_standings: dict[str, Any],
    competition_code: str,
    source_snapshot_date: str,
) -> pd.DataFrame:
    """
    Flatten football-data.org standings into
    standing snapshot records.

    Grain:
        One team x competition x season x snapshot.
    """

    loaded_at = datetime.now(
        timezone.utc
    )

    competition = (
        raw_standings.get(
            "competition",
            {},
        )
    )

    season = (
        raw_standings.get(
            "season",
            {},
        )
    )

    current_matchday = (
        season.get(
            "currentMatchday"
        )
    )

    records = []

    for standing_group in (
        raw_standings.get(
            "standings",
            [],
        )
    ):

        standing_type = (
            standing_group.get(
                "type"
            )
        )

        # Keep only the overall table.
        if standing_type != "TOTAL":
            continue

        for row in standing_group.get(
            "table",
            [],
        ):

            team = row.get(
                "team",
                {},
            )

            records.append(
                {
                    "competition_id":
                        competition.get(
                            "id"
                        ),

                    "competition_code":
                        competition_code,

                    "season_id":
                        season.get(
                            "id"
                        ),

                    "snapshot_matchday":
                        current_matchday,

                    "snapshot_date":
                        source_snapshot_date,

                    "team_id":
                        team.get(
                            "id"
                        ),

                    "position":
                        row.get(
                            "position"
                        ),

                    "played":
                        row.get(
                            "playedGames"
                        ),

                    "form":
                        row.get(
                            "form"
                        ),

                    "won":
                        row.get(
                            "won"
                        ),

                    "drawn":
                        row.get(
                            "draw"
                        ),

                    "lost":
                        row.get(
                            "lost"
                        ),

                    "points":
                        row.get(
                            "points"
                        ),

                    "goals_for":
                        row.get(
                            "goalsFor"
                        ),

                    "goals_against":
                        row.get(
                            "goalsAgainst"
                        ),

                    "goal_difference":
                        row.get(
                            "goalDifference"
                        ),

                    "loaded_at":
                        loaded_at,
                }
            )

    dataframe = pd.DataFrame(
        records
    )

    if dataframe.empty:

        raise ValueError(
            "Standings transformation produced "
            "zero rows."
        )

    integer_columns = [
        "season_id",
        "snapshot_matchday",
        "team_id",
        "position",
        "played",
        "won",
        "drawn",
        "lost",
        "points",
        "goals_for",
        "goals_against",
        "goal_difference",
    ]

    for column in integer_columns:

        dataframe[
            column
        ] = (
            dataframe[
                column
            ]
            .astype(
                "Int64"
            )
        )

    if (
        dataframe[
            "team_id"
        ]
        .isna()
        .any()
    ):

        raise ValueError(
            "Null team IDs found "
            "in standings."
        )

    if (
        dataframe[
            "team_id"
        ]
        .duplicated()
        .any()
    ):

        duplicate_ids = (
            dataframe.loc[
                dataframe[
                    "team_id"
                ]
                .duplicated(),
                "team_id",
            ]
            .tolist()
        )

        raise ValueError(
            "Duplicate teams found in TOTAL "
            "standings: "
            f"{duplicate_ids}"
        )

    if (
        dataframe[
            "played"
        ]
        != (
            dataframe[
                "won"
            ]
            + dataframe[
                "drawn"
            ]
            + dataframe[
                "lost"
            ]
        )
    ).any():

        raise ValueError(
            "Standings validation failed: "
            "played != won + drawn + lost."
        )

    calculated_goal_difference = (
        dataframe[
            "goals_for"
        ]
        - dataframe[
            "goals_against"
        ]
    )

    if (
        calculated_goal_difference
        != dataframe[
            "goal_difference"
        ]
    ).any():

        raise ValueError(
            "Standings validation failed: "
            "goal_difference does not equal "
            "goals_for - goals_against."
        )

    return dataframe


# ============================================================
# Relationship validation
# ============================================================

def validate_match_team_relationships(
    fact_match: pd.DataFrame,
    dim_team: pd.DataFrame,
) -> None:
    """
    Ensure match team IDs exist in dim_team.
    """

    valid_team_ids = set(
        dim_team[
            "team_id"
        ]
        .dropna()
    )

    match_team_ids = (
        set(
            fact_match[
                "home_team_id"
            ]
            .dropna()
        )
        | set(
            fact_match[
                "away_team_id"
            ]
            .dropna()
        )
    )

    unknown_team_ids = (
        match_team_ids
        - valid_team_ids
    )

    if unknown_team_ids:

        raise ValueError(
            "Matches reference team IDs "
            "missing from dim_team: "
            f"{sorted(unknown_team_ids)}"
        )


def validate_standing_team_relationships(
    standings: pd.DataFrame,
    dim_team: pd.DataFrame,
) -> None:
    """
    Ensure every standings team exists
    in dim_team.
    """

    valid_team_ids = set(
        dim_team[
            "team_id"
        ]
        .dropna()
    )

    standing_team_ids = set(
        standings[
            "team_id"
        ]
        .dropna()
    )

    unknown_team_ids = (
        standing_team_ids
        - valid_team_ids
    )

    if unknown_team_ids:

        raise ValueError(
            "Standings reference team IDs "
            "missing from dim_team: "
            f"{sorted(unknown_team_ids)}"
        )


# ============================================================
# Team processing
# ============================================================

def process_teams(
    competition_code: str,
) -> Path:
    """
    Transform the latest raw team snapshot,
    merge the approved SportsDB reference,
    and write dim_team as Parquet.
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

    dim_team = transform_teams(
        raw_teams,
        competition_code,
    )

    (
        dim_team,
        reference_path,
    ) = enrich_teams_with_reference(
        dim_team,
        competition_code,
    )

    output_path = (
        PROCESSED_DATA_DIR
        / competition_code
        / "dim_team.parquet"
    )

    save_parquet(
        dim_team,
        output_path,
    )

    badge_count = int(
        dim_team[
            "sportsdb_badge_url"
        ]
        .notna()
        .sum()
    )

    print()
    print(
        "Beautiful Game Analytics"
    )
    print(
        "------------------------"
    )
    print(
        f"Source snapshot : "
        f"{snapshot_dir.name}"
    )
    print(
        f"Teams processed : "
        f"{len(dim_team)}"
    )
    print(
        f"Badge coverage  : "
        f"{badge_count}/{len(dim_team)}"
    )
    print(
        f"Reference       : "
        f"{reference_path}"
    )
    print(
        f"Output          : "
        f"{output_path}"
    )

    print()

    print(
        dim_team[
            [
                "team_id",
                "team_name",
                "short_name",
                "tla",
                "sportsdb_team_name",
                "sportsdb_resolution_method",
            ]
        ]
        .to_string(
            index=False
        )
    )

    return output_path


# ============================================================
# Match processing
# ============================================================

def process_matches(
    competition_code: str,
) -> Path:
    """
    Transform the latest raw match snapshot
    and write fact_match as Parquet.
    """

    snapshot_dir = (
        get_latest_snapshot_directory(
            competition_code
        )
    )

    matches_path = (
        snapshot_dir
        / "matches.json"
    )

    raw_matches = load_json(
        matches_path
    )

    fact_match = transform_matches(
        raw_matches=raw_matches,
        competition_code=competition_code,
        source_snapshot_date=(
            snapshot_dir.name
        ),
    )

    dim_team_path = (
        PROCESSED_DATA_DIR
        / competition_code
        / "dim_team.parquet"
    )

    if not dim_team_path.exists():

        raise FileNotFoundError(
            "dim_team.parquet does not exist. "
            "Process teams before matches."
        )

    dim_team = pd.read_parquet(
        dim_team_path
    )

    validate_match_team_relationships(
        fact_match,
        dim_team,
    )

    output_path = (
        PROCESSED_DATA_DIR
        / competition_code
        / "fact_match.parquet"
    )

    save_parquet(
        fact_match,
        output_path,
    )

    completed_matches = int(
        fact_match[
            "status"
        ]
        .eq(
            "FINISHED"
        )
        .sum()
    )

    scheduled_matches = int(
        fact_match[
            "status"
        ]
        .isin(
            [
                "SCHEDULED",
                "TIMED",
            ]
        )
        .sum()
    )

    live_matches = int(
        fact_match[
            "status"
        ]
        .isin(
            [
                "IN_PLAY",
                "PAUSED",
            ]
        )
        .sum()
    )

    other_matches = (
        len(
            fact_match
        )
        - completed_matches
        - scheduled_matches
        - live_matches
    )

    print()
    print(
        "Match Transformation"
    )
    print(
        "--------------------"
    )

    print(
        f"Source snapshot   : "
        f"{snapshot_dir.name}"
    )

    print(
        f"Matches processed : "
        f"{len(fact_match)}"
    )

    print(
        f"Finished matches  : "
        f"{completed_matches}"
    )

    print(
        f"Future matches    : "
        f"{scheduled_matches}"
    )

    print(
        f"Live matches      : "
        f"{live_matches}"
    )

    print(
        f"Other statuses    : "
        f"{other_matches}"
    )

    print(
        f"Output            : "
        f"{output_path}"
    )

    return output_path


# ============================================================
# Standings processing
# ============================================================

def process_standings(
    competition_code: str,
) -> Path:
    """
    Transform the latest raw standings
    snapshot and preserve it as Parquet.
    """

    snapshot_dir = (
        get_latest_snapshot_directory(
            competition_code
        )
    )

    standings_path = (
        snapshot_dir
        / "standings.json"
    )

    raw_standings = load_json(
        standings_path
    )

    fact_standing_snapshot = (
        transform_standings(
            raw_standings=raw_standings,
            competition_code=(
                competition_code
            ),
            source_snapshot_date=(
                snapshot_dir.name
            ),
        )
    )

    dim_team_path = (
        PROCESSED_DATA_DIR
        / competition_code
        / "dim_team.parquet"
    )

    if not dim_team_path.exists():

        raise FileNotFoundError(
            "dim_team.parquet does not exist. "
            "Process teams first."
        )

    dim_team = pd.read_parquet(
        dim_team_path
    )

    validate_standing_team_relationships(
        fact_standing_snapshot,
        dim_team,
    )

    output_path = (
        PROCESSED_DATA_DIR
        / competition_code
        / "standings"
        / f"{snapshot_dir.name}.parquet"
    )

    save_parquet(
        fact_standing_snapshot,
        output_path,
    )

    matchday = (
        fact_standing_snapshot[
            "snapshot_matchday"
        ]
        .iloc[0]
    )

    print()
    print(
        "Standings Transformation"
    )
    print(
        "------------------------"
    )

    print(
        f"Source snapshot  : "
        f"{snapshot_dir.name}"
    )

    print(
        f"Snapshot matchday: "
        f"{matchday}"
    )

    print(
        f"Teams processed  : "
        f"{len(fact_standing_snapshot)}"
    )

    print(
        f"Output           : "
        f"{output_path}"
    )

    return output_path


# ============================================================
# Entry point
# ============================================================

def main() -> None:

    competition_code = "PD"

    print()
    print(
        "Beautiful Game Analytics"
    )
    print(
        "========================"
    )

    process_teams(
        competition_code
    )

    process_matches(
        competition_code
    )

    process_standings(
        competition_code
    )


if __name__ == "__main__":
    main()