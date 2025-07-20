import json

from typing import List

import certifi
import pandas as pd
import requests

from bs4 import BeautifulSoup

WIKI_PAGE = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"


def fetch_html(url: str) -> str:
    response = requests.get(url, verify=certifi.where())
    response.raise_for_status()
    return response.text


def parse_sp500_constituents_html(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", {"id": "constituents"})

    if table is None:
        raise ValueError("No table with id='constituents' found")

    df = pd.read_html(str(table))[0]
    df = rename_columns(df)

    records = df[
        ["symbol", "company_name", "gics_sector", "gics_sub_industry", "cik"]
    ].to_dict(orient="records")
    return records


def rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    # Handle common variations in column headers
    column_mapping = {
        "Symbol": "symbol",
        "Security": "company_name",
        "GICS Sector": "gics_sector",
        "GICS Sub-Industry": "gics_sub_industry",  # 2020 > newer format
        "GICS Sub Industry": "gics_sub_industry",  # 2020 < older format
        "CIK": "cik",
    }

    # Filter only columns that actually exist in the DataFrame
    rename_mapping = {
        col: target for col, target in column_mapping.items() if col in df.columns
    }

    return df.rename(columns=rename_mapping)


def get_wayback_snapshot_list() -> List[str]:
    wayback_page_json_url = "https://web.archive.org/cdx/search/cdx?url=en.wikipedia.org/wiki/List_of_S%26P_500_companies&output=json&fl=timestamp,original&collapse=digest"  # noqa: E501, B950
    response = requests.get(wayback_page_json_url, verify=certifi.where())
    response.raise_for_status()
    snapshot_json = json.loads(response.text)
    # first row is a title row ["timestamp"","original"]
    return snapshot_json[1:]
