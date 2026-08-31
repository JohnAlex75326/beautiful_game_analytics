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
    get_match_explorer,
)


st.set_page_config(
    page_title="Matches | Beautiful Game Analytics",
    page_icon="⚽",
    layout="wide",
)


apply_branding()
render_sidebar()


@st.cache_data(ttl=300)
def load_matches() -> pd.DataFrame:
    return get_match_explorer()


matches = load_matches()


# --------------------------------------------------
# Header
# --------------------------------------------------

page_header(
    "Matches",
    "Explore fixtures, results and matchday activity.",
)


# --------------------------------------------------
# Filters
# --------------------------------------------------

st.markdown("### Match Explorer")

filter_col1, filter_col2, filter_col3 = st.columns(3)


with filter_col1:

    matchdays = sorted(
        matches["matchday"]
        .dropna()
        .astype(int)
        .unique()
        .tolist()
    )

    selected_matchday = st.selectbox(
        "Matchday",
        options=["All"] + matchdays,
    )


with filter_col2:

    teams = sorted(
        set(matches["home_team"].dropna())
        | set(matches["away_team"].dropna())
    )

    selected_team = st.selectbox(
        "Team",
        options=["All"] + teams,
    )


with filter_col3:

    states = [
        "All",
        "Finished",
        "Live",
        "Upcoming",
        "Other",
    ]

    selected_state = st.selectbox(
        "Match State",
        options=states,
    )


# --------------------------------------------------
# Apply filters
# --------------------------------------------------

filtered = matches.copy()


if selected_matchday != "All":

    filtered = filtered[
        filtered["matchday"]
        == selected_matchday
    ]


if selected_team != "All":

    filtered = filtered[
        (filtered["home_team"] == selected_team)
        |
        (filtered["away_team"] == selected_team)
    ]


if selected_state != "All":

    filtered = filtered[
        filtered["match_state"]
        == selected_state
    ]


# --------------------------------------------------
# KPIs
# --------------------------------------------------

total_matches = len(filtered)

finished_matches = int(
    filtered["match_state"]
    .eq("Finished")
    .sum()
)

live_matches = int(
    filtered["match_state"]
    .eq("Live")
    .sum()
)

upcoming_matches = int(
    filtered["match_state"]
    .eq("Upcoming")
    .sum()
)


kpi1, kpi2, kpi3, kpi4 = st.columns(4)

kpi1.metric(
    "Matches",
    total_matches,
)

kpi2.metric(
    "Finished",
    finished_matches,
)

kpi3.metric(
    "Live",
    live_matches,
)

kpi4.metric(
    "Upcoming",
    upcoming_matches,
)


# --------------------------------------------------
# Fixture / result table
# --------------------------------------------------

st.markdown("### Fixtures & Results")


display = filtered[
    [
        "matchday",
        "utc_date",
        "home_team",
        "scoreline",
        "away_team",
        "match_state",
    ]
].copy()


display["utc_date"] = pd.to_datetime(
    display["utc_date"]
)


display["Date"] = (
    display["utc_date"]
    .dt.strftime("%d %b %Y • %H:%M")
)


display = display[
    [
        "matchday",
        "Date",
        "home_team",
        "scoreline",
        "away_team",
        "match_state",
    ]
]


display.columns = [
    "MD",
    "Date",
    "Home",
    "Score",
    "Away",
    "State",
]


st.dataframe(
    display,
    use_container_width=True,
    hide_index=True,
    height=520,
)


# --------------------------------------------------
# Analytics
# --------------------------------------------------

left, right = st.columns(
    2,
    gap="large",
)


with left:

    st.markdown("### Match Status")

    status_summary = (
        filtered
        .groupby(
            "match_state",
            as_index=False,
        )
        .size()
        .rename(
            columns={
                "size": "matches",
            }
        )
    )

    status_figure = px.bar(
        status_summary,
        x="match_state",
        y="matches",
        labels={
            "match_state": "",
            "matches": "Matches",
        },
    )

    status_figure.update_layout(
        showlegend=False,
        height=350,
        margin={
            "l": 0,
            "r": 10,
            "t": 10,
            "b": 20,
        },
    )

    st.plotly_chart(
        status_figure,
        use_container_width=True,
    )


with right:

    st.markdown("### Finished-Match Goals")

    finished = filtered[
        filtered["match_state"]
        == "Finished"
    ].copy()

    if finished.empty:

        st.info(
            "No finished matches match the current filters."
        )

    else:

        finished["total_goals"] = (
            finished["home_score"]
            + finished["away_score"]
        )

        goals_by_matchday = (
            finished
            .groupby(
                "matchday",
                as_index=False,
            )
            .agg(
                matches=(
                    "match_id",
                    "count",
                ),
                goals=(
                    "total_goals",
                    "sum",
                ),
            )
        )

        goals_by_matchday[
            "goals_per_match"
        ] = (
            goals_by_matchday["goals"]
            / goals_by_matchday["matches"]
        )

        goals_figure = px.line(
            goals_by_matchday,
            x="matchday",
            y="goals_per_match",
            markers=True,
            labels={
                "matchday": "Matchday",
                "goals_per_match": "Goals / Match",
            },
        )

        goals_figure.update_layout(
            height=350,
            margin={
                "l": 0,
                "r": 10,
                "t": 10,
                "b": 20,
            },
        )

        st.plotly_chart(
            goals_figure,
            use_container_width=True,
        )


# --------------------------------------------------
# Context note
# --------------------------------------------------

if live_matches > 0:

    st.info(
        "Live-status records reflect the latest stored "
        "football-data.org snapshot. The public dashboard "
        "does not call the source API directly."
    )


render_footer()