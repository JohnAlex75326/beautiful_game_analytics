from __future__ import annotations

from html import escape
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
    get_match_status_summary,
    get_recent_matches,
    get_reconciliation_summary,
    get_team_performance,
    get_upcoming_matches,
)


# ============================================================
# Page configuration
# ============================================================

st.set_page_config(
    page_title="Overview | Beautiful Game Analytics",
    page_icon="⚽",
    layout="wide",
)


apply_branding()
render_sidebar()


# ============================================================
# Overview-specific styling
# ============================================================

st.markdown(
    """
    <style>

    /* ----------------------------------------------------
       League snapshot cards
       ---------------------------------------------------- */

    .bga-overview-snapshot-card {
        background:
            linear-gradient(
                145deg,
                #111821 0%,
                #0D131B 100%
            );

        border: 1px solid #202833;
        border-radius: 16px;

        padding: 16px 18px;

        min-height: 126px;

        margin-bottom: 12px;

        display: flex;
        align-items: center;

        gap: 16px;
    }


    .bga-overview-snapshot-crest {
        width: 58px;
        height: 58px;

        object-fit: contain;

        flex-shrink: 0;
    }


    .bga-overview-snapshot-content {
        min-width: 0;
    }


    .bga-overview-snapshot-label {
        color: #8995A4;

        font-size: 0.67rem;
        font-weight: 800;

        text-transform: uppercase;
        letter-spacing: 0.08em;

        margin-bottom: 5px;
    }


    .bga-overview-snapshot-team {
        font-size: 1.15rem;
        font-weight: 800;

        line-height: 1.1;
    }


    .bga-overview-snapshot-value {
        color: #2EE59D;

        font-size: 0.76rem;
        font-weight: 700;

        margin-top: 6px;
    }

        /* ----------------------------------------------------
       About project
       ---------------------------------------------------- */

    .bga-about-card {
        background:
            linear-gradient(
                145deg,
                #111821 0%,
                #0D131B 100%
            );

        border: 1px solid #202833;
        border-radius: 18px;

        padding:
            26px
            28px;

        margin:
            10px 0
            24px 0;
    }


    .bga-about-kicker {
        color: #2EE59D;

        font-size: 0.70rem;
        font-weight: 800;

        text-transform: uppercase;
        letter-spacing: 0.10em;

        margin-bottom: 14px;
    }


    .bga-about-body {
        color: #C2CBD5;

        font-size: 0.92rem;

        line-height: 1.75;

        max-width: 1000px;
    }


    .bga-about-body p {
        margin:
            0 0
            15px 0;
    }


    .bga-about-body p:last-child {
        margin-bottom: 0;
    }


    .bga-about-emphasis {
        color: #F5F7FA;

        font-weight: 700;
    }


    /* ----------------------------------------------------
       Match pulse card
       ---------------------------------------------------- */

    .bga-pulse-card {
        background:
            linear-gradient(
                145deg,
                #111821 0%,
                #0D131B 100%
            );

        border: 1px solid #202833;
        border-radius: 14px;

        padding: 12px 14px;

        margin-bottom: 10px;

        display: grid;

        grid-template-columns:
            minmax(0, 1fr)
            62px
            minmax(0, 1fr);

        gap: 10px;

        align-items: center;
    }


    .bga-pulse-team {
        display: flex;
        flex-direction: column;

        align-items: center;

        text-align: center;

        min-width: 0;
    }


    .bga-pulse-crest {
        width: 38px;
        height: 38px;

        object-fit: contain;

        margin-bottom: 5px;
    }


    .bga-pulse-team-name {
        font-size: 0.73rem;
        font-weight: 700;

        line-height: 1.1;

        overflow-wrap: anywhere;
    }


    .bga-pulse-score {
        text-align: center;

        font-size: 1.08rem;
        font-weight: 800;
    }


    .bga-pulse-vs {
        text-align: center;

        color: #768291;

        font-size: 0.67rem;
        font-weight: 800;

        letter-spacing: 0.08em;
    }


    .bga-pulse-meta {
        grid-column:
            1 / -1;

        border-top: 1px solid #202833;

        padding-top: 7px;

        color: #788493;

        text-align: center;

        font-size: 0.64rem;
    }


    /* ----------------------------------------------------
       Responsive
       ---------------------------------------------------- */

    @media (max-width: 850px) {

        .bga-overview-snapshot-card {
            min-height: auto;
        }

    }


    @media (max-width: 640px) {

        .bga-overview-snapshot-crest {
            width: 50px;
            height: 50px;
        }


        .bga-pulse-card {
            grid-template-columns:
                minmax(0, 1fr)
                52px
                minmax(0, 1fr);
        }


        .bga-pulse-crest {
            width: 32px;
            height: 32px;
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
def load_dashboard_data():
    """
    Load the business-ready datasets required
    by the Beautiful Game Analytics overview.
    """

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


if standings.empty:

    st.error(
        "No standings data is currently available."
    )

    st.stop()


# ============================================================
# Helper functions
# ============================================================

def safe_text(
    value: object,
    fallback: str = "—",
) -> str:
    """
    Return HTML-safe scalar text.
    """

    if pd.isna(value):

        return fallback


    return escape(
        str(value)
    )


def safe_url(
    value: object,
) -> str:
    """
    Return an HTML-safe URL.
    """

    if pd.isna(value):

        return ""


    return escape(
        str(value),
        quote=True,
    )


def render_snapshot_card(
    label: str,
    team_name: object,
    badge_url: object,
    value: str,
) -> str:
    """
    Render one crest-based league snapshot card.
    """

    safe_label = safe_text(
        label
    )

    safe_team = safe_text(
        team_name
    )

    safe_badge = safe_url(
        badge_url
    )

    safe_value = safe_text(
        value
    )


    crest_html = (
        f'<img '
        f'class="bga-overview-snapshot-crest" '
        f'src="{safe_badge}" '
        f'alt="{safe_team} crest" '
        f'loading="lazy">'
        if safe_badge
        else ""
    )


    return (
        '<div class="bga-overview-snapshot-card">'
        f'{crest_html}'
        '<div class="bga-overview-snapshot-content">'
        f'<div class="bga-overview-snapshot-label">'
        f'{safe_label}'
        '</div>'
        f'<div class="bga-overview-snapshot-team">'
        f'{safe_team}'
        '</div>'
        f'<div class="bga-overview-snapshot-value">'
        f'{safe_value}'
        '</div>'
        '</div>'
        '</div>'
    )


def format_match_datetime(
    value: object,
) -> str:
    """
    Format a UTC kickoff in mainland Spain time.
    """

    if pd.isna(value):

        return "Date unavailable"


    timestamp = pd.Timestamp(
        value
    )


    if timestamp.tzinfo is None:

        timestamp = timestamp.tz_localize(
            "UTC"
        )


    local_time = (
        timestamp
        .tz_convert(
            ZoneInfo(
                "Europe/Madrid"
            )
        )
    )


    return (
        local_time.strftime(
            "%d %b • %H:%M %Z"
        )
    )


def render_pulse_card(
    row: pd.Series,
    finished: bool,
) -> str:
    """
    Render a compact recent-result or upcoming-fixture card.
    """

    home_team = safe_text(
        row[
            "home_team"
        ]
    )

    away_team = safe_text(
        row[
            "away_team"
        ]
    )


    home_badge = safe_url(
        row[
            "home_badge_url"
        ]
    )

    away_badge = safe_url(
        row[
            "away_badge_url"
        ]
    )


    if finished:

        score_html = (
            '<div class="bga-pulse-score">'
            f'{int(row["home_score"])}'
            ' – '
            f'{int(row["away_score"])}'
            '</div>'
        )

    else:

        score_html = (
            '<div class="bga-pulse-vs">'
            'VS'
            '</div>'
        )


    date_text = (
        format_match_datetime(
            row[
                "utc_date"
            ]
        )
    )


    matchday_text = (
        f'Matchday {int(row["matchday"])}'
        if pd.notna(
            row[
                "matchday"
            ]
        )
        else "Matchday —"
    )


    return (
        '<div class="bga-pulse-card">'

        '<div class="bga-pulse-team">'
        f'<img '
        f'class="bga-pulse-crest" '
        f'src="{home_badge}" '
        f'alt="{home_team} crest" '
        f'loading="lazy">'
        f'<div class="bga-pulse-team-name">'
        f'{home_team}'
        '</div>'
        '</div>'

        f'{score_html}'

        '<div class="bga-pulse-team">'
        f'<img '
        f'class="bga-pulse-crest" '
        f'src="{away_badge}" '
        f'alt="{away_team} crest" '
        f'loading="lazy">'
        f'<div class="bga-pulse-team-name">'
        f'{away_team}'
        '</div>'
        '</div>'

        '<div class="bga-pulse-meta">'
        f'{matchday_text}'
        ' • '
        f'{date_text}'
        '</div>'

        '</div>'
    )


# ============================================================
# Header
# ============================================================

page_header(
    "Beautiful Game Analytics",
    (
        "La Liga matchday intelligence, team performance "
        "and source-data signals."
    ),
)


# ============================================================
# Core metrics
# ============================================================

finished_matches = (
    statuses.loc[
        statuses[
            "status"
        ]
        == "FINISHED",
        "match_count",
    ]
    .sum()
)


total_teams = int(
    reconciliation.iloc[0][
        "total_teams"
    ]
)


reconciled_teams = int(
    reconciliation.iloc[0][
        "reconciled_teams"
    ]
)


latest_matchday = int(
    standings[
        "snapshot_matchday"
    ]
    .max()
)


reconciliation_rate = (
    reconciled_teams
    / total_teams
    * 100
)


col1, col2, col3, col4 = (
    st.columns(4)
)


col1.metric(
    "Teams",
    total_teams,
)


col2.metric(
    "Finished Matches",
    int(
        finished_matches
    ),
)


col3.metric(
    "Latest Matchday",
    latest_matchday,
)


col4.metric(
    "Source Reconciliation",
    f"{reconciliation_rate:.0f}%",
)


# ============================================================
# Data-health notice
# ============================================================

if reconciliation_rate < 100:

    st.warning(
        f"{total_teams - reconciled_teams} teams currently "
        "have standings information ahead of the "
        "FINISHED-match feed. Official standings remain "
        "preserved independently."
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


left, right = st.columns(
    [
        2.2,
        1,
    ],
    gap="large",
)


# --------------------------------------------------
# Current standings
# --------------------------------------------------

with left:

    st.markdown(
        (
            '<div class="bga-section-title">'
            'Current Standings'
            '</div>'
        ),
        unsafe_allow_html=True,
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
                "goal_difference",
                "points",
            ]
        ]
        .head(10)
        .copy()
    )


    table.columns = [
        "Pos",
        "Crest",
        "Team",
        "P",
        "W",
        "D",
        "L",
        "GD",
        "Pts",
    ]


    overview_table_height = (
        38
        + len(table) * 35
    )


    st.dataframe(
        table,

        use_container_width=True,

        hide_index=True,

        height=overview_table_height,

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
        },
    )


# --------------------------------------------------
# Snapshot cards
# --------------------------------------------------

with right:

    st.markdown(
        (
            '<div class="bga-section-title">'
            'League Snapshot'
            '</div>'
        ),
        unsafe_allow_html=True,
    )


    snapshot_html = (
        render_snapshot_card(
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

        + render_snapshot_card(
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

        + render_snapshot_card(
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
    )


    st.markdown(
        snapshot_html,
        unsafe_allow_html=True,
    )


# ============================================================
# Matchday pulse
# ============================================================

st.markdown(
    (
        '<div class="bga-section-title">'
        'Matchday Pulse'
        '</div>'
    ),
    unsafe_allow_html=True,
)


recent_col, upcoming_col = (
    st.columns(
        2,
        gap="large",
    )
)


# --------------------------------------------------
# Recent results
# --------------------------------------------------

with recent_col:

    st.markdown(
        "#### Recent Results"
    )


    if recent_matches.empty:

        st.info(
            "No finished matches are currently available."
        )


    else:

        recent_html = "".join(
            render_pulse_card(
                row=row,
                finished=True,
            )

            for _, row
            in recent_matches.iterrows()
        )


        st.markdown(
            recent_html,
            unsafe_allow_html=True,
        )


# --------------------------------------------------
# Upcoming fixtures
# --------------------------------------------------

with upcoming_col:

    st.markdown(
        "#### Upcoming Fixtures"
    )


    if upcoming_matches.empty:

        st.info(
            "No upcoming fixtures are currently available."
        )


    else:

        upcoming_html = "".join(
            render_pulse_card(
                row=row,
                finished=False,
            )

            for _, row
            in upcoming_matches.iterrows()
        )


        st.markdown(
            upcoming_html,
            unsafe_allow_html=True,
        )


# ============================================================
# Finished-match performance
# ============================================================

st.markdown(
    (
        '<div class="bga-section-title">'
        'Finished-Match Performance'
        '</div>'
    ),
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
        "points_per_game":
            "Points Per Game",

        "short_name":
            "",
    },
)


figure.update_layout(
    yaxis={
        "categoryorder":
            "total ascending"
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

# ============================================================
# About this project
# ============================================================

st.markdown(
    (
        '<div class="bga-section-title">'
        'About This Project'
        '</div>'
    ),
    unsafe_allow_html=True,
)


about_html = (
    '<div class="bga-about-card">'

    '<div class="bga-about-kicker">'
    'Why I Built Beautiful Game Analytics'
    '</div>'

    '<div class="bga-about-body">'

    '<p>'
    'I built Beautiful Game Analytics as a way to bring '
    'together two things I care about: football and building '
    'reliable data products. Football has been a long-standing '
    'interest of mine, and this project gives me a place to '
    'explore the game through the engineering craft I work '
    'with professionally.'
    '</p>'

    '<p>'
    'The goal was '
    '<span class="bga-about-emphasis">'
    'not simply to build another scores dashboard.'
    '</span> '
    'I wanted to treat public football data like a real data '
    'product: ingest it reliably, preserve the source truth, '
    'model it in a warehouse, test it, reconcile competing '
    'views of the data, document the transformations, and then '
    'present the result in a way that actually feels native '
    'to football.'
    '</p>'

    '<p>'
    'It is also a portfolio project, but I want the engineering '
    'to be useful rather than decorative. If the standings and '
    'match feed disagree, the product should make that visible. '
    'If a metric is derived, it should be traceable. The '
    'architecture underneath the dashboard matters just as '
    'much to me as the visual product people interact with.'
    '</p>'

    '<p>'
    'As Beautiful Game Analytics evolves, my intention is to '
    'expand into more competitions, richer football-native '
    'analysis and selective AI features while keeping the same '
    'discipline around provenance, reliability and data '
    'quality. '
    '<span class="bga-about-emphasis">'
    'The ambition is simple: build a football product first, '
    'with production-minded data engineering underneath it.'
    '</span>'
    '</p>'

        '<p>'
    'The original spark for this project came from '
    '<a '
    'href="https://github.com/peter115342/soccer-tracker-DE-project" '
    'target="_blank" '
    'style="color: #2EE59D; font-weight: 700; '
    'text-decoration: none;">'
    'Peter&apos;s Football Statistics Tracker'
    '</a>, '
    'an end-to-end football data engineering project that '
    'showed me how the sport could be used as the foundation '
    'for a serious engineering portfolio project. Beautiful '
    'Game Analytics grew from that inspiration into my own '
    'take on the idea, with a different architecture, '
    'data model, analytical layer and product direction.'
    '</p>'

    '</div>'

    '</div>'
)


st.markdown(
    about_html,
    unsafe_allow_html=True,
)

# ============================================================
# Footer
# ============================================================

render_footer()