import pandas as pd
import plotly.express as px
import streamlit as st

from src.ui.layout import (
    apply_branding,
    page_header,
    render_footer,
    render_sidebar,
)

from src.warehouse.queries import (
    get_data_health_overview,
    get_match_status_summary,
    get_model_row_counts,
    get_pipeline_runs,
    get_reconciliation_detail,
)

from src.warehouse.s3_sync import (
    get_warehouse_sync_status,
)


# --------------------------------------------------
# Page configuration
# --------------------------------------------------

st.set_page_config(
    page_title="Data Health | Beautiful Game Analytics",
    page_icon="⚙️",
    layout="wide",
)


# --------------------------------------------------
# Shared branding
# --------------------------------------------------

apply_branding()
render_sidebar()


# --------------------------------------------------
# Load data
# --------------------------------------------------

@st.cache_data(ttl=300)
def load_health_data():
    """
    Load the analytical datasets required by the
    Data Health page.

    All warehouse queries pass through queries.py,
    which first checks whether the local DuckDB cache
    should be refreshed from Amazon S3.
    """

    return (
        get_data_health_overview(),
        get_match_status_summary(),
        get_model_row_counts(),
        get_reconciliation_detail(),
        get_pipeline_runs(),
    )


(
    health,
    match_status,
    model_counts,
    reconciliation,
    pipeline_runs,
) = load_health_data()


# The queries above already trigger the warehouse
# synchronization check. We inspect the resulting
# local/S3 state after that process has completed.
warehouse_sync = get_warehouse_sync_status()


health_row = health.iloc[0]


# --------------------------------------------------
# Header
# --------------------------------------------------

page_header(
    "Data Health",
    "Warehouse freshness, model coverage and "
    "source-reconciliation observability.",
)


# --------------------------------------------------
# Cloud warehouse
# --------------------------------------------------

st.markdown("### Cloud Warehouse")


cloud1, cloud2, cloud3 = st.columns(3)


# Storage mode
storage_mode = (
    "Amazon S3"
    if warehouse_sync["s3_enabled"]
    else "Local"
)


cloud1.metric(
    "Storage",
    storage_mode,
)


# Warehouse cache status
if not warehouse_sync["s3_enabled"]:

    cache_status = "Local Only"

elif warehouse_sync["is_current"]:

    cache_status = "Current"

else:

    cache_status = "Update Available"


cloud2.metric(
    "Warehouse Cache",
    cache_status,
)


# Latest S3 publication time
remote_last_modified = warehouse_sync[
    "remote_last_modified"
]


if remote_last_modified:

    remote_modified = pd.to_datetime(
        remote_last_modified,
        utc=True,
    )

    cloud3.metric(
        "S3 Published",
        remote_modified.strftime(
            "%d %b • %H:%M UTC"
        ),
    )

else:

    cloud3.metric(
        "S3 Published",
        "N/A",
    )


# Warehouse state message
if warehouse_sync["is_current"]:

    st.success(
        "The local analytical warehouse matches "
        "the latest version published to Amazon S3."
    )

elif warehouse_sync["s3_enabled"]:

    st.warning(
        "A newer S3 warehouse version is available."
    )

else:

    st.info(
        "S3 synchronization is not configured. "
        "Using the local development warehouse."
    )


# --------------------------------------------------
# Core health metrics
# --------------------------------------------------

match_rows = int(
    health_row["match_rows"]
)

standing_snapshots = int(
    health_row["standing_snapshots"]
)

reconciled_teams = int(
    health_row["reconciled_teams"]
)

total_teams = int(
    health_row["total_teams"]
)


reconciliation_rate = (
    reconciled_teams
    / total_teams
    * 100
)


latest_load = pd.to_datetime(
    health_row["latest_warehouse_load"],
    utc=True,
)


latest_load_display = (
    latest_load.strftime(
        "%d %b %Y • %H:%M UTC"
    )
)


kpi1, kpi2, kpi3, kpi4 = st.columns(4)


kpi1.metric(
    "Match Records",
    match_rows,
)


kpi2.metric(
    "Standing Snapshots",
    standing_snapshots,
)


kpi3.metric(
    "Reconciled Teams",
    f"{reconciliation_rate:.0f}%",
    f"{reconciled_teams}/{total_teams}",
)


kpi4.metric(
    "Latest Warehouse Load",
    latest_load_display,
)


# --------------------------------------------------
# Overall source health
# --------------------------------------------------

if reconciliation_rate == 100:

    st.success(
        "Official standings currently reconcile with "
        "all matches marked FINISHED by the source."
    )

else:

    unreconciled_count = (
        total_teams
        - reconciled_teams
    )

    st.warning(
        f"{unreconciled_count} teams currently have "
        "official standings information ahead of the "
        "FINISHED-match feed. The pipeline preserves "
        "both source states rather than rewriting them."
    )


# --------------------------------------------------
# Source freshness
# --------------------------------------------------

st.markdown("### Source Freshness")


source_snapshot = pd.to_datetime(
    health_row["latest_source_snapshot"]
)


fresh1, fresh2 = st.columns(
    2,
    gap="large",
)


with fresh1:

    st.markdown(
        """
        <div class="bga-card">
            <div class="bga-card-label">
                Latest Source Snapshot
            </div>
            <div class="bga-card-value">
        """
        + source_snapshot.strftime("%d %B %Y")
        + """
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


with fresh2:

    st.markdown(
        """
        <div class="bga-card">
            <div class="bga-card-label">
                Storage Strategy
            </div>
            <div class="bga-card-value">
                Snapshot Preserved
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.caption(
    "Source snapshots are stored independently so that "
    "historical states can be compared as the season progresses."
)


# --------------------------------------------------
# Match-feed state
# --------------------------------------------------

st.markdown("### Match Feed State")


status_figure = px.bar(
    match_status,
    x="status",
    y="match_count",
    text="match_count",
    labels={
        "status": "Status",
        "match_count": "Matches",
    },
)


status_figure.update_traces(
    textposition="outside"
)


status_figure.update_layout(
    height=400,
    showlegend=False,
    margin={
        "l": 0,
        "r": 20,
        "t": 20,
        "b": 20,
    },
)


st.plotly_chart(
    status_figure,
    use_container_width=True,
)


# --------------------------------------------------
# Standings reconciliation
# --------------------------------------------------

st.markdown("### Standings Reconciliation")


unreconciled = reconciliation[
    reconciliation["is_reconciled"] == False
].copy()


if unreconciled.empty:

    st.success(
        "Every team currently reconciles."
    )

else:

    display_reconciliation = unreconciled[
        [
            "position",
            "short_name",
            "played_delta",
            "points_delta",
            "goals_for_delta",
            "goals_against_delta",
        ]
    ].copy()


    display_reconciliation.columns = [
        "Pos",
        "Team",
        "Played Δ",
        "Points Δ",
        "GF Δ",
        "GA Δ",
    ]


    st.dataframe(
        display_reconciliation,
        use_container_width=True,
        hide_index=True,
    )


    st.caption(
        "A positive delta means the official standings "
        "contain information not yet represented by matches "
        "marked FINISHED in the stored match feed."
    )


# --------------------------------------------------
# Warehouse / dbt model inventory
# --------------------------------------------------

st.markdown("### Data Model Inventory")


layer_order = [
    "Warehouse",
    "Staging",
    "Intermediate",
    "Mart",
]


model_counts["layer"] = pd.Categorical(
    model_counts["layer"],
    categories=layer_order,
    ordered=True,
)


model_counts = model_counts.sort_values(
    [
        "layer",
        "model",
    ]
)


display_models = model_counts.copy()


display_models.columns = [
    "Layer",
    "Dataset",
    "Rows",
]


st.dataframe(
    display_models,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Layer": st.column_config.TextColumn(
            "Layer",
            width="medium",
        ),
        "Dataset": st.column_config.TextColumn(
            "Dataset",
            width="large",
        ),
        "Rows": st.column_config.NumberColumn(
            "Rows",
            format="%d",
        ),
    },
)


# --------------------------------------------------
# Pipeline architecture
# --------------------------------------------------

st.markdown("### Pipeline Architecture")


st.code(
    """
football-data.org
        │
        ▼
Python Ingestion
        │
        ▼
Raw JSON Snapshots
        │
        ▼
Pandas Transformations
        │
        ▼
Processed Parquet
        │
        ▼
DuckDB Warehouse
        │
        ▼
dbt
 ┌──────┼───────────┐
 ▼      ▼           ▼
Staging Intermediate Marts
                     │
                     ▼
                 Amazon S3
                     │
                     ▼
             Local DuckDB Cache
                     │
                     ▼
                 Streamlit
    """,
    language=None,
)


# --------------------------------------------------
# Pipeline observability
# --------------------------------------------------

st.markdown("### Pipeline Observability")


if pipeline_runs.empty:

    st.info(
        "No pipeline execution history is currently available."
    )

else:

    latest_run = pipeline_runs.iloc[0]


    run_col1, run_col2, run_col3, run_col4 = st.columns(4)


    run_col1.metric(
        "Latest Run",
        latest_run["status"],
    )


    run_col2.metric(
        "Stage",
        latest_run["current_stage"],
    )


    run_col3.metric(
        "Duration",
        f"{latest_run['duration_seconds']:.1f}s",
    )


    latest_started = pd.to_datetime(
        latest_run["started_at"],
        utc=True,
    )


    run_col4.metric(
        "Started",
        latest_started.strftime(
            "%d %b • %H:%M UTC"
        ),
    )


    if latest_run["status"] == "SUCCESS":

        st.success(
            "The latest ingestion → transformation → "
            "warehouse → dbt pipeline completed successfully."
        )

    else:

        st.error(
            f"Latest pipeline run failed during "
            f"{latest_run['failed_stage']}."
        )


    # --------------------------------------------------
    # Recent pipeline history
    # --------------------------------------------------

    st.markdown("#### Recent Pipeline Runs")


    run_history = pipeline_runs[
        [
            "started_at",
            "status",
            "current_stage",
            "failed_stage",
            "duration_seconds",
            "error_message",
        ]
    ].copy()


    run_history["started_at"] = pd.to_datetime(
        run_history["started_at"],
        utc=True,
    ).dt.strftime(
        "%d %b %Y • %H:%M UTC"
    )


    run_history["duration_seconds"] = (
        run_history["duration_seconds"]
        .round(2)
    )


    run_history.columns = [
        "Started",
        "Status",
        "Stage",
        "Failed Stage",
        "Duration (s)",
        "Error",
    ]


    st.dataframe(
        run_history,
        use_container_width=True,
        hide_index=True,
    )


# --------------------------------------------------
# Footer
# --------------------------------------------------

render_footer()