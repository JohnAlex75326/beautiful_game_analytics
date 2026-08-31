import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


FOOTBALL_DATA_API_TOKEN = os.getenv("FOOTBALL_DATA_API_TOKEN")

FOOTBALL_DATA_BASE_URL = os.getenv(
    "FOOTBALL_DATA_BASE_URL",
    "https://api.football-data.org/v4",
)

FOOTBALL_COMPETITIONS = [
    competition.strip()
    for competition in os.getenv(
        "FOOTBALL_COMPETITIONS",
        "PD",
    ).split(",")
    if competition.strip()
]


DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

DUCKDB_PATH = DATA_DIR / "beautiful_game_analytics.duckdb"


def validate_config() -> None:
    """Validate required project configuration."""

    if not FOOTBALL_DATA_API_TOKEN:
        raise ValueError(
            "FOOTBALL_DATA_API_TOKEN is missing. "
            "Add it to the local .env file."
        )