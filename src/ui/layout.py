import streamlit as st


def apply_branding() -> None:
    """Apply shared Beautiful Game Analytics styling."""

    st.markdown(
        """
        <style>

        .block-container {
            max-width: 1450px;
            padding-top: 3rem;
            padding-bottom: 4rem;
        }

        [data-testid="stSidebar"] {
            border-right: 1px solid #202833;
        }

        [data-testid="stMetric"] {
            background: #111821;
            border: 1px solid #202833;
            border-radius: 14px;
            padding: 18px;
        }

        [data-testid="stMetricLabel"] {
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }

        .bga-title {
            font-size: 2.6rem;
            font-weight: 800;
            line-height: 1.05;
            margin-bottom: 0.35rem;
        }

        .bga-subtitle {
            color: #9DA8B6;
            font-size: 1rem;
            margin-bottom: 1.5rem;
        }

        .bga-card {
            background: #111821;
            border: 1px solid #202833;
            border-radius: 14px;
            padding: 18px 20px;
            margin-bottom: 12px;
        }

        .bga-card-label {
            color: #8995A4;
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }

        .bga-card-value {
            font-size: 1.45rem;
            font-weight: 700;
            margin-top: 4px;
        }

        .bga-section-title {
            font-size: 1.4rem;
            font-weight: 700;
            margin-top: 1.4rem;
            margin-bottom: 0.8rem;
        }

        /* Tighten native kicker heading spacing */
        [data-testid="stMarkdownContainer"] h4 {
            margin-top: 0;
            margin-bottom: 0.45rem;
            padding-top: 0.25rem;
            line-height: 1.6;
            font-size: 0.9rem;
            letter-spacing: 0.08em;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> None:
    """Render common product context."""

    st.sidebar.markdown("## ⚽ Beautiful Game Analytics")
    st.sidebar.caption("Football intelligence from public data")

    st.sidebar.divider()

    st.sidebar.markdown("**Competition**")
    st.sidebar.write("La Liga")

    st.sidebar.markdown("**Season**")
    st.sidebar.write("2026/27")

    st.sidebar.divider()

    st.sidebar.caption(
        "Python • DuckDB • dbt • Streamlit"
    )


def page_header(
    title: str,
    subtitle: str,
    kicker: str = "LA LIGA • 2026/27",
) -> None:
    """Render the standard Beautiful Game Analytics page header."""

    # Give the kicker a proper Streamlit heading line box
    st.markdown(
        f"#### :green[{kicker}]"
    )

    st.markdown(
        f"""
        <div class="bga-title">
            {title}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="bga-subtitle">
            {subtitle}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    """Render source attribution."""

    st.divider()

    st.caption(
        "Football data provided by the Football-Data.org API. "
        "Beautiful Game Analytics is an independent portfolio project."
    )