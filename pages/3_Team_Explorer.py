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
    get_current_standings,
    get_match_explorer,
    get_team_performance,
)


st.set_page_config(
    page_title="Team Explorer | Beautiful Game Analytics",
    page_icon="⚽",
    layout="wide",
)


apply_branding()
render_sidebar()


@st.cache_data(ttl=300)
def load_team_data():
    return (
        get_current_standings(),
        get_team_performance(),
        get_match_explorer(),
    )


standings, performance, matches = load_team_data()


# --------------------------------------------------
# Header
# --------------------------------------------------

page_header(
    "Team Explorer",
    "Explore club performance, results, form and "
    "official league position.",
)


# --------------------------------------------------
# Team selector
# --------------------------------------------------

teams = sorted(
    standings["short_name"]
    .dropna()
    .unique()
    .tolist()
)


default_team = (
    teams.index("Real Madrid")
    if "Real Madrid" in teams
    else 0
)


selected_team = st.selectbox(
    "Select Team",
    options=teams,
    index=default_team,
)


# --------------------------------------------------
# Selected team records
# --------------------------------------------------

official = standings[
    standings["short_name"] == selected_team
].iloc[0]


derived = performance[
    performance["short_name"] == selected_team
]


if derived.empty:
    derived_row = None
else:
    derived_row = derived.iloc[0]


team_id = official["team_id"]


team_matches = matches[
    (
        matches["home_team_id"] == team_id
    )
    |
    (
        matches["away_team_id"] == team_id
    )
].copy()


# --------------------------------------------------
# Team identity
# --------------------------------------------------

st.markdown(
    f"## {official['team_name']}"
)

st.caption(
    f"{official['tla']} • "
    f"Official position #{official['position']}"
)


# --------------------------------------------------
# Core KPIs
# --------------------------------------------------

kpi1, kpi2, kpi3, kpi4 = st.columns(4)


kpi1.metric(
    "League Position",
    f"#{int(official['position'])}",
)


kpi2.metric(
    "Official Points",
    int(official["points"]),
)


if derived_row is not None:

    kpi3.metric(
        "Finished-Match PPG",
        f"{derived_row['points_per_game']:.2f}",
    )

    kpi4.metric(
        "Goal Difference",
        f"{int(derived_row['goal_difference']):+d}",
    )

else:

    kpi3.metric(
        "Finished-Match PPG",
        "N/A",
    )

    kpi4.metric(
        "Goal Difference",
        "N/A",
    )


# --------------------------------------------------
# Reconciliation notice
# --------------------------------------------------

if bool(official["is_reconciled"]):

    st.success(
        "Official standings totals currently reconcile "
        "with the FINISHED-match feed."
    )

else:

    st.warning(
        "Official standings are currently ahead of the "
        "FINISHED-match feed for this club. Official table "
        "metrics and derived match analytics are shown "
        "separately."
    )


# --------------------------------------------------
# Performance snapshot
# --------------------------------------------------

st.markdown("### Performance Snapshot")


if derived_row is None:

    st.info(
        "No finished-match performance data is currently "
        "available for this team."
    )

else:

    perf1, perf2, perf3, perf4 = st.columns(4)

    perf1.metric(
        "Played",
        int(derived_row["played"]),
    )

    perf2.metric(
        "W-D-L",
        (
            f"{int(derived_row['won'])}-"
            f"{int(derived_row['drawn'])}-"
            f"{int(derived_row['lost'])}"
        ),
    )

    perf3.metric(
        "Goals / Match",
        f"{derived_row['goals_for_per_game']:.2f}",
    )

    perf4.metric(
        "Conceded / Match",
        f"{derived_row['goals_against_per_game']:.2f}",
    )


# --------------------------------------------------
# Home / Away
# --------------------------------------------------

if derived_row is not None:

    st.markdown("### Home vs Away")

    home_away = pd.DataFrame(
        {
            "Venue": [
                "Home",
                "Away",
            ],
            "Points": [
                derived_row["home_points"],
                derived_row["away_points"],
            ],
        }
    )

    home_away_figure = px.bar(
        home_away,
        x="Venue",
        y="Points",
        text="Points",
        labels={
            "Points": "Points Earned",
        },
    )

    home_away_figure.update_traces(
        textposition="outside"
    )

    home_away_figure.update_layout(
        height=350,
        showlegend=False,
        margin={
            "l": 0,
            "r": 20,
            "t": 10,
            "b": 20,
        },
    )

    st.plotly_chart(
        home_away_figure,
        use_container_width=True,
    )


# --------------------------------------------------
# Finished-match form
# --------------------------------------------------

st.markdown("### Recent Finished Matches")


finished_team_matches = team_matches[
    team_matches["match_state"] == "Finished"
].copy()


finished_team_matches = (
    finished_team_matches
    .sort_values(
        "utc_date",
        ascending=False,
    )
)


if finished_team_matches.empty:

    st.info(
        "No completed matches are available for this club."
    )

else:

    def team_result(row):
        if row["home_team_id"] == team_id:

            if row["result"] == "H":
                return "W"

            if row["result"] == "D":
                return "D"

            return "L"

        if row["result"] == "A":
            return "W"

        if row["result"] == "D":
            return "D"

        return "L"


    finished_team_matches[
        "Team Result"
    ] = finished_team_matches.apply(
        team_result,
        axis=1,
    )


    recent_display = finished_team_matches[
        [
            "matchday",
            "utc_date",
            "home_team",
            "scoreline",
            "away_team",
            "Team Result",
        ]
    ].copy()


    recent_display["utc_date"] = pd.to_datetime(
        recent_display["utc_date"]
    )


    recent_display["Date"] = (
        recent_display["utc_date"]
        .dt.strftime("%d %b %Y")
    )


    recent_display = recent_display[
        [
            "matchday",
            "Date",
            "home_team",
            "scoreline",
            "away_team",
            "Team Result",
        ]
    ]


    recent_display.columns = [
        "MD",
        "Date",
        "Home",
        "Score",
        "Away",
        "Result",
    ]


    st.dataframe(
        recent_display,
        use_container_width=True,
        hide_index=True,
    )


# --------------------------------------------------
# Upcoming fixtures
# --------------------------------------------------

st.markdown("### Upcoming Fixtures")


upcoming = team_matches[
    team_matches["match_state"] == "Upcoming"
].copy()


upcoming = (
    upcoming
    .sort_values("utc_date")
    .head(5)
)


if upcoming.empty:

    st.info(
        "No upcoming fixtures are currently available."
    )

else:

    upcoming["utc_date"] = pd.to_datetime(
        upcoming["utc_date"]
    )


    upcoming["Date"] = (
        upcoming["utc_date"]
        .dt.strftime(
            "%d %b %Y • %H:%M"
        )
    )


    upcoming_display = upcoming[
        [
            "matchday",
            "Date",
            "home_team",
            "away_team",
            "status",
        ]
    ].copy()


    upcoming_display.columns = [
        "MD",
        "Date",
        "Home",
        "Away",
        "Status",
    ]


    st.dataframe(
        upcoming_display,
        use_container_width=True,
        hide_index=True,
    )


# --------------------------------------------------
# Official vs derived
# --------------------------------------------------

st.markdown("### Official vs Finished-Match Data")


if derived_row is not None:

    comparison = pd.DataFrame(
        {
            "Metric": [
                "Played",
                "Points",
                "Goals For",
                "Goals Against",
            ],

            "Official Standings": [
                official["played"],
                official["points"],
                official["goals_for"],
                official["goals_against"],
            ],

            "Finished Matches": [
                derived_row["played"],
                derived_row["points"],
                derived_row["goals_for"],
                derived_row["goals_against"],
            ],
        }
    )


    comparison["Difference"] = (
        comparison["Official Standings"]
        - comparison["Finished Matches"]
    )


    st.dataframe(
        comparison,
        use_container_width=True,
        hide_index=True,
    )


render_footer()