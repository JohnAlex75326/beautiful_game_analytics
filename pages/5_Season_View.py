from __future__ import annotations

import pandas as pd
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
)


# ============================================================
# Page configuration
# ============================================================

st.set_page_config(
    page_title="Season View | Beautiful Game Analytics",
    page_icon="🗓️",
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

    .bga-matrix-legend {
        display: flex;
        flex-wrap: wrap;

        gap:
            10px
            20px;

        margin:
            10px 0
            8px 0;
    }


    .bga-matrix-legend-item {
        display: inline-flex;

        align-items: center;

        gap: 7px;

        color: #AAB4C0;

        font-size: 0.74rem;
        font-weight: 700;
    }


    .bga-matrix-dot {
        width: 9px;
        height: 9px;

        border-radius: 50%;
    }


    .bga-matrix-home-win {
        background: #2EE59D;
    }


    .bga-matrix-draw {
        background: #8995A4;
    }


    .bga-matrix-away-win {
        background: #FF8585;
    }


    .bga-matrix-upcoming {
        background: #394452;
    }


    .bga-matrix-context {
        color: #788493;

        font-size: 0.73rem;

        margin-bottom: 18px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# Data
# ============================================================

@st.cache_data(ttl=300)
def load_season_data():
    """
    Load the current table and full fixture set.
    """

    return (
        get_current_standings(),
        get_match_explorer(),
    )


standings, matches = (
    load_season_data()
)


if standings.empty:

    st.error(
        "No standings data is currently available."
    )

    st.stop()


if matches.empty:

    st.error(
        "No fixture data is currently available."
    )

    st.stop()


# ============================================================
# Header
# ============================================================

page_header(
    "Season View",
    (
        "A football-native view of the La Liga season: "
        "every club against every opponent."
    ),
)


# ============================================================
# Team order
# ============================================================

team_order = (
    standings[
        "short_name"
    ]
    .dropna()
    .tolist()
)


team_tla = (
    standings[
        [
            "short_name",
            "tla",
        ]
    ]
    .drop_duplicates()
    .set_index(
        "short_name"
    )[
        "tla"
    ]
    .to_dict()
)


# ============================================================
# Season metrics
# ============================================================

finished_matches = int(
    (
        matches[
            "match_state"
        ]
        == "Finished"
    )
    .sum()
)


upcoming_matches = int(
    (
        matches[
            "match_state"
        ]
        == "Upcoming"
    )
    .sum()
)


total_matches = len(
    matches
)


completion_rate = (
    finished_matches
    / total_matches
    * 100
    if total_matches
    else 0
)


metric_col1, metric_col2, metric_col3 = (
    st.columns(3)
)


metric_col1.metric(
    "Played",
    finished_matches,
)


metric_col2.metric(
    "Remaining",
    upcoming_matches,
)


metric_col3.metric(
    "Season Complete",
    f"{completion_rate:.0f}%",
)


# ============================================================
# Fixture matrix
# ============================================================

st.markdown(
    "### Fixture Matrix"
)


st.caption(
    (
        "Rows are the home club. Columns are the away club. "
        "Finished fixtures show the score from the home team's "
        "perspective."
    )
)


legend_html = (
    '<div class="bga-matrix-legend">'

    '<div class="bga-matrix-legend-item">'
    '<span class="bga-matrix-dot bga-matrix-home-win"></span>'
    'Home win'
    '</div>'

    '<div class="bga-matrix-legend-item">'
    '<span class="bga-matrix-dot bga-matrix-draw"></span>'
    'Draw'
    '</div>'

    '<div class="bga-matrix-legend-item">'
    '<span class="bga-matrix-dot bga-matrix-away-win"></span>'
    'Away win'
    '</div>'

    '<div class="bga-matrix-legend-item">'
    '<span class="bga-matrix-dot bga-matrix-upcoming"></span>'
    'Not played'
    '</div>'

    '</div>'

    '<div class="bga-matrix-context">'
    'Home ↓ &nbsp;&nbsp; Away →'
    '</div>'
)


st.markdown(
    legend_html,
    unsafe_allow_html=True,
)


# ------------------------------------------------------------
# Create empty score matrix
# ------------------------------------------------------------

matrix_columns = [
    team_tla.get(
        team,
        team,
    )
    for team in team_order
]


score_matrix = pd.DataFrame(
    "·",

    index=team_order,

    columns=matrix_columns,
)


score_matrix.index.name = (
    "Home ↓ / Away →"
)


# ------------------------------------------------------------
# Mark diagonal
# ------------------------------------------------------------

for team in team_order:

    tla = team_tla.get(
        team,
        team,
    )

    if tla in score_matrix.columns:

        score_matrix.loc[
            team,
            tla,
        ] = "—"


# ------------------------------------------------------------
# Populate fixtures
# ------------------------------------------------------------

for _, row in matches.iterrows():

    home_team = (
        row[
            "home_team"
        ]
    )

    away_team = (
        row[
            "away_team"
        ]
    )


    away_tla = (
        row[
            "away_tla"
        ]
    )


    if (
        home_team
        not in score_matrix.index
    ):

        continue


    if (
        away_tla
        not in score_matrix.columns
    ):

        continue


    if (
        row[
            "match_state"
        ]
        == "Finished"
        and pd.notna(
            row[
                "home_score"
            ]
        )
        and pd.notna(
            row[
                "away_score"
            ]
        )
    ):

        score_matrix.loc[
            home_team,
            away_tla,
        ] = (
            f"{int(row['home_score'])}"
            "–"
            f"{int(row['away_score'])}"
        )


    elif (
        row[
            "match_state"
        ]
        == "Live"
        and pd.notna(
            row[
                "home_score"
            ]
        )
        and pd.notna(
            row[
                "away_score"
            ]
        )
    ):

        score_matrix.loc[
            home_team,
            away_tla,
        ] = (
            f"{int(row['home_score'])}"
            "–"
            f"{int(row['away_score'])}"
            "*"
        )


    else:

        score_matrix.loc[
            home_team,
            away_tla,
        ] = "·"


# ============================================================
# Matrix styling
# ============================================================

def style_fixture_cell(
    value: object,
) -> str:
    """
    Style a matrix cell from the home team's perspective.
    """

    text = str(
        value
    )


    if text == "—":

        return (
            "background-color: #0B0F14; "
            "color: #46515E; "
            "text-align: center; "
            "font-weight: 600;"
        )


    if text == "·":

        return (
            "background-color: #111821; "
            "color: #46515E; "
            "text-align: center; "
            "font-weight: 600;"
        )


    clean_text = (
        text
        .replace(
            "*",
            "",
        )
    )


    try:

        home_score, away_score = (
            clean_text
            .split(
                "–"
            )
        )


        home_score = int(
            home_score
        )

        away_score = int(
            away_score
        )


    except (
        TypeError,
        ValueError,
    ):

        return (
            "text-align: center;"
        )


    if home_score > away_score:

        return (
            "background-color: #123026; "
            "color: #5DEBB1; "
            "text-align: center; "
            "font-weight: 800;"
        )


    if home_score < away_score:

        return (
            "background-color: #351B20; "
            "color: #FF9A9A; "
            "text-align: center; "
            "font-weight: 800;"
        )


    return (
        "background-color: #242D38; "
        "color: #D6DCE3; "
        "text-align: center; "
        "font-weight: 800;"
    )


styled_matrix = (
    score_matrix
    .style
    .map(
        style_fixture_cell
    )
)


st.dataframe(
    styled_matrix,

    use_container_width=True,

    height=760,
)


st.caption(
    (
        "Green = home win • Grey = draw • Red = away win • "
        "Dot = fixture not yet played • * = live score."
    )
)


# ============================================================
# Club season strip
# ============================================================

st.markdown(
    "### Club Season Strip"
)


selected_team = st.selectbox(
    "Select Club",

    options=team_order,

    index=(
        team_order.index(
            "Real Madrid"
        )
        if "Real Madrid"
        in team_order
        else 0
    ),
)


team_matches = (
    matches[
        (
            matches[
                "home_team"
            ]
            == selected_team
        )
        |
        (
            matches[
                "away_team"
            ]
            == selected_team
        )
    ]
    .copy()
    .sort_values(
        [
            "matchday",
            "utc_date",
        ]
    )
)


def team_result(
    row: pd.Series,
) -> str:
    """
    Return W/D/L from the selected club's perspective.
    """

    if (
        row[
            "match_state"
        ]
        != "Finished"
    ):

        return "Upcoming"


    home_score = int(
        row[
            "home_score"
        ]
    )

    away_score = int(
        row[
            "away_score"
        ]
    )


    if (
        row[
            "home_team"
        ]
        == selected_team
    ):

        goals_for = (
            home_score
        )

        goals_against = (
            away_score
        )


    else:

        goals_for = (
            away_score
        )

        goals_against = (
            home_score
        )


    if goals_for > goals_against:

        return "W"


    if goals_for < goals_against:

        return "L"


    return "D"


team_matches[
    "Result"
] = (
    team_matches
    .apply(
        team_result,
        axis=1,
    )
)


team_matches[
    "Opponent"
] = (
    team_matches
    .apply(
        lambda row:
            row[
                "away_team"
            ]
            if row[
                "home_team"
            ]
            == selected_team
            else row[
                "home_team"
            ],
        axis=1,
    )
)


team_matches[
    "Venue"
] = (
    team_matches[
        "home_team"
    ]
    .eq(
        selected_team
    )
    .map(
        {
            True:
                "Home",

            False:
                "Away",
        }
    )
)


team_matches[
    "Score"
] = (
    team_matches
    .apply(
        lambda row:
            (
                row[
                    "scoreline"
                ]
                if row[
                    "match_state"
                ]
                == "Finished"
                else "—"
            ),
        axis=1,
    )
)


season_strip = (
    team_matches[
        [
            "matchday",
            "Opponent",
            "Venue",
            "Result",
            "Score",
        ]
    ]
    .copy()
)


season_strip.columns = [
    "MD",
    "Opponent",
    "Venue",
    "Result",
    "Score",
]


st.dataframe(
    season_strip,

    use_container_width=True,

    hide_index=True,

    height=520,

    column_config={

        "MD":
            st.column_config.NumberColumn(
                "MD",
                width="small",
            ),

        "Opponent":
            st.column_config.TextColumn(
                "Opponent",
                width="medium",
            ),

        "Venue":
            st.column_config.TextColumn(
                "Venue",
                width="small",
            ),

        "Result":
            st.column_config.TextColumn(
                "Result",
                width="small",
            ),

        "Score":
            st.column_config.TextColumn(
                "Score",
                width="small",
            ),
    },
)


# ============================================================
# Footer
# ============================================================

render_footer()