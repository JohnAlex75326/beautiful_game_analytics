from pathlib import Path

import duckdb
import pandas as pd

from src.config import DUCKDB_PATH
from src.warehouse.s3_sync import ensure_latest_warehouse


def query_dataframe(query: str) -> pd.DataFrame:
    """
    Execute a read-only analytical query against
    the Beautiful Game Analytics DuckDB warehouse.
    """

    # Check whether S3 has a newer warehouse before querying.
    ensure_latest_warehouse()

    connection = duckdb.connect(
        str(DUCKDB_PATH),
        read_only=True,
    )

    try:
        return connection.execute(query).df()

    finally:
        connection.close()

def get_current_standings() -> pd.DataFrame:
    """
    Return the current official league table,
    including approved club artwork metadata.
    """

    return query_dataframe(
        """
        SELECT
            position,
            team_id,
            team_name,
            short_name,
            tla,
            sportsdb_badge_url,
            played,
            won,
            drawn,
            lost,
            goals_for,
            goals_against,
            goal_difference,
            points,
            is_reconciled,
            snapshot_date,
            snapshot_matchday

        FROM analytics.mart_current_standings

        ORDER BY
            position,
            short_name
        """
    )


def get_team_performance() -> pd.DataFrame:
    """
    Return performance derived from FINISHED matches.
    """

    return query_dataframe(
        """
        SELECT
            team_id,
            team_name,
            short_name,
            tla,
            played,
            won,
            drawn,
            lost,
            points,
            goals_for,
            goals_against,
            goal_difference,
            points_per_game,
            goals_for_per_game,
            goals_against_per_game,
            home_points,
            away_points
        FROM analytics.mart_team_performance
        ORDER BY
            points DESC,
            goal_difference DESC,
            goals_for DESC
        """
    )


def get_match_status_summary() -> pd.DataFrame:
    """
    Return current source match-status counts.
    """

    return query_dataframe(
        """
        SELECT
            status,
            COUNT(*) AS match_count
        FROM main.fact_match
        GROUP BY status
        ORDER BY match_count DESC
        """
    )


def get_reconciliation_summary() -> pd.DataFrame:
    """
    Return current standings reconciliation health.
    """

    return query_dataframe(
        """
        SELECT
            COUNT(*) AS total_teams,

            SUM(
                CASE
                    WHEN is_reconciled THEN 1
                    ELSE 0
                END
            ) AS reconciled_teams,

            SUM(
                CASE
                    WHEN NOT is_reconciled THEN 1
                    ELSE 0
                END
            ) AS unreconciled_teams

        FROM analytics.mart_current_standings
        """
    )

def get_recent_matches(
    limit: int = 8,
) -> pd.DataFrame:
    """
    Return the latest completed fixtures,
    including approved club artwork.
    """

    return query_dataframe(
        f"""
        SELECT
            m.matchday,
            m.utc_date,

            h.short_name AS home_team,
            h.sportsdb_badge_url AS home_badge_url,

            a.short_name AS away_team,
            a.sportsdb_badge_url AS away_badge_url,

            m.home_score,
            m.away_score

        FROM main.fact_match m

        INNER JOIN main.dim_team h
            ON m.home_team_id = h.team_id

        INNER JOIN main.dim_team a
            ON m.away_team_id = a.team_id

        WHERE m.status = 'FINISHED'

        ORDER BY m.utc_date DESC

        LIMIT {int(limit)}
        """
    )


def get_upcoming_matches(
    limit: int = 8,
) -> pd.DataFrame:
    """
    Return the next scheduled fixtures,
    including approved club artwork.
    """

    return query_dataframe(
        f"""
        SELECT
            m.matchday,
            m.utc_date,

            h.short_name AS home_team,
            h.sportsdb_badge_url AS home_badge_url,

            a.short_name AS away_team,
            a.sportsdb_badge_url AS away_badge_url,

            m.status

        FROM main.fact_match m

        INNER JOIN main.dim_team h
            ON m.home_team_id = h.team_id

        INNER JOIN main.dim_team a
            ON m.away_team_id = a.team_id

        WHERE m.status IN (
            'SCHEDULED',
            'TIMED'
        )

        ORDER BY m.utc_date

        LIMIT {int(limit)}
        """
    )


def get_match_explorer() -> pd.DataFrame:
    """
    Return the business-ready fixture and result dataset.
    """

    return query_dataframe(
        """
        SELECT
            match_id,
            matchday,
            utc_date,
            status,
            match_state,

            home_team_id,
            home_team,
            home_tla,
            home_badge_url,

            away_team_id,
            away_team,
            away_tla,
            away_badge_url,

            home_score,
            away_score,
            scoreline,
            result

        FROM analytics.mart_match_explorer

        ORDER BY
            utc_date ASC,
            matchday ASC
        """
    )

def get_data_health_overview() -> pd.DataFrame:
    """
    Return high-level warehouse freshness and
    reconciliation metrics.
    """

    return query_dataframe(
        """
        SELECT

            (
                SELECT COUNT(*)
                FROM main.fact_match
            ) AS match_rows,

            (
                SELECT COUNT(DISTINCT snapshot_date)
                FROM main.fact_standing_snapshot
            ) AS standing_snapshots,

            (
                SELECT MAX(source_snapshot_date)
                FROM main.fact_match
            ) AS latest_source_snapshot,

            (
                SELECT MAX(loaded_at)
                FROM main.fact_match
            ) AS latest_warehouse_load,

            (
                SELECT COUNT(*)
                FROM analytics.mart_current_standings
                WHERE is_reconciled = TRUE
            ) AS reconciled_teams,

            (
                SELECT COUNT(*)
                FROM analytics.mart_current_standings
            ) AS total_teams
        """
    )


def get_model_row_counts() -> pd.DataFrame:
    """
    Return row counts across the warehouse and
    dbt analytics layers.
    """

    return query_dataframe(
        """
        SELECT
            'Warehouse' AS layer,
            'dim_team' AS model,
            COUNT(*) AS rows
        FROM main.dim_team

        UNION ALL

        SELECT
            'Warehouse',
            'fact_match',
            COUNT(*)
        FROM main.fact_match

        UNION ALL

        SELECT
            'Warehouse',
            'fact_standing_snapshot',
            COUNT(*)
        FROM main.fact_standing_snapshot

        UNION ALL

        SELECT
            'Staging',
            'stg_teams',
            COUNT(*)
        FROM analytics.stg_teams

        UNION ALL

        SELECT
            'Staging',
            'stg_matches',
            COUNT(*)
        FROM analytics.stg_matches

        UNION ALL

        SELECT
            'Staging',
            'stg_standings',
            COUNT(*)
        FROM analytics.stg_standings

        UNION ALL

        SELECT
            'Intermediate',
            'int_team_match_results',
            COUNT(*)
        FROM analytics.int_team_match_results

        UNION ALL

        SELECT
            'Intermediate',
            'int_standings_reconciliation',
            COUNT(*)
        FROM analytics.int_standings_reconciliation

        UNION ALL

        SELECT
            'Mart',
            'mart_current_standings',
            COUNT(*)
        FROM analytics.mart_current_standings

        UNION ALL

        SELECT
            'Mart',
            'mart_team_performance',
            COUNT(*)
        FROM analytics.mart_team_performance

        UNION ALL

        SELECT
            'Mart',
            'mart_match_explorer',
            COUNT(*)
        FROM analytics.mart_match_explorer
        """
    )


def get_reconciliation_detail() -> pd.DataFrame:
    """
    Return official-vs-finished-match reconciliation
    detail for every team.
    """

    return query_dataframe(
        """
        SELECT
            position,
            short_name,
            played,
            points,
            is_reconciled,
            played_delta,
            points_delta,
            goals_for_delta,
            goals_against_delta

        FROM analytics.mart_current_standings

        ORDER BY
            position,
            short_name
        """
    )

def get_pipeline_runs(limit: int = 10) -> pd.DataFrame:
    """
    Return recent Beautiful Game Analytics pipeline runs.
    """

    limit = int(limit)

    return query_dataframe(
        f"""
        SELECT
            run_id,
            competition_code,
            started_at,
            finished_at,
            status,
            current_stage,
            failed_stage,
            duration_seconds,
            error_message

        FROM main.pipeline_run_log

        ORDER BY started_at DESC

        LIMIT {limit}
        """
    )