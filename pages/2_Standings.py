from __future__ import annotations

from html import escape

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


# ============================================================
# Page configuration
# ============================================================

st.set_page_config(
    page_title="Standings | Beautiful Game Analytics",
    page_icon="⚽",
    layout="wide",
)


apply_branding()
render_sidebar()


# ============================================================
# Page-specific styling
# ============================================================

st.markdown(
    """
    <style>

    /* ----------------------------------------------------
       League highlight grid
       ---------------------------------------------------- */

    .bga-league-highlights {
        display: grid;

        grid-template-columns:
            repeat(3, minmax(0, 1fr));

        gap: 16px;

        margin:
            10px 0
            20px 0;
    }


    /* ----------------------------------------------------
       League highlight card
       ---------------------------------------------------- */

    .bga-highlight-card {
        background:
            linear-gradient(
                145deg,
                #111821 0%,
                #0D131B 100%
            );

        border: 1px solid #202833;

        border-radius: 18px;

        min-height: 170px;

        padding: 18px 20px;

        display: flex;

        flex-direction: column;

        align-items: center;

        justify-content: center;

        text-align: center;
    }


    .bga-highlight-label {
        color: #8995A4;

        font-size: 0.68rem;

        font-weight: 800;

        text-transform: uppercase;

        letter-spacing: 0.09em;

        margin-bottom: 12px;
    }


    .bga-highlight-crest {
        width: 58px;

        height: 58px;

        object-fit: contain;

        margin-bottom: 8px;
    }


    .bga-highlight-team {
        font-size: 1rem;

        font-weight: 750;

        line-height: 1.15;
    }


    .bga-highlight-value {
        color: #2EE59D;

        font-size: 0.78rem;

        font-weight: 700;

        margin-top: 5px;
    }


    /* ----------------------------------------------------
       Table context
       ---------------------------------------------------- */

    .bga-table-note {
        color: #8995A4;

        font-size: 0.76rem;

        margin-top: 8px;

        margin-bottom: 18px;
    }


    /* ----------------------------------------------------
       Responsive
       ---------------------------------------------------- */

    @media (max-width: 900px) {

        .bga-league-highlights {
            grid-template-columns: 1fr;
        }

    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# Data loading
# ============================================================

@st.cache_data(ttl=300)
def load_standings_data():
    """
    Load official standings and reconciliation summary.
    """

    return (
        get_current_standings(),
        get_reconciliation_summary(),
    )


standings, reconciliation = (
    load_standings_data()
)


if standings.empty:

    st.error(
        "No standings data is currently available."
    )

    st.stop()


# ============================================================
# Helper functions
# ============================================================

def render_highlight_card(
    label: str,
    team_name: str,
    badge_url: str,
    value: str,
) -> str:
    """
    Render one league highlight card.
    """

    safe_label = escape(
        str(label)
    )

    safe_team = escape(
        str(team_name)
    )

    safe_value = escape(
        str(value)
    )

    safe_badge = escape(
        str(badge_url),
        quote=True,
    )


    return (
        '<div class="bga-highlight-card">'
        f'<div class="bga-highlight-label">{safe_label}</div>'
        f'<img '
        f'class="bga-highlight-crest" '
        f'src="{safe_badge}" '
        f'alt="{safe_team} crest" '
        f'loading="lazy">'
        f'<div class="bga-highlight-team">{safe_team}</div>'
        f'<div class="bga-highlight-value">{safe_value}</div>'
        '</div>'
    )


# ============================================================
# Header
# ============================================================

page_header(
    "Standings",
    (
        "Official La Liga table, league position and "
        "source-reconciliation status."
    ),
)


# ============================================================
# League snapshot
# ============================================================

leader = (
    standings.iloc[0]
)


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
    reconciliation.iloc[0][
        "reconciled_teams"
    ]
)


total_teams = int(
    reconciliation.iloc[0][
        "total_teams"
    ]
)


reconciliation_rate = (
    reconciled_teams
    / total_teams
    * 100
)


# ============================================================
# Club highlights
# ============================================================

highlight_html = (
    '<div class="bga-league-highlights">'

    + render_highlight_card(
        label="League Leader",

        team_name=(
            leader[
                "short_name"
            ]
        ),

        badge_url=(
            leader[
                "sportsdb_badge_url"
            ]
        ),

        value=(
            f"{int(leader['points'])} points"
        ),
    )

    + render_highlight_card(
        label="Best Attack",

        team_name=(
            best_attack[
                "short_name"
            ]
        ),

        badge_url=(
            best_attack[
                "sportsdb_badge_url"
            ]
        ),

        value=(
            f"{int(best_attack['goals_for'])} goals"
        ),
    )

    + render_highlight_card(
        label="Best Defence",

        team_name=(
            best_defence[
                "short_name"
            ]
        ),

        badge_url=(
            best_defence[
                "sportsdb_badge_url"
            ]
        ),

        value=(
            f"{int(best_defence['goals_against'])} conceded"
        ),
    )

    + '</div>'
)


st.markdown(
    highlight_html,
    unsafe_allow_html=True,
)


# ============================================================
# League metadata
# ============================================================

health_col1, health_col2 = (
    st.columns(2)
)


health_col1.metric(
    "Current Matchday",
    int(
        standings.iloc[0][
            "snapshot_matchday"
        ]
    ),
)


health_col2.metric(
    "Source Reconciliation",
    f"{reconciliation_rate:.0f}%",

    (
        f"{reconciled_teams}/"
        f"{total_teams} teams"
    ),
)


# ============================================================
# Reconciliation context
# ============================================================

if reconciliation_rate < 100:

    st.warning(
        f"{total_teams - reconciled_teams} teams have "
        "official standings information ahead of the "
        "FINISHED-match feed. The table below preserves "
        "the official standings snapshot."
    )


# ============================================================
# Current league table
# ============================================================

st.markdown(
    "### Current League Table"
)


table = (
    standings[
        [
            "position",
            "sportsdb_badge_url",
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
    ]
    .copy()
)


table[
    "is_reconciled"
] = (
    table[
        "is_reconciled"
    ]
    .map(
        {
            True:
                "✓ Synced",

            False:
                "⚠ Pending",
        }
    )
)


table.columns = [
    "Pos",
    "Crest",
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


# --------------------------------------------------
# Dynamic table height
#
# Header + visible team rows.
#
# This prevents a large empty section beneath
# the final club in competitions with fewer rows.
# --------------------------------------------------

table_height = (
    38
    + len(table) * 35
)


st.dataframe(
    table,

    use_container_width=True,

    hide_index=True,

    height=table_height,

    column_config={

        "Pos":
            st.column_config.NumberColumn(
                "Pos",
                width="small",
            ),

        "Crest":
            st.column_config.ImageColumn(
                "",
                width="small",
                help="Club crest",
            ),

        "Team":
            st.column_config.TextColumn(
                "Team",
                width="medium",
            ),

        "P":
            st.column_config.NumberColumn(
                "P",
                width="small",
            ),

        "W":
            st.column_config.NumberColumn(
                "W",
                width="small",
            ),

        "D":
            st.column_config.NumberColumn(
                "D",
                width="small",
            ),

        "L":
            st.column_config.NumberColumn(
                "L",
                width="small",
            ),

        "GF":
            st.column_config.NumberColumn(
                "GF",
                width="small",
            ),

        "GA":
            st.column_config.NumberColumn(
                "GA",
                width="small",
            ),

        "GD":
            st.column_config.NumberColumn(
                "GD",
                width="small",
            ),

        "Pts":
            st.column_config.NumberColumn(
                "Pts",
                width="small",
            ),

        "Data":
            st.column_config.TextColumn(
                "Data",

                help=(
                    "Whether official standings totals "
                    "currently reconcile with matches "
                    "marked FINISHED by the source API."
                ),
            ),
    },
)


st.markdown(
    (
        '<div class="bga-table-note">'
        'Displayed positions are preserved exactly as '
        'supplied by the source. Tied positions are '
        'therefore possible.'
        '</div>'
    ),
    unsafe_allow_html=True,
)


# ============================================================
# Points race
# ============================================================

st.markdown(
    "### Points Race"
)


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
        "points":
            "Points",

        "short_name":
            "",
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


# ============================================================
# Goal performance
# ============================================================

st.markdown(
    "### Goal Performance"
)


goal_col1, goal_col2 = (
    st.columns(
        2,
        gap="large",
    )
)


# --------------------------------------------------
# Goal difference
# --------------------------------------------------

with goal_col1:

    st.markdown(
        "#### Goal Difference"
    )


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
            "goal_difference":
                "Goal Difference",

            "short_name":
                "",
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


# --------------------------------------------------
# Goals scored
# --------------------------------------------------

with goal_col2:

    st.markdown(
        "#### Goals Scored"
    )


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
            "goals_for":
                "Goals",

            "short_name":
                "",
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


# ============================================================
# Reconciliation detail
# ============================================================

st.markdown(
    "### Data Reconciliation"
)


unreconciled = (
    standings[
        standings[
            "is_reconciled"
        ]
        == False
    ]
    .copy()
)


if unreconciled.empty:

    st.success(
        "All teams currently reconcile with the "
        "FINISHED-match feed."
    )


else:

    st.info(
        f"{len(unreconciled)} teams currently have "
        "standings totals ahead of the "
        "FINISHED-match feed."
    )


    reconciliation_table = (
        unreconciled[
            [
                "sportsdb_badge_url",
                "position",
                "short_name",
                "played",
                "points",
            ]
        ]
        .copy()
    )


    reconciliation_table.columns = [
        "Crest",
        "Pos",
        "Team",
        "Official Played",
        "Official Points",
    ]


    reconciliation_table_height = (
        38
        + len(
            reconciliation_table
        )
        * 35
    )


    st.dataframe(
        reconciliation_table,

        use_container_width=True,

        hide_index=True,

        height=(
            reconciliation_table_height
        ),

        column_config={

            "Crest":
                st.column_config.ImageColumn(
                    "",
                    width="small",
                ),

            "Pos":
                st.column_config.NumberColumn(
                    "Pos",
                    width="small",
                ),

            "Official Played":
                st.column_config.NumberColumn(
                    "Official Played",
                    width="small",
                ),

            "Official Points":
                st.column_config.NumberColumn(
                    "Official Points",
                    width="small",
                ),
        },
    )


# ============================================================
# Footer
# ============================================================

render_footer()