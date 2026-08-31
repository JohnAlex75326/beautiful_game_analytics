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
    get_match_status_summary,
    get_recent_matches,
    get_reconciliation_summary,
    get_team_performance,
    get_upcoming_matches,
)


st.set_page_config(
    page_title="Beautiful Game Analytics",
    page_icon="⚽",
    layout="wide",
)


apply_branding()
render_sidebar()


@st.cache_data(ttl=300)
def load_dashboard_data():

    return (
        get_current_standings(),
        get_team_performance(),
        get_match_status_summary(),
        get_reconciliation_summary(),
        get_recent_matches(),
        get_upcoming_matches(),
    )


(
    standings,
    performance,
    statuses,
    reconciliation,
    recent_matches,
    upcoming_matches,
) = load_dashboard_data()


# --------------------------------------------------
# Header
# --------------------------------------------------

page_header(
    "Beautiful Game Analytics",
    "La Liga matchday intelligence, team performance "
    "and source-data signals.",
)


# --------------------------------------------------
# Core metrics
# --------------------------------------------------

finished_matches = statuses.loc[
    statuses["status"] == "FINISHED",
    "match_count",
].sum()

total_teams = int(
    reconciliation.iloc[0]["total_teams"]
)

reconciled_teams = int(
    reconciliation.iloc[0]["reconciled_teams"]
)

latest_matchday = int(
    standings["snapshot_matchday"].max()
)

reconciliation_rate = (
    reconciled_teams
    / total_teams
    * 100
)


col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Teams",
    total_teams,
)

col2.metric(
    "Finished Matches",
    int(finished_matches),
)

col3.metric(
    "Latest Matchday",
    latest_matchday,
)

col4.metric(
    "Source Reconciliation",
    f"{reconciliation_rate:.0f}%",
)


# --------------------------------------------------
# Data-health notice
# --------------------------------------------------

if reconciliation_rate < 100:

    st.warning(
        f"{total_teams - reconciled_teams} teams currently "
        "have standings information ahead of the "
        "FINISHED-match feed. Official standings remain "
        "preserved independently."
    )


# --------------------------------------------------
# League snapshot
# --------------------------------------------------

leader = standings.iloc[0]

best_attack = (
    standings
    .sort_values(
        "goals_for",
        ascending=False,
    )
    .iloc[0]
)

best_defence = (
    standings
    .sort_values(
        "goals_against",
        ascending=True,
    )
    .iloc[0]
)


left, right = st.columns(
    [2.2, 1],
    gap="large",
)


with left:

    st.markdown(
        '<div class="bga-section-title">'
        'Current Standings'
        '</div>',
        unsafe_allow_html=True,
    )

    table = standings[
        [
            "position",
            "short_name",
            "played",
            "won",
            "drawn",
            "lost",
            "goal_difference",
            "points",
        ]
    ].head(10).copy()

    table.columns = [
        "Pos",
        "Team",
        "P",
        "W",
        "D",
        "L",
        "GD",
        "Pts",
    ]

    st.dataframe(
        table,
        use_container_width=True,
        hide_index=True,
        height=390,
    )


with right:

    st.markdown(
        '<div class="bga-section-title">'
        'League Snapshot'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="bga-card">
            <div class="bga-card-label">
                League Leader
            </div>
            <div class="bga-card-value">
                {leader["short_name"]}
            </div>
            {leader["points"]} points
        </div>

        <div class="bga-card">
            <div class="bga-card-label">
                Best Attack
            </div>
            <div class="bga-card-value">
                {best_attack["short_name"]}
            </div>
            {best_attack["goals_for"]} goals
        </div>

        <div class="bga-card">
            <div class="bga-card-label">
                Best Defence
            </div>
            <div class="bga-card-value">
                {best_defence["short_name"]}
            </div>
            {best_defence["goals_against"]} conceded
        </div>
        """,
        unsafe_allow_html=True,
    )


# --------------------------------------------------
# Recent + Upcoming
# --------------------------------------------------

st.markdown(
    '<div class="bga-section-title">'
    'Matchday Pulse'
    '</div>',
    unsafe_allow_html=True,
)


recent_col, upcoming_col = st.columns(
    2,
    gap="large",
)


with recent_col:

    st.markdown("#### Recent Results")

    recent = recent_matches.copy()

    recent["Score"] = (
        recent["home_score"].astype(str)
        + " – "
        + recent["away_score"].astype(str)
    )

    recent = recent[
        [
            "matchday",
            "home_team",
            "Score",
            "away_team",
        ]
    ]

    recent.columns = [
        "MD",
        "Home",
        "Score",
        "Away",
    ]

    st.dataframe(
        recent,
        use_container_width=True,
        hide_index=True,
    )


with upcoming_col:

    st.markdown("#### Upcoming Fixtures")

    upcoming = upcoming_matches[
        [
            "matchday",
            "home_team",
            "away_team",
            "status",
        ]
    ].copy()

    upcoming.columns = [
        "MD",
        "Home",
        "Away",
        "Status",
    ]

    st.dataframe(
        upcoming,
        use_container_width=True,
        hide_index=True,
    )


# --------------------------------------------------
# Performance
# --------------------------------------------------

st.markdown(
    '<div class="bga-section-title">'
    'Finished-Match Performance'
    '</div>',
    unsafe_allow_html=True,
)


chart_data = (
    performance
    .sort_values(
        "points_per_game",
        ascending=False,
    )
    .head(10)
)


figure = px.bar(
    chart_data,
    x="points_per_game",
    y="short_name",
    orientation="h",
    labels={
        "points_per_game": "Points Per Game",
        "short_name": "",
    },
)

figure.update_layout(
    yaxis={
        "categoryorder": "total ascending"
    },
    margin={
        "l": 0,
        "r": 20,
        "t": 10,
        "b": 20,
    },
    height=430,
)

st.plotly_chart(
    figure,
    use_container_width=True,
)


render_footer()