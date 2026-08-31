from __future__ import annotations

from zoneinfo import ZoneInfo

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


# ============================================================
# Page configuration
# ============================================================

st.set_page_config(
    page_title="Team Explorer | Beautiful Game Analytics",
    page_icon="⚽",
    layout="wide",
)


apply_branding()
render_sidebar()


# ============================================================
# Page-specific CSS
# ============================================================

st.markdown(
    """
    <style>

    /* ----------------------------------------------------
       Club identity
       ---------------------------------------------------- */

    .bga-club-hero {
        background:
            linear-gradient(
                145deg,
                #111821 0%,
                #0D131B 100%
            );

        border: 1px solid #202833;
        border-radius: 18px;

        padding: 24px;

        margin:
            8px 0
            20px 0;

        display: flex;

        align-items: center;

        gap: 22px;
    }


    .bga-club-hero-crest {
        width: 100px;
        height: 100px;

        object-fit: contain;

        flex-shrink: 0;
    }


    .bga-club-identity {
        display: flex;
        flex-direction: column;

        min-width: 0;
    }


    .bga-club-name {
        font-size: 1.55rem;
        font-weight: 800;

        line-height: 1.1;
    }


    .bga-club-meta {
        color: #8995A4;

        font-size: 0.78rem;

        margin-top: 7px;
    }


    .bga-club-position {
        color: #2EE59D;

        font-weight: 700;
    }


    /* ----------------------------------------------------
       Responsive club hero
       ---------------------------------------------------- */

    @media (max-width: 640px) {

        .bga-club-hero {
            flex-direction: column;

            text-align: center;

            padding: 20px;
        }


        .bga-club-hero-crest {
            width: 84px;
            height: 84px;
        }


        .bga-club-name {
            font-size: 1.3rem;
        }

    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# Data
# ============================================================

@st.cache_data(ttl=300)
def load_team_data():
    """
    Load standings, performance and match explorer data.
    """

    return (
        get_current_standings(),
        get_team_performance(),
        get_match_explorer(),
    )


standings, performance, matches = (
    load_team_data()
)


if standings.empty:

    st.error(
        "No team data is currently available."
    )

    st.stop()


matches["utc_date"] = pd.to_datetime(
    matches["utc_date"],
    utc=True,
)


# ============================================================
# Header
# ============================================================

page_header(
    "Team Explorer",
    (
        "Explore club performance, results, form and "
        "official league position."
    ),
)


# ============================================================
# Team selector
# ============================================================

teams = sorted(
    standings[
        "short_name"
    ]
    .dropna()
    .unique()
    .tolist()
)


default_team = (
    teams.index(
        "Real Madrid"
    )
    if "Real Madrid" in teams
    else 0
)


selected_team = st.selectbox(
    "Select Team",
    options=teams,
    index=default_team,
)


# ============================================================
# Selected team records
# ============================================================

official = (
    standings[
        standings[
            "short_name"
        ]
        == selected_team
    ]
    .iloc[0]
)


derived = (
    performance[
        performance[
            "short_name"
        ]
        == selected_team
    ]
)


if derived.empty:

    derived_row = None

else:

    derived_row = (
        derived.iloc[0]
    )


team_id = (
    official[
        "team_id"
    ]
)


team_matches = matches[
    (
        matches[
            "home_team_id"
        ]
        == team_id
    )
    |
    (
        matches[
            "away_team_id"
        ]
        == team_id
    )
].copy()


# ============================================================
# Club identity hero
# ============================================================

club_name = str(
    official[
        "team_name"
    ]
)


club_tla = str(
    official[
        "tla"
    ]
)


club_badge = str(
    official[
        "sportsdb_badge_url"
    ]
)


club_position = int(
    official[
        "position"
    ]
)


club_hero = (
    '<div class="bga-club-hero">'

    f'<img '
    f'class="bga-club-hero-crest" '
    f'src="{club_badge}" '
    f'alt="{club_name} crest">'

    '<div class="bga-club-identity">'

    f'<div class="bga-club-name">'
    f'{club_name}'
    f'</div>'

    '<div class="bga-club-meta">'
    f'{club_tla}'
    ' &nbsp;•&nbsp; '
    f'<span class="bga-club-position">'
    f'Official position #{club_position}'
    f'</span>'
    '</div>'

    '</div>'

    '</div>'
)


st.markdown(
    club_hero,
    unsafe_allow_html=True,
)


# ============================================================
# Core KPIs
# ============================================================

kpi1, kpi2, kpi3, kpi4 = (
    st.columns(4)
)


kpi1.metric(
    "League Position",
    f"#{club_position}",
)


kpi2.metric(
    "Official Points",
    int(
        official[
            "points"
        ]
    ),
)


if derived_row is not None:

    kpi3.metric(
        "Finished-Match PPG",
        (
            f"{derived_row['points_per_game']:.2f}"
        ),
    )


    kpi4.metric(
        "Goal Difference",
        (
            f"{int(derived_row['goal_difference']):+d}"
        ),
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


# ============================================================
# Reconciliation notice
# ============================================================

if bool(
    official[
        "is_reconciled"
    ]
):

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


# ============================================================
# Performance snapshot
# ============================================================

st.markdown(
    "### Performance Snapshot"
)


if derived_row is None:

    st.info(
        "No finished-match performance data is currently "
        "available for this team."
    )


else:

    perf1, perf2, perf3, perf4 = (
        st.columns(4)
    )


    perf1.metric(
        "Played",
        int(
            derived_row[
                "played"
            ]
        ),
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
        (
            f"{derived_row['goals_for_per_game']:.2f}"
        ),
    )


    perf4.metric(
        "Conceded / Match",
        (
            f"{derived_row['goals_against_per_game']:.2f}"
        ),
    )


# ============================================================
# Home vs Away
# ============================================================

if derived_row is not None:

    st.markdown(
        "### Home vs Away"
    )


    home_away = pd.DataFrame(
        {
            "Venue": [
                "Home",
                "Away",
            ],

            "Points": [
                derived_row[
                    "home_points"
                ],

                derived_row[
                    "away_points"
                ],
            ],
        }
    )


    home_away_figure = px.bar(
        home_away,

        x="Venue",
        y="Points",

        text="Points",

        labels={
            "Points":
                "Points Earned",
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


# ============================================================
# Recent finished matches
# ============================================================

st.markdown(
    "### Recent Finished Matches"
)


finished_team_matches = (
    team_matches[
        team_matches[
            "match_state"
        ]
        == "Finished"
    ]
    .copy()
)


finished_team_matches = (
    finished_team_matches
    .sort_values(
        "utc_date",
        ascending=False,
    )
    .head(8)
)


if finished_team_matches.empty:

    st.info(
        "No completed matches are available "
        "for this club."
    )


else:

    def team_result(
        row: pd.Series,
    ) -> str:
        """
        Determine result from selected team's perspective.
        """

        if (
            row[
                "home_team_id"
            ]
            == team_id
        ):

            if row[
                "result"
            ] == "H":

                return "W"


            if row[
                "result"
            ] == "D":

                return "D"


            return "L"


        if row[
            "result"
        ] == "A":

            return "W"


        if row[
            "result"
        ] == "D":

            return "D"


        return "L"


    finished_team_matches[
        "Team Result"
    ] = (
        finished_team_matches.apply(
            team_result,
            axis=1,
        )
    )


    finished_team_matches[
        "Date"
    ] = (
        finished_team_matches[
            "utc_date"
        ]
        .dt.tz_convert(
            ZoneInfo(
                "Europe/Madrid"
            )
        )
        .dt.strftime(
            "%d %b %Y"
        )
    )


    recent_display = (
        finished_team_matches[
            [
                "matchday",
                "Date",
                "home_badge_url",
                "home_team",
                "scoreline",
                "away_team",
                "away_badge_url",
                "Team Result",
            ]
        ]
        .copy()
    )


    recent_display.columns = [
        "MD",
        "Date",
        "Home Crest",
        "Home",
        "Score",
        "Away",
        "Away Crest",
        "Result",
    ]


    st.dataframe(
        recent_display,
        use_container_width=True,
        hide_index=True,

        column_config={

            "Home Crest":
                st.column_config.ImageColumn(
                    "",
                    width="small",
                ),

            "Away Crest":
                st.column_config.ImageColumn(
                    "",
                    width="small",
                ),

            "MD":
                st.column_config.NumberColumn(
                    "MD",
                    width="small",
                ),

            "Result":
                st.column_config.TextColumn(
                    "Result",
                    width="small",
                ),
        },
    )


# ============================================================
# Upcoming fixtures
# ============================================================

st.markdown(
    "### Upcoming Fixtures"
)


upcoming = (
    team_matches[
        team_matches[
            "match_state"
        ]
        == "Upcoming"
    ]
    .copy()
)


upcoming = (
    upcoming
    .sort_values(
        "utc_date"
    )
    .head(5)
)


if upcoming.empty:

    st.info(
        "No upcoming fixtures are currently available."
    )


else:

    madrid_dates = (
        upcoming[
            "utc_date"
        ]
        .dt.tz_convert(
            ZoneInfo(
                "Europe/Madrid"
            )
        )
    )


    upcoming[
        "Date"
    ] = (
        madrid_dates
        .dt.strftime(
            "%d %b %Y • %H:%M"
        )
        +
        " "
        +
        madrid_dates
        .dt.strftime(
            "%Z"
        )
    )


    upcoming_display = (
        upcoming[
            [
                "matchday",
                "Date",
                "home_badge_url",
                "home_team",
                "away_team",
                "away_badge_url",
                "status",
            ]
        ]
        .copy()
    )


    upcoming_display.columns = [
        "MD",
        "Date",
        "Home Crest",
        "Home",
        "Away",
        "Away Crest",
        "Status",
    ]


    st.dataframe(
        upcoming_display,
        use_container_width=True,
        hide_index=True,

        column_config={

            "Home Crest":
                st.column_config.ImageColumn(
                    "",
                    width="small",
                ),

            "Away Crest":
                st.column_config.ImageColumn(
                    "",
                    width="small",
                ),
        },
    )


# ============================================================
# Official vs derived
# ============================================================

st.markdown(
    "### Official vs Finished-Match Data"
)


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
                official[
                    "played"
                ],

                official[
                    "points"
                ],

                official[
                    "goals_for"
                ],

                official[
                    "goals_against"
                ],
            ],

            "Finished Matches": [
                derived_row[
                    "played"
                ],

                derived_row[
                    "points"
                ],

                derived_row[
                    "goals_for"
                ],

                derived_row[
                    "goals_against"
                ],
            ],
        }
    )


    comparison[
        "Difference"
    ] = (
        comparison[
            "Official Standings"
        ]
        - comparison[
            "Finished Matches"
        ]
    )


    st.dataframe(
        comparison,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# Footer
# ============================================================

render_footer()