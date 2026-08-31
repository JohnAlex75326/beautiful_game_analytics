import plotly.express as px
import streamlit as st

from src.ui.layout import (
    apply_branding,
    page_header,
    render_footer,
    render_sidebar,
)

from src.warehouse.queries import (
    get_current_standings,
    get_reconciliation_summary,
)


st.set_page_config(
    page_title="Standings | Beautiful Game Analytics",
    page_icon="⚽",
    layout="wide",
)


apply_branding()
render_sidebar()


@st.cache_data(ttl=300)
def load_standings_data():
    return (
        get_current_standings(),
        get_reconciliation_summary(),
    )


standings, reconciliation = load_standings_data()


# --------------------------------------------------
# Header
# --------------------------------------------------

page_header(
    "Standings",
    "Official La Liga table, league position and "
    "source-reconciliation status.",
)


# --------------------------------------------------
# League snapshot
# --------------------------------------------------

leader = standings.iloc[0]

best_attack = (
    standings
    .sort_values(
        [
            "goals_for",
            "goal_difference",
        ],
        ascending=[
            False,
            False,
        ],
    )
    .iloc[0]
)

best_defence = (
    standings
    .sort_values(
        [
            "goals_against",
            "goal_difference",
        ],
        ascending=[
            True,
            False,
        ],
    )
    .iloc[0]
)

reconciled_teams = int(
    reconciliation.iloc[0]["reconciled_teams"]
)

total_teams = int(
    reconciliation.iloc[0]["total_teams"]
)

reconciliation_rate = (
    reconciled_teams
    / total_teams
    * 100
)


col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "League Leader",
    leader["short_name"],
    f'{leader["points"]} pts',
)

col2.metric(
    "Best Attack",
    best_attack["short_name"],
    f'{best_attack["goals_for"]} goals',
)

col3.metric(
    "Best Defence",
    best_defence["short_name"],
    f'{best_defence["goals_against"]} conceded',
)

col4.metric(
    "Source Reconciliation",
    f"{reconciliation_rate:.0f}%",
    f"{reconciled_teams}/{total_teams} teams",
)


# --------------------------------------------------
# Data-health context
# --------------------------------------------------

if reconciliation_rate < 100:

    st.warning(
        f"{total_teams - reconciled_teams} teams have "
        "official standings information ahead of the "
        "FINISHED-match feed. The table below preserves "
        "the official standings snapshot."
    )


# --------------------------------------------------
# Current table
# --------------------------------------------------

st.markdown("### Current League Table")


table = standings[
    [
        "position",
        "short_name",
        "played",
        "won",
        "drawn",
        "lost",
        "goals_for",
        "goals_against",
        "goal_difference",
        "points",
        "is_reconciled",
    ]
].copy()


table["is_reconciled"] = table[
    "is_reconciled"
].map(
    {
        True: "✓ Synced",
        False: "⚠ Pending",
    }
)


table.columns = [
    "Pos",
    "Team",
    "P",
    "W",
    "D",
    "L",
    "GF",
    "GA",
    "GD",
    "Pts",
    "Data",
]


st.dataframe(
    table,
    use_container_width=True,
    hide_index=True,
    height=740,
    column_config={
        "Pos": st.column_config.NumberColumn(
            "Pos",
            width="small",
        ),
        "Team": st.column_config.TextColumn(
            "Team",
            width="medium",
        ),
        "Pts": st.column_config.NumberColumn(
            "Pts",
            width="small",
        ),
        "Data": st.column_config.TextColumn(
            "Data",
            help=(
                "Whether official standings totals "
                "currently reconcile with matches "
                "marked FINISHED by the source API."
            ),
        ),
    },
)


st.caption(
    "Displayed positions are preserved exactly as supplied "
    "by the source. Tied positions are therefore possible."
)


# --------------------------------------------------
# Points race
# --------------------------------------------------

st.markdown("### Points Race")


points_chart = (
    standings
    .sort_values(
        [
            "points",
            "goal_difference",
            "goals_for",
        ],
        ascending=[
            True,
            True,
            True,
        ],
    )
)


points_figure = px.bar(
    points_chart,
    x="points",
    y="short_name",
    orientation="h",
    text="points",
    labels={
        "points": "Points",
        "short_name": "",
    },
)


points_figure.update_traces(
    textposition="outside",
)


points_figure.update_layout(
    height=650,
    showlegend=False,
    margin={
        "l": 0,
        "r": 50,
        "t": 10,
        "b": 20,
    },
)


st.plotly_chart(
    points_figure,
    use_container_width=True,
)


# --------------------------------------------------
# Goal performance
# --------------------------------------------------

st.markdown("### Goal Performance")


goal_col1, goal_col2 = st.columns(
    2,
    gap="large",
)


with goal_col1:

    st.markdown("#### Goal Difference")

    gd_chart = (
        standings
        .sort_values(
            "goal_difference",
            ascending=True,
        )
    )

    gd_figure = px.bar(
        gd_chart,
        x="goal_difference",
        y="short_name",
        orientation="h",
        labels={
            "goal_difference": "Goal Difference",
            "short_name": "",
        },
    )

    gd_figure.update_layout(
        height=550,
        showlegend=False,
        margin={
            "l": 0,
            "r": 20,
            "t": 10,
            "b": 20,
        },
    )

    st.plotly_chart(
        gd_figure,
        use_container_width=True,
    )


with goal_col2:

    st.markdown("#### Goals Scored")

    gf_chart = (
        standings
        .sort_values(
            "goals_for",
            ascending=True,
        )
    )

    gf_figure = px.bar(
        gf_chart,
        x="goals_for",
        y="short_name",
        orientation="h",
        labels={
            "goals_for": "Goals",
            "short_name": "",
        },
    )

    gf_figure.update_layout(
        height=550,
        showlegend=False,
        margin={
            "l": 0,
            "r": 20,
            "t": 10,
            "b": 20,
        },
    )

    st.plotly_chart(
        gf_figure,
        use_container_width=True,
    )


# --------------------------------------------------
# Reconciliation detail
# --------------------------------------------------

st.markdown("### Data Reconciliation")


unreconciled = standings[
    standings["is_reconciled"] == False
].copy()


if unreconciled.empty:

    st.success(
        "All teams currently reconcile with the "
        "FINISHED-match feed."
    )

else:

    st.info(
        f"{len(unreconciled)} teams currently have "
        "standings totals ahead of the FINISHED-match feed."
    )

    reconciliation_table = unreconciled[
        [
            "position",
            "short_name",
            "played",
            "points",
        ]
    ].copy()

    reconciliation_table.columns = [
        "Pos",
        "Team",
        "Official Played",
        "Official Points",
    ]

    st.dataframe(
        reconciliation_table,
        use_container_width=True,
        hide_index=True,
    )


render_footer()