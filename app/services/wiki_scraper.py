import certifi
import pandas as pd
import requests


def fetch_wikipedia_html(url: str) -> str:
    response = requests.get(url, verify=certifi.where())
    response.raise_for_status()
    return response.text


def parse_sp500_constituents_html(html: str) -> list[dict]:
    tables = pd.read_html(html)
    df = tables[0]

    df = df.rename(
        columns={
            "Symbol": "symbol",
            "Security": "company_name",
            "GICS Sector": "gics_sector",
            "GICS Sub-Industry": "gics_sub_industry",
            "CIK": "cik",
        }
    )

    records = df[
        ["symbol", "company_name", "gics_sector", "gics_sub_industry", "cik"]
    ].to_dict(orient="records")
    return records
