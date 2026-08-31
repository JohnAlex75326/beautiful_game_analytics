import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from src.config import (
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
)


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
            f"No raw data directory found for "
            f"{competition_code}: {competition_dir}"
        )

    snapshot_dirs = [
        path
        for path in competition_dir.iterdir()
        if path.is_dir()
    ]

    if not snapshot_dirs:
        raise FileNotFoundError(
            f"No snapshots found for {competition_code}"
        )

    return max(snapshot_dirs)


def load_json(
    filepath: Path,
) -> dict[str, Any]:
    """Load a JSON file from disk."""

    with filepath.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def transform_teams(
    raw_teams: dict[str, Any],
    competition_code: str,
) -> pd.DataFrame:
    """
    Flatten football-data.org team records
    into the dim_team structure.
    """

    loaded_at = datetime.now(
        timezone.utc
    )

    records = []

    for team in raw_teams.get("teams", []):

        records.append(
            {
                "team_id": team.get("id"),
                "team_name": team.get("name"),
                "short_name": team.get("shortName"),
                "tla": team.get("tla"),
                "country": (
                    team.get("area", {})
                    .get("name")
                ),
                "venue_name": team.get("venue"),
                "founded": team.get("founded"),
                "club_colors": team.get("clubColors"),
                "crest_url": team.get("crest"),
                "competition_code": competition_code,
                "loaded_at": loaded_at,
            }
        )

    dataframe = pd.DataFrame(records)

    if dataframe.empty:
        raise ValueError(
            "Team transformation produced zero rows."
        )

    if dataframe["team_id"].duplicated().any():
        duplicate_ids = (
            dataframe.loc[
                dataframe["team_id"].duplicated(),
                "team_id",
            ]
            .tolist()
        )

        raise ValueError(
            f"Duplicate team IDs found: {duplicate_ids}"
        )

    return dataframe

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

    for match in raw_matches.get("matches", []):

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
                "match_id": match.get("id"),
                "competition_id": competition.get("id"),
                "competition_code": competition_code,
                "season_id": season.get("id"),
                "matchday": match.get("matchday"),
                "stage": match.get("stage"),
                "utc_date": match.get("utcDate"),
                "status": match.get("status"),
                "home_team_id": home_team.get("id"),
                "away_team_id": away_team.get("id"),
                "home_score": full_time.get("home"),
                "away_score": full_time.get("away"),
                "result": result_mapping.get(winner),
                "source_last_updated": match.get(
                    "lastUpdated"
                ),
                "source_snapshot_date": (
                    source_snapshot_date
                ),
                "loaded_at": loaded_at,
            }
        )

    dataframe = pd.DataFrame(records)

    if dataframe.empty:
        raise ValueError(
            "Match transformation produced zero rows."
        )

    # -----------------------------
    # Data types
    # -----------------------------

    dataframe["utc_date"] = pd.to_datetime(
        dataframe["utc_date"],
        utc=True,
    )

    dataframe["source_last_updated"] = (
        pd.to_datetime(
            dataframe["source_last_updated"],
            utc=True,
        )
    )

    dataframe["matchday"] = (
        dataframe["matchday"]
        .astype("Int64")
    )

    dataframe["home_score"] = (
        dataframe["home_score"]
        .astype("Int64")
    )

    dataframe["away_score"] = (
        dataframe["away_score"]
        .astype("Int64")
    )

    dataframe["result"] = (
        dataframe["result"]
        .astype("string")
    )

    # -----------------------------
    # Data-quality assertions
    # -----------------------------

    if dataframe["match_id"].isna().any():
        raise ValueError(
            "Null match IDs found."
        )

    if dataframe["match_id"].duplicated().any():

        duplicate_ids = (
            dataframe.loc[
                dataframe["match_id"].duplicated(),
                "match_id",
            ]
            .tolist()
        )

        raise ValueError(
            f"Duplicate match IDs found: "
            f"{duplicate_ids}"
        )

    same_team = (
        dataframe["home_team_id"]
        == dataframe["away_team_id"]
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
            f"for matches: {invalid_matches}"
        )

    return dataframe

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

    competition = raw_standings.get(
        "competition",
        {},
    )

    season = raw_standings.get(
        "season",
        {},
    )

    current_matchday = season.get(
        "currentMatchday"
    )

    records = []

    for standing_group in raw_standings.get(
        "standings",
        [],
    ):

        standing_type = standing_group.get(
            "type"
        )

        # For the initial league table,
        # keep only the overall TOTAL table.
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
                    "competition_id": competition.get(
                        "id"
                    ),
                    "competition_code": competition_code,
                    "season_id": season.get(
                        "id"
                    ),
                    "snapshot_matchday": current_matchday,
                    "snapshot_date": source_snapshot_date,
                    "team_id": team.get(
                        "id"
                    ),
                    "position": row.get(
                        "position"
                    ),
                    "played": row.get(
                        "playedGames"
                    ),
                    "form": row.get(
                        "form"
                    ),
                    "won": row.get(
                        "won"
                    ),
                    "drawn": row.get(
                        "draw"
                    ),
                    "lost": row.get(
                        "lost"
                    ),
                    "points": row.get(
                        "points"
                    ),
                    "goals_for": row.get(
                        "goalsFor"
                    ),
                    "goals_against": row.get(
                        "goalsAgainst"
                    ),
                    "goal_difference": row.get(
                        "goalDifference"
                    ),
                    "loaded_at": loaded_at,
                }
            )

    dataframe = pd.DataFrame(
        records
    )

    if dataframe.empty:
        raise ValueError(
            "Standings transformation produced zero rows."
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
        dataframe[column] = (
            dataframe[column]
            .astype("Int64")
        )

    # -----------------------------
    # Data-quality assertions
    # -----------------------------

    if dataframe["team_id"].isna().any():
        raise ValueError(
            "Null team IDs found in standings."
        )

    if dataframe["team_id"].duplicated().any():

        duplicate_ids = (
            dataframe.loc[
                dataframe["team_id"].duplicated(),
                "team_id",
            ]
            .tolist()
        )

        raise ValueError(
            "Duplicate teams found in TOTAL "
            f"standings: {duplicate_ids}"
        )


    if (
        dataframe["played"]
        != (
            dataframe["won"]
            + dataframe["drawn"]
            + dataframe["lost"]
        )
    ).any():

        raise ValueError(
            "Standings validation failed: "
            "played != won + drawn + lost."
        )

    calculated_goal_difference = (
        dataframe["goals_for"]
        - dataframe["goals_against"]
    )

    if (
        calculated_goal_difference
        != dataframe["goal_difference"]
    ).any():

        raise ValueError(
            "Standings validation failed: "
            "goal_difference does not equal "
            "goals_for - goals_against."
        )

    return dataframe


def validate_match_team_relationships(
    fact_match: pd.DataFrame,
    dim_team: pd.DataFrame,
) -> None:
    """
    Ensure match team IDs exist in dim_team.
    """

    valid_team_ids = set(
        dim_team["team_id"].dropna()
    )

    match_team_ids = set(
        fact_match["home_team_id"]
        .dropna()
    ) | set(
        fact_match["away_team_id"]
        .dropna()
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
        dim_team["team_id"]
        .dropna()
    )

    standing_team_ids = set(
        standings["team_id"]
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

def save_parquet(
    dataframe: pd.DataFrame,
    filepath: Path,
) -> None:
    """Write a DataFrame to Parquet."""

    filepath.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    dataframe.to_parquet(
        filepath,
        index=False,
    )


def process_teams(
    competition_code: str,
) -> Path:
    """
    Transform the latest raw team snapshot
    and write dim_team as Parquet.
    """

    snapshot_dir = get_latest_snapshot_directory(
        competition_code
    )

    teams_path = snapshot_dir / "teams.json"

    raw_teams = load_json(
        teams_path
    )

    dim_team = transform_teams(
        raw_teams,
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

    print()
    print("Beautiful Game Analytics")
    print("------------------------")
    print(
        f"Source snapshot : {snapshot_dir.name}"
    )
    print(
        f"Teams processed : {len(dim_team)}"
    )
    print(
        f"Output          : {output_path}"
    )

    print()
    print(
        dim_team[
            [
                "team_id",
                "team_name",
                "short_name",
                "tla",
                "venue_name",
            ]
        ].to_string(index=False)
    )

    return output_path

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
        source_snapshot_date=snapshot_dir.name,
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

    completed_matches = (
        fact_match["status"]
        .eq("FINISHED")
        .sum()
    )

    scheduled_matches = (
        fact_match["status"]
        .isin(
            [
                "SCHEDULED",
                "TIMED",
            ]
        )
        .sum()
    )

    live_matches = (
    fact_match["status"]
    .isin(
        [
            "IN_PLAY",
            "PAUSED",
        ]
    )
    .sum()
    )

    other_matches = (
    len(fact_match)
    - completed_matches
    - scheduled_matches
    - live_matches
    )

    print()
    print("Match Transformation")
    print("--------------------")

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
            competition_code=competition_code,
            source_snapshot_date=snapshot_dir.name,
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
    print("Standings Transformation")
    print("------------------------")
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

def main() -> None:

    competition_code = "PD"

    print()
    print("Beautiful Game Analytics")
    print("========================")

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