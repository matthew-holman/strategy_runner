import json

from io import StringIO
from typing import List

import certifi
import pandas as pd
import requests

from bs4 import BeautifulSoup

WIKI_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
WAYBACK_API = (
    "https://web.archive.org/cdx/search/cdx"
    "?url=en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    "&output=json&fl=timestamp,original&collapse=digest"
)


def get_latest_snapshot_html() -> str:
    """Fetch the live Wikipedia page HTML for the S&P 500 index."""
    return _fetch_html(WIKI_URL)


def get_snapshot_html_from_wayback(timestamp: str, original_path: str) -> str:
    """Fetch archived HTML for a specific timestamp from Wayback Machine."""
    url = f"https://web.archive.org/web/{timestamp}/{original_path}"
    return _fetch_html(url)


def get_snapshot_timestamps() -> List[tuple[str, str]]:
    """Return list of (timestamp, original path) tuples from Wayback Machine."""
    response = requests.get(WAYBACK_API, verify=certifi.where())
    response.raise_for_status()
    snapshots = json.loads(response.text)
    return snapshots[1:]  # skip header


def extract_constituents(html: str) -> list[dict]:
    """Parse and normalize S&P 500 constituent data from HTML."""
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", {"id": "constituents"})

    if table is None:
        raise ValueError("No table with id='constituents' found")

    df = pd.read_html(
        StringIO(str(table)), converters={"CIK": lambda x: str(x).zfill(10)}
    )[0]
    df = _rename_columns(df)

    # Normalize ticker symbols to Yahoo format
    df["symbol"] = df["symbol"].apply(_normalize_ticker_symbol)

    return df[
        ["symbol", "company_name", "gics_sector", "gics_sub_industry", "cik"]
    ].to_dict(orient="records")


def _rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize variations in Wikipedia table headers."""
    column_mapping = {
        "Symbol": "symbol",
        "Security": "company_name",
        "GICS Sector": "gics_sector",
        "GICS Sub-Industry": "gics_sub_industry",
        "GICS Sub Industry": "gics_sub_industry",
        "CIK": "cik",
    }
    rename_mapping = {
        col: target for col, target in column_mapping.items() if col in df.columns
    }
    return df.rename(columns=rename_mapping)


def _normalize_ticker_symbol(symbol: str) -> str:
    """Convert symbol from Wikipedia format with dots (e.g., BRK.B) to Yahoo
    Finance format with dashes (e.g., BRK-B)."""
    return symbol.replace(".", "-")


def _fetch_html(url: str) -> str:
    response = requests.get(url, verify=certifi.where())
    response.raise_for_status()
    return response.text
