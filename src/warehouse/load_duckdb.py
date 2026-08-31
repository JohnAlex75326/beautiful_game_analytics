import duckdb

from src.config import (
    DUCKDB_PATH,
    PROCESSED_DATA_DIR,
)


def get_connection() -> duckdb.DuckDBPyConnection:
    """
    Open a connection to the Beautiful Game Analytics
    DuckDB warehouse.
    """

    DUCKDB_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    return duckdb.connect(
        str(DUCKDB_PATH)
    )


def load_dim_team(
    connection: duckdb.DuckDBPyConnection,
    competition_code: str,
) -> None:
    """
    Load the latest team dimension into DuckDB.
    """

    parquet_path = (
        PROCESSED_DATA_DIR
        / competition_code
        / "dim_team.parquet"
    ).as_posix()

    connection.execute(
        f"""
        CREATE OR REPLACE TABLE dim_team AS

        SELECT *
        FROM read_parquet('{parquet_path}')
        """
    )


def load_fact_match(
    connection: duckdb.DuckDBPyConnection,
    competition_code: str,
) -> None:
    """
    Load the latest match fact table into DuckDB.
    """

    parquet_path = (
        PROCESSED_DATA_DIR
        / competition_code
        / "fact_match.parquet"
    ).as_posix()

    connection.execute(
        f"""
        CREATE OR REPLACE TABLE fact_match AS

        SELECT *
        FROM read_parquet('{parquet_path}')
        """
    )


def load_fact_standing_snapshot(
    connection: duckdb.DuckDBPyConnection,
    competition_code: str,
) -> None:
    """
    Load all preserved standings snapshots into DuckDB.
    """

    parquet_glob = (
        PROCESSED_DATA_DIR
        / competition_code
        / "standings"
        / "*.parquet"
    ).as_posix()

    connection.execute(
        f"""
        CREATE OR REPLACE TABLE fact_standing_snapshot AS

        SELECT *
        FROM read_parquet(
            '{parquet_glob}',
            union_by_name = true
        )
        """
    )


def validate_warehouse(
    connection: duckdb.DuckDBPyConnection,
) -> None:
    """
    Run basic warehouse validation checks.
    """

    team_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM dim_team
        """
    ).fetchone()[0]

    match_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM fact_match
        """
    ).fetchone()[0]

    standing_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM fact_standing_snapshot
        """
    ).fetchone()[0]

    snapshot_count = connection.execute(
        """
        SELECT COUNT(
            DISTINCT snapshot_date
        )
        FROM fact_standing_snapshot
        """
    ).fetchone()[0]

    print()
    print("Warehouse Validation")
    print("--------------------")
    print(
        f"Teams                    : {team_count}"
    )
    print(
        f"Matches                  : {match_count}"
    )
    print(
        f"Standing snapshot rows   : {standing_count}"
    )
    print(
        f"Standing snapshot dates  : {snapshot_count}"
    )

    if team_count == 0:
        raise ValueError(
            "dim_team contains zero rows."
        )

    if match_count == 0:
        raise ValueError(
            "fact_match contains zero rows."
        )

    if standing_count == 0:
        raise ValueError(
            "fact_standing_snapshot contains zero rows."
        )


def build_warehouse(
    competition_code: str,
) -> None:
    """
    Build the Beautiful Game Analytics
    DuckDB warehouse.
    """

    print()
    print("Beautiful Game Analytics")
    print("========================")
    print("Building DuckDB warehouse...")

    connection = get_connection()

    try:

        connection.execute(
            "BEGIN TRANSACTION"
        )

        load_dim_team(
            connection,
            competition_code,
        )

        load_fact_match(
            connection,
            competition_code,
        )

        load_fact_standing_snapshot(
            connection,
            competition_code,
        )

        validate_warehouse(
            connection
        )

        connection.execute(
            "COMMIT"
        )

    except Exception:

        connection.execute(
            "ROLLBACK"
        )

        raise

    finally:

        connection.close()

    print()
    print(
        f"Warehouse created: {DUCKDB_PATH}"
    )


def main() -> None:
    build_warehouse("PD")


if __name__ == "__main__":
    main()