# ⚽ Beautiful Game Analytics

**Beautiful Game Analytics (BGA)** is a public football data product that combines data engineering, analytics engineering, cloud infrastructure, and football-native visualization.

The project currently focuses on **La Liga 2026/27**, transforming public football data into a tested analytical warehouse and an interactive Streamlit application.

> The goal is not simply to build another scores dashboard.  
> Beautiful Game Analytics treats football data like a real data product: ingest it reliably, preserve source truth, model it, test it, reconcile inconsistencies, and present it through an interface that feels native to the sport.

---

## 🌐 Live Project

**Interactive Application**  
https://beautifulgameanalytics-njgntd499kezmsdpcvoau.streamlit.app

**dbt Documentation**  
https://johnalex75326.github.io/beautiful_game_analytics/

---

## What the Project Shows

Beautiful Game Analytics is designed as an end-to-end portfolio project demonstrating:

- Python data ingestion and transformation
- REST API integration
- Raw source snapshot preservation
- Parquet-based processing
- DuckDB analytical warehousing
- dbt staging, intermediate, and mart layers
- Data quality testing and reconciliation
- GitHub Actions orchestration
- AWS S3 warehouse publication
- Streamlit application development
- Football-specific analytical visualization
- Multi-layer observability and data freshness monitoring

---

# 🏗 Architecture

```text
                    football-data.org
                           │
                           ▼
                    Python Ingestion
                           │
                           ▼
                   Raw JSON Snapshots
                           │
                           ▼
                Pandas Transformations
                           │
                           ▼
                  Processed Parquet
                           │
                           ▼
                 DuckDB Warehouse
                           │
                           ▼
                          dbt
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
          Staging      Intermediate      Marts
                                           │
                                           ▼
                                      Amazon S3
                                           │
                                           ▼
                                Local DuckDB Cache
                                           │
                                           ▼
                                       Streamlit
```

Production refreshes are orchestrated with **GitHub Actions**.

The analytical DuckDB warehouse is published to a private Amazon S3 bucket after a successful pipeline run. The Streamlit application synchronizes against the latest published warehouse before serving analytical queries.

---

# 📊 Product Features

## Overview

The landing page provides a compact view of the current competition state, including:

- league leaders
- team performance
- current standings
- recent results
- upcoming fixtures
- matchday context
- data freshness indicators

---

## ⚽ Matches

A football-native match explorer containing:

- matchday navigation ribbon
- finished, live, and upcoming fixture states
- club crests
- score cards
- team filters
- match-state filters
- Europe/Madrid fixture times

The matchday ribbon makes it possible to move through the season without treating fixtures like a generic BI table.

---

## 📈 Standings

The standings view combines official source data with derived analytical context.

Features include:

- official current league table
- Champions League zone
- European race zone
- relegation zone
- leader / best attack / best defence cards
- source reconciliation
- latest fully completed round
- league position movement
- points race

### Match-Derived Position Movement

Historical league position is reconstructed from **finished match results**.

Positions are calculated using:

```text
Points
  ↓
Goal Difference
  ↓
Goals Scored
```

The visualization supports:

- Title Race
- European Race
- Relegation Battle
- Custom Clubs

The official standings remain the authoritative current table. The historical race visualization is explicitly treated as an analytical reconstruction because official competition tie-breaking rules may differ when clubs remain level.

---

## 🛡 Team Explorer

The Team Explorer provides a club-focused analytical view.

Features include:

- club identity and crest
- current league position
- points and performance metrics
- home vs away performance
- recent form strip
- recent completed fixtures
- upcoming fixtures

Real Madrid is currently used as the default spotlight club.

---

# 🗓 Season View

The Season View provides a competition-wide perspective.

## Fixture Matrix

A 20 × 20 fixture matrix shows every home/away combination across the La Liga season.

```text
Rows    → Home clubs
Columns → Away clubs
```

Cells indicate:

- 🟢 Home win
- ⚪ Draw
- 🔴 Away win
- · Fixture not yet played
- — Same club

Finished fixtures display their score directly inside the matrix.

## Club Season Strip

Users can select a club and inspect its entire season schedule with:

- matchday
- opponent
- venue
- result
- score

---

# 🩺 Data Health

Beautiful Game Analytics exposes its own engineering state instead of hiding the pipeline behind the dashboard.

The Data Health page includes:

- warehouse freshness
- S3 publication status
- local cache status
- source snapshot freshness
- match feed state
- standings reconciliation
- model row counts
- pipeline execution history
- pipeline duration
- failure-stage reporting

This allows the analytical product to communicate whether its underlying data is currently healthy.

---

# 🧠 Source Reconciliation

Football APIs do not always update every resource at exactly the same moment.

For example:

```text
Season metadata
        │
        └── Current Matchday = 6

Match feed
        │
        └── Latest fully completed round = 3
```

Beautiful Game Analytics preserves both states instead of silently rewriting one to match the other.

The warehouse therefore separates:

```text
Official Source State
        ↕
Match-Derived Analytics
        ↕
Reconciliation Layer
```

This makes source discrepancies observable and traceable.

---

# 🗃 Data Model

The physical warehouse contains the core football entities:

```text
dim_team
fact_match
fact_standing_snapshot
pipeline_run_log
```

dbt then builds the analytical layer.

## Staging

```text
stg_teams
stg_matches
stg_standings
```

## Intermediate

```text
int_team_match_results
int_standings_reconciliation
```

## Marts

```text
mart_current_standings
mart_team_performance
mart_match_explorer
```

The project currently runs:

```text
8 dbt models
62 tests
70 dbt build items
```

with the production target expected to complete without warnings or errors.

---

# 🔄 Pipeline

The core production pipeline follows four stages:

```text
1. API_INGESTION
        ↓
2. TRANSFORMATION
        ↓
3. WAREHOUSE_LOAD
        ↓
4. DBT_BUILD
```

A successful build produces:

```text
data/beautiful_game_analytics.duckdb
```

The warehouse is then published to Amazon S3 for consumption by the application.

---

# ☁️ Cloud Architecture

Beautiful Game Analytics currently uses:

- **GitHub** — source control
- **GitHub Actions** — scheduled pipeline orchestration
- **AWS IAM / OIDC** — GitHub-to-AWS authentication
- **Amazon S3** — persistent warehouse publication
- **Streamlit Community Cloud** — public application
- **GitHub Pages** — dbt documentation

The pipeline currently refreshes automatically throughout the day.

---

# 🎨 Club Artwork

Football data and club artwork are intentionally treated as separate concerns.

**Football-Data.org** remains authoritative for competition, team, fixture, result, and standings identifiers.

**TheSportsDB** is used as a slow-changing reference source for approved club artwork.

Club artwork mappings are manually validated before publication rather than resolved dynamically during every pipeline run.

This prevents incorrect semantic matches from appearing in the application.

---

# 📁 Repository Structure

```text
beautiful_game_analytics/
│
├── .github/
│   └── workflows/
│       └── refresh-data.yml
│
├── .streamlit/
│   └── config.toml
│
├── data/
│   └── reference/
│       └── sportsdb/
│
├── dbt/
│   ├── models/
│   │   ├── staging/
│   │   ├── intermediate/
│   │   └── marts/
│   ├── dbt_project.yml
│   └── profiles.yml
│
├── pages/
│   ├── 1_Matches.py
│   ├── 2_Standings.py
│   ├── 3_Team_Explorer.py
│   ├── 4_Data_Health.py
│   └── 5_Season_View.py
│
├── src/
│   ├── ingest/
│   ├── transform/
│   ├── ui/
│   ├── warehouse/
│   ├── config.py
│   └── pipeline.py
│
├── app.py
├── requirements.txt
└── README.md
```

Generated raw data, processed data, credentials, and runtime DuckDB files are intentionally excluded from source control.

---

# 🛠 Technology Stack

| Layer | Technology |
|---|---|
| Language | Python |
| API ingestion | Requests |
| Transformation | Pandas |
| Intermediate storage | Parquet |
| Analytical database | DuckDB |
| Analytics engineering | dbt |
| Dashboard | Streamlit |
| Visualization | Plotly |
| Cloud storage | Amazon S3 |
| CI/CD & orchestration | GitHub Actions |
| Cloud authentication | AWS IAM + GitHub OIDC |
| Documentation | dbt Docs + GitHub Pages |

---

# 🚀 Local Development

## 1. Clone the repository

```bash
git clone https://github.com/JohnAlex75326/beautiful_game_analytics.git
cd beautiful_game_analytics
```

## 2. Create a virtual environment

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

## 3. Install dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 4. Configure the football API

Create a local `.env` file:

```text
FOOTBALL_DATA_API_TOKEN=<your-token>
FOOTBALL_COMPETITIONS=PD
FOOTBALL_DATA_BASE_URL=https://api.football-data.org/v4
```

A free API key can be obtained from:

https://www.football-data.org/

## 5. Run the pipeline

```bash
python -m src.pipeline
```

This performs:

```text
API ingestion
    ↓
raw snapshot creation
    ↓
transformation
    ↓
DuckDB load
    ↓
dbt build
```

## 6. Launch Streamlit

```bash
streamlit run app.py
```

---

# 🧪 dbt

Run the analytical build directly with:

```bash
dbt build \
  --project-dir dbt \
  --profiles-dir dbt
```

Generate documentation with:

```bash
dbt docs generate \
  --project-dir dbt \
  --profiles-dir dbt
```

The production documentation is also published through GitHub Pages:

https://johnalex75326.github.io/beautiful_game_analytics/

---

# 📡 Data Sources

### Football-Data.org

Used for:

- competitions
- teams
- fixtures
- scores
- match status
- league standings

https://www.football-data.org/

### TheSportsDB

Used for manually validated club artwork metadata.

https://www.thesportsdb.com/

---

# ⚠️ Current Scope

Beautiful Game Analytics currently focuses on:

```text
Competition: La Liga
Code: PD
Season: 2026/27
```

The current football-data.org integration does not yet model rich player-level or event-level analytics.

The product therefore does **not** currently claim to provide:

- xG
- shot maps
- passing networks
- player heatmaps
- progressive passing
- detailed player match statistics

These features require an appropriate player/event data source and additional modeling.

---

# 🗺 Roadmap

Potential future development includes:

### Multi-Competition Support

```text
La Liga
Premier League
Champions League
```

The Champions League requires stage-aware modeling because league-phase and knockout competition semantics differ from domestic leagues.

### Player Analytics

Potential future entities include:

```text
dim_player
bridge_player_team
fact_player_match
fact_goal
fact_card
fact_substitution
```

### Rich Football Analytics

Future data permitting:

- player form
- player comparisons
- shot maps
- passing networks
- fixture difficulty
- matchday movers
- competition journey views
- Champions League knockout bracket

### Multi-Source Football Platform

A longer-term direction is a canonical football data model capable of resolving teams, players, and matches across multiple providers.

---

# 💡 Project Philosophy

Beautiful Game Analytics is built around a simple principle:

> **The interface should feel like a football product, while the system underneath should behave like a production data platform.**

That means:

```text
Preserve source truth
        ↓
Make transformations traceable
        ↓
Test analytical models
        ↓
Expose reconciliation
        ↓
Monitor freshness
        ↓
Build football-native experiences
```

---

# 🙏 Inspiration

The original spark for this project came from **Peter's Football Statistics Tracker**, an end-to-end football data engineering project that demonstrated how football could serve as the foundation for a serious engineering portfolio project.

https://github.com/peter115342/soccer-tracker-DE-project

Beautiful Game Analytics grew from that inspiration into a separate implementation with its own architecture, data model, analytical layer, cloud infrastructure, and product direction.

---

# 📜 Attribution

Football data provided by the **Football-Data.org API**.

Club artwork metadata provided by **TheSportsDB**.

Club names, crests, and trademarks are the property of their respective rights holders and are displayed for identification purposes only.

Beautiful Game Analytics is an independent portfolio project and is not affiliated with or endorsed by La Liga or any football club.

---

## Built With

**Python • DuckDB • dbt • AWS • GitHub Actions • Streamlit • Plotly**

⚽ Data engineering for the beautiful game.
