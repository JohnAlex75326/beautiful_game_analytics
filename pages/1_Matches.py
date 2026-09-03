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
    get_match_explorer,
)


# ============================================================
# Page configuration
# ============================================================

st.set_page_config(
    page_title="Matches | Beautiful Game Analytics",
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
       Match grid
       ---------------------------------------------------- */

    .bga-match-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 16px;
        margin-top: 12px;
        margin-bottom: 30px;
    }


    /* ----------------------------------------------------
       Match card
       ---------------------------------------------------- */

    .bga-match-card {
        background:
            linear-gradient(
                145deg,
                #111821 0%,
                #0D131B 100%
            );

        border: 1px solid #202833;
        border-radius: 18px;

        padding: 18px 20px 20px 20px;

        min-height: 245px;

        display: flex;
        flex-direction: column;

        transition:
            border-color 0.2s ease,
            transform 0.2s ease,
            box-shadow 0.2s ease;
    }


    .bga-match-card:hover {
        border-color: #364252;

        transform: translateY(-2px);

        box-shadow:
            0 10px 28px
            rgba(0, 0, 0, 0.22);
    }


    /* ----------------------------------------------------
       Card header
       ---------------------------------------------------- */

    .bga-match-header {
        display: flex;
        align-items: center;
        justify-content: space-between;

        margin-bottom: 18px;
    }


    .bga-matchday {
        color: #8995A4;

        font-size: 0.72rem;
        font-weight: 700;

        text-transform: uppercase;
        letter-spacing: 0.08em;
    }


    /* ----------------------------------------------------
       Match-state badges
       ---------------------------------------------------- */

    .bga-state {
        display: inline-flex;
        align-items: center;

        border-radius: 999px;

        padding: 5px 9px;

        font-size: 0.68rem;
        font-weight: 800;

        letter-spacing: 0.06em;
        text-transform: uppercase;
    }


    .bga-state-finished {
        background: #1A2430;
        color: #B4C0CF;

        border: 1px solid #2B3745;
    }


    .bga-state-upcoming {
        background:
            rgba(
                46,
                229,
                157,
                0.10
            );

        color: #2EE59D;

        border:
            1px solid
            rgba(
                46,
                229,
                157,
                0.28
            );
    }


    .bga-state-live {
        background:
            rgba(
                255,
                95,
                95,
                0.12
            );

        color: #FF6B6B;

        border:
            1px solid
            rgba(
                255,
                95,
                95,
                0.30
            );
    }


    .bga-state-other {
        background: #1A2430;
        color: #B4C0CF;

        border: 1px solid #2B3745;
    }


    /* ----------------------------------------------------
       Match body
       ---------------------------------------------------- */

    .bga-match-body {
        display: grid;

        grid-template-columns:
            minmax(0, 1fr)
            105px
            minmax(0, 1fr);

        align-items: center;

        flex: 1;

        gap: 12px;
    }


    /* ----------------------------------------------------
       Team
       ---------------------------------------------------- */

    .bga-team {
        display: flex;
        flex-direction: column;

        align-items: center;

        min-width: 0;

        text-align: center;
    }


    .bga-crest-shell {
        width: 82px;
        height: 82px;

        display: flex;
        align-items: center;
        justify-content: center;

        margin-bottom: 10px;
    }


    .bga-crest {
        display: block;

        width: 72px;
        height: 72px;

        object-fit: contain;
    }


    .bga-team-name {
        font-size: 0.96rem;
        font-weight: 700;

        line-height: 1.2;

        overflow-wrap: anywhere;
    }


    .bga-team-tla {
        margin-top: 5px;

        color: #748091;

        font-size: 0.68rem;
        font-weight: 700;

        letter-spacing: 0.08em;
    }


    /* ----------------------------------------------------
       Score
       ---------------------------------------------------- */

    .bga-score-block {
        display: flex;
        flex-direction: column;

        align-items: center;
        justify-content: center;

        text-align: center;
    }


    .bga-score {
        font-size: 2rem;
        font-weight: 800;

        letter-spacing: -0.04em;
        line-height: 1;
    }


    .bga-vs {
        color: #6F7B89;

        font-size: 0.80rem;
        font-weight: 800;

        letter-spacing: 0.10em;
    }


    /* ----------------------------------------------------
       Card footer
       ---------------------------------------------------- */

    .bga-match-footer {
        border-top: 1px solid #202833;

        margin-top: 18px;
        padding-top: 12px;

        text-align: center;

        color: #8F9BAA;

        font-size: 0.76rem;
    }


    .bga-timezone {
        color: #657181;

        font-size: 0.64rem;

        margin-left: 4px;
    }


    /* ----------------------------------------------------
       Empty state
       ---------------------------------------------------- */

    .bga-empty-state {
        border: 1px dashed #2B3745;
        border-radius: 16px;

        padding: 34px;

        text-align: center;

        color: #8995A4;

        margin: 14px 0 28px 0;
    }

    /* ----------------------------------------------------
       Matchday navigation
    ---------------------------------------------------- */

    .bga-matchday-nav-header {
        display: flex;
        align-items: center;
        justify-content: space-between;

        gap: 12px;

        margin:
            8px 0
            8px 0;
    }


    .bga-matchday-nav-label {
        color: #8995A4;

        font-size: 0.72rem;
        font-weight: 800;

        text-transform: uppercase;
        letter-spacing: 0.09em;
    }


    .bga-matchday-nav-context {
        color: #66717F;

        font-size: 0.72rem;
    }


    .bga-matchday-viewing {
        color: #8995A4;

        font-size: 0.72rem;

        text-align: center;

        margin:
            4px 0
            18px 0;
    }


    .bga-matchday-viewing strong {
        color: #2EE59D;
    }


    /* Streamlit buttons used by matchday ribbon */

    div[data-testid="stButton"] > button {
        border-radius: 12px;

        min-height: 42px;

        font-weight: 750;

        border-color: #283340;

        transition:
            border-color 0.2s ease,
            transform 0.2s ease;
    }


    div[data-testid="stButton"] > button:hover {
        border-color: #2EE59D;

        transform: translateY(-1px);
    }


    div[data-testid="stButton"] > button:disabled {
        opacity: 1;

        background:
            rgba(
                46,
                229,
                157,
                0.12
            );

        border-color:
            rgba(
                46,
                229,
                157,
                0.45
            );

        color: #2EE59D;
    }


    /* ----------------------------------------------------
       Tablet
       ---------------------------------------------------- */

    @media (max-width: 1000px) {

        .bga-match-grid {
            grid-template-columns: 1fr;
        }

    }


    /* ----------------------------------------------------
       Mobile
       ---------------------------------------------------- */

    @media (max-width: 640px) {

        .bga-match-card {
            padding: 15px 14px 16px 14px;

            min-height: 220px;
        }


        .bga-match-body {
            grid-template-columns:
                minmax(0, 1fr)
                72px
                minmax(0, 1fr);

            gap: 8px;
        }


        .bga-crest-shell {
            width: 60px;
            height: 60px;
        }


        .bga-crest {
            width: 54px;
            height: 54px;
        }


        .bga-team-name {
            font-size: 0.82rem;
        }


        .bga-team-tla {
            font-size: 0.62rem;
        }


        .bga-score {
            font-size: 1.55rem;
        }


        .bga-match-footer {
            font-size: 0.68rem;
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
def load_matches() -> pd.DataFrame:
    """
    Load the business-ready match explorer mart.
    """

    return get_match_explorer()


matches = load_matches()


if matches.empty:

    st.error(
        "No match data is currently available."
    )

    st.stop()


matches["utc_date"] = pd.to_datetime(
    matches["utc_date"],
    utc=True,
)


# ============================================================
# Helper functions
# ============================================================

def determine_default_matchday(
    dataframe: pd.DataFrame,
) -> int | str:
    """
    Determine the most relevant matchday when
    the page first opens.

    Priority:
    1. Live matchday
    2. Latest finished matchday
    3. Earliest upcoming matchday
    4. All
    """

    live_matchdays = (
        dataframe.loc[
            dataframe["match_state"].eq("Live"),
            "matchday",
        ]
        .dropna()
        .astype(int)
    )


    if not live_matchdays.empty:

        return int(
            live_matchdays.min()
        )


    finished_matchdays = (
        dataframe.loc[
            dataframe["match_state"].eq("Finished"),
            "matchday",
        ]
        .dropna()
        .astype(int)
    )


    if not finished_matchdays.empty:

        return int(
            finished_matchdays.max()
        )


    upcoming_matchdays = (
        dataframe.loc[
            dataframe["match_state"].eq("Upcoming"),
            "matchday",
        ]
        .dropna()
        .astype(int)
    )


    if not upcoming_matchdays.empty:

        return int(
            upcoming_matchdays.min()
        )


    return "All"

def get_matchday_window(
    matchdays: list[int],
    selected_matchday: int | str,
    fallback_matchday: int | str,
    window_size: int = 7,
) -> list[int]:
    """
    Return a centered window of matchdays for
    football-style navigation.
    """

    if not matchdays:

        return []


    if (
        isinstance(
            selected_matchday,
            int,
        )
        and selected_matchday
        in matchdays
    ):

        anchor = selected_matchday


    elif (
        isinstance(
            fallback_matchday,
            int,
        )
        and fallback_matchday
        in matchdays
    ):

        anchor = fallback_matchday


    else:

        anchor = matchdays[0]


    anchor_index = (
        matchdays.index(
            anchor
        )
    )


    half_window = (
        window_size // 2
    )


    start_index = max(
        0,
        anchor_index
        - half_window,
    )


    start_index = min(
        start_index,
        max(
            0,
            len(matchdays)
            - window_size,
        ),
    )


    end_index = (
        start_index
        + window_size
    )


    return matchdays[
        start_index:end_index
    ]


def set_selected_matchday(
    matchday: int | str,
) -> None:
    """
    Update matchday navigation state.
    """

    st.session_state[
        "selected_matchday"
    ] = matchday

    st.session_state[
        "matchday_select"
    ] = matchday

def safe_text(
    value: object,
    fallback: str = "—",
) -> str:
    """
    Convert a scalar value to escaped HTML-safe text.
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
    Convert a scalar URL to an HTML-safe attribute value.
    """

    if pd.isna(value):

        return ""


    return escape(
        str(value),
        quote=True,
    )


def render_state_badge(
    match_state: str,
) -> str:
    """
    Render the visual match-state pill.

    Keep generated HTML compact because indented
    HTML may be interpreted by Markdown as code.
    """

    normalized_state = str(
        match_state
    ).strip()


    css_class = {
        "Finished":
            "bga-state-finished",

        "Live":
            "bga-state-live",

        "Upcoming":
            "bga-state-upcoming",

        "Other":
            "bga-state-other",

    }.get(
        normalized_state,
        "bga-state-other",
    )


    return (
        f'<span class="bga-state {css_class}">'
        f'{escape(normalized_state)}'
        '</span>'
    )


def render_score(
    row: pd.Series,
) -> str:
    """
    Render the score for finished/live games.

    Upcoming fixtures display VS.
    """

    match_state = str(
        row["match_state"]
    )


    if match_state in {
        "Finished",
        "Live",
    }:

        home_score = row[
            "home_score"
        ]

        away_score = row[
            "away_score"
        ]


        if (
            pd.notna(home_score)
            and pd.notna(away_score)
        ):

            return (
                '<div class="bga-score">'
                f'{int(home_score)} – {int(away_score)}'
                '</div>'
            )


    return (
        '<div class="bga-vs">'
        'VS'
        '</div>'
    )


def render_crest(
    badge_url: object,
    team_name: str,
) -> str:
    """
    Render a club crest.

    A fallback football icon is retained for
    defensive UI behavior.
    """

    url = safe_url(
        badge_url
    )


    if not url:

        return (
            '<div class="bga-crest-shell">'
            '⚽'
            '</div>'
        )


    safe_team_name = escape(
        team_name,
        quote=True,
    )


    return (
        '<div class="bga-crest-shell">'
        '<img '
        'class="bga-crest" '
        f'src="{url}" '
        f'alt="{safe_team_name} crest" '
        'loading="lazy">'
        '</div>'
    )


def render_match_card(
    row: pd.Series,
) -> str:
    """
    Build one complete football match card.

    Generated HTML deliberately contains no leading
    indentation so Streamlit Markdown does not
    interpret HTML elements as code blocks.
    """

    # --------------------------------------------------
    # Matchday
    # --------------------------------------------------

    if pd.notna(
        row["matchday"]
    ):

        matchday = int(
            row["matchday"]
        )

    else:

        matchday = "—"


    # --------------------------------------------------
    # Date / time
    # --------------------------------------------------

    match_datetime = row[
        "utc_date"
    ]


    if pd.notna(
        match_datetime
    ):

        madrid_datetime = (
            match_datetime
            .tz_convert(
                ZoneInfo(
                    "Europe/Madrid"
                )
            )
        )


        date_text = (
            madrid_datetime
            .strftime(
                "%d %b %Y • %H:%M"
            )
        )

    else:

        date_text = (
            "Date unavailable"
        )


    # --------------------------------------------------
    # Team values
    # --------------------------------------------------

    raw_home_team = (
        str(
            row["home_team"]
        )
        if pd.notna(
            row["home_team"]
        )
        else "Home team"
    )


    raw_away_team = (
        str(
            row["away_team"]
        )
        if pd.notna(
            row["away_team"]
        )
        else "Away team"
    )


    home_team = safe_text(
        row["home_team"]
    )

    away_team = safe_text(
        row["away_team"]
    )


    home_tla = safe_text(
        row["home_tla"]
    )

    away_tla = safe_text(
        row["away_tla"]
    )


    home_crest = render_crest(
        row["home_badge_url"],
        raw_home_team,
    )


    away_crest = render_crest(
        row["away_badge_url"],
        raw_away_team,
    )


    # --------------------------------------------------
    # State / score
    # --------------------------------------------------

    state_badge = (
        render_state_badge(
            row["match_state"]
        )
    )


    score = (
        render_score(
            row
        )
    )


    # --------------------------------------------------
    # Compact HTML
    # --------------------------------------------------

    return (
        '<article class="bga-match-card">'

        '<div class="bga-match-header">'
        f'<div class="bga-matchday">Matchday {matchday}</div>'
        f'{state_badge}'
        '</div>'

        '<div class="bga-match-body">'

        '<div class="bga-team">'
        f'{home_crest}'
        f'<div class="bga-team-name">{home_team}</div>'
        f'<div class="bga-team-tla">{home_tla}</div>'
        '</div>'

        '<div class="bga-score-block">'
        f'{score}'
        '</div>'

        '<div class="bga-team">'
        f'{away_crest}'
        f'<div class="bga-team-name">{away_team}</div>'
        f'<div class="bga-team-tla">{away_tla}</div>'
        '</div>'

        '</div>'

        '<div class="bga-match-footer">'
        f'{date_text}'
        '<span class="bga-timezone"> CEST</span>'
        '</div>'

        '</article>'
    )


# ============================================================
# Header
# ============================================================

page_header(
    "Matches",
    (
        "Fixtures, results and matchday "
        "intelligence across La Liga."
    ),
)


# ============================================================
# Filter preparation
# ============================================================

st.markdown(
    "### Match Explorer"
)


matchdays = sorted(
    matches["matchday"]
    .dropna()
    .astype(int)
    .unique()
    .tolist()
)


matchday_options = (
    ["All"]
    + matchdays
)


default_matchday = (
    determine_default_matchday(
        matches
    )
)

if (
    "selected_matchday"
    not in st.session_state
):

    st.session_state[
        "selected_matchday"
    ] = default_matchday


if (
    st.session_state[
        "selected_matchday"
    ]
    not in matchday_options
):

    st.session_state[
        "selected_matchday"
    ] = default_matchday


teams = sorted(
    set(
        matches["home_team"]
        .dropna()
    )
    |
    set(
        matches["away_team"]
        .dropna()
    )
)


states = [
    "All",
    "Finished",
    "Live",
    "Upcoming",
    "Other",
]

# ============================================================
# Matchday ribbon
# ============================================================

selected_matchday = (
    st.session_state[
        "selected_matchday"
    ]
)


visible_matchdays = (
    get_matchday_window(
        matchdays=matchdays,
        selected_matchday=selected_matchday,
        fallback_matchday=default_matchday,
        window_size=7,
    )
)


st.markdown(
    (
        '<div class="bga-matchday-nav-header">'

        '<div class="bga-matchday-nav-label">'
        'Matchday'
        '</div>'

        '<div class="bga-matchday-nav-context">'
        'Browse the season'
        '</div>'

        '</div>'
    ),
    unsafe_allow_html=True,
)


if visible_matchdays:

    navigation_columns = (
        st.columns(
            [
                0.55,
                *(
                    [1] * len(
                        visible_matchdays
                    )
                ),
                0.55,
            ]
        )
    )


    # --------------------------------------------------------
    # Previous
    # --------------------------------------------------------

    with navigation_columns[0]:

        if (
            isinstance(
                selected_matchday,
                int,
            )
            and selected_matchday
            in matchdays
        ):

            selected_index = (
                matchdays.index(
                    selected_matchday
                )
            )

        else:

            selected_index = (
                matchdays.index(
                    default_matchday
                )
                if default_matchday
                in matchdays
                else 0
            )


        previous_disabled = (
            selected_index <= 0
        )


        if st.button(
            "‹",
            key="matchday_previous",
            disabled=previous_disabled,
            use_container_width=True,
        ):

            set_selected_matchday(
                matchdays[
                    selected_index - 1
                ]
            )

            st.rerun()


    # --------------------------------------------------------
    # Matchday buttons
    # --------------------------------------------------------

    for index, matchday in enumerate(
        visible_matchdays,
        start=1,
    ):

        with navigation_columns[index]:

            is_selected = (
                selected_matchday
                == matchday
            )


            is_current = (
                default_matchday
                == matchday
            )


            label = (
                f"MD{matchday}"
            )


            if is_current:

                label += " •"


            if st.button(
                label,
                key=(
                    f"matchday_button_"
                    f"{matchday}"
                ),
                disabled=is_selected,
                use_container_width=True,
            ):

                set_selected_matchday(
                    matchday
                )

                st.rerun()


    # --------------------------------------------------------
    # Next
    # --------------------------------------------------------

    with navigation_columns[-1]:

        next_disabled = (
            selected_index
            >= len(matchdays) - 1
        )


        if st.button(
            "›",
            key="matchday_next",
            disabled=next_disabled,
            use_container_width=True,
        ):

            set_selected_matchday(
                matchdays[
                    selected_index + 1
                ]
            )

            st.rerun()

if (
    selected_matchday
    == "All"
):

    viewing_text = (
        "Viewing all matchdays"
    )


elif (
    selected_matchday
    == default_matchday
):

    viewing_text = (
        f'Viewing <strong>'
        f'Matchday {selected_matchday}'
        f'</strong> • Current'
    )


else:

    viewing_text = (
        f'Viewing <strong>'
        f'Matchday {selected_matchday}'
        f'</strong>'
    )


st.markdown(
    (
        '<div class="bga-matchday-viewing">'
        f'{viewing_text}'
        '</div>'
    ),
    unsafe_allow_html=True,
)

if (
    "matchday_select"
    not in st.session_state
):

    st.session_state[
        "matchday_select"
    ] = (
        st.session_state[
            "selected_matchday"
        ]
    )


# ============================================================
# Filters
# ============================================================

filter_col1, filter_col2, filter_col3 = (
    st.columns(3)
)


def sync_matchday_select() -> None:
    """
    Synchronize fallback selectbox with ribbon.
    """

    st.session_state[
        "selected_matchday"
    ] = (
        st.session_state[
            "matchday_select"
        ]
    )


with filter_col1:

    st.selectbox(
        "Jump to Matchday",
        options=matchday_options,
        key="matchday_select",
        on_change=sync_matchday_select,
    )


selected_matchday = (
    st.session_state[
        "selected_matchday"
    ]
)


with filter_col2:

    selected_team = (
        st.selectbox(
            "Team",
            options=(
                ["All"]
                + teams
            ),
        )
    )


with filter_col3:

    selected_state = (
        st.selectbox(
            "Match State",
            options=states,
        )
    )
# ============================================================
# Apply filters
# ============================================================

filtered = (
    matches.copy()
)


if selected_matchday != "All":

    filtered = filtered[
        filtered["matchday"]
        == selected_matchday
    ]


if selected_team != "All":

    filtered = filtered[
        (
            filtered["home_team"]
            == selected_team
        )
        |
        (
            filtered["away_team"]
            == selected_team
        )
    ]


if selected_state != "All":

    filtered = filtered[
        filtered["match_state"]
        == selected_state
    ]


filtered = (
    filtered
    .sort_values(
        [
            "utc_date",
            "matchday",
        ]
    )
    .reset_index(
        drop=True
    )
)


# ============================================================
# KPIs
# ============================================================

total_matches = len(
    filtered
)


finished_matches = int(
    filtered["match_state"]
    .eq(
        "Finished"
    )
    .sum()
)


live_matches = int(
    filtered["match_state"]
    .eq(
        "Live"
    )
    .sum()
)


upcoming_matches = int(
    filtered["match_state"]
    .eq(
        "Upcoming"
    )
    .sum()
)


kpi1, kpi2, kpi3, kpi4 = (
    st.columns(4)
)


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


# ============================================================
# Match cards
# ============================================================

st.markdown(
    "### Fixtures & Results"
)


if filtered.empty:

    st.markdown(
        (
            '<div class="bga-empty-state">'
            'No fixtures match the selected filters.'
            '</div>'
        ),
        unsafe_allow_html=True,
    )


else:

    cards_html = "".join(
        render_match_card(
            row
        )
        for _, row
        in filtered.iterrows()
    )


    # IMPORTANT:
    #
    # Keep this HTML compact.
    # Leading indentation can cause Markdown to display
    # HTML tags as literal code instead of rendering them.

    match_grid_html = (
        '<div class="bga-match-grid">'
        f'{cards_html}'
        '</div>'
    )


    st.markdown(
        match_grid_html,
        unsafe_allow_html=True,
    )


# ============================================================
# Analytics
# ============================================================

st.markdown(
    "### Match Analytics"
)


left, right = st.columns(
    2,
    gap="large",
)


# --------------------------------------------------
# Match status
# --------------------------------------------------

with left:

    st.markdown(
        "#### Match Status"
    )


    status_summary = (
        filtered
        .groupby(
            "match_state",
            as_index=False,
        )
        .size()
        .rename(
            columns={
                "size":
                    "matches",
            }
        )
    )


    if status_summary.empty:

        st.info(
            "No match-state data "
            "matches the current filters."
        )


    else:

        status_figure = (
            px.bar(
                status_summary,
                x="match_state",
                y="matches",
                labels={
                    "match_state":
                        "",

                    "matches":
                        "Matches",
                },
            )
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


# --------------------------------------------------
# Finished-match goals
# --------------------------------------------------

with right:

    st.markdown(
        "#### Finished-Match Goals"
    )


    finished = (
        filtered[
            filtered["match_state"]
            == "Finished"
        ]
        .copy()
    )


    if finished.empty:

        st.info(
            "No finished matches "
            "match the current filters."
        )


    else:

        finished[
            "total_goals"
        ] = (
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


        goals_figure = (
            px.line(
                goals_by_matchday,

                x="matchday",
                y="goals_per_match",

                markers=True,

                labels={
                    "matchday":
                        "Matchday",

                    "goals_per_match":
                        "Goals / Match",
                },
            )
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


# ============================================================
# Source-state context
# ============================================================

if live_matches > 0:

    st.info(
        "Live-status records reflect the latest stored "
        "football-data.org snapshot. The public dashboard "
        "does not call the source API directly."
    )


# ============================================================
# Footer
# ============================================================

render_footer()