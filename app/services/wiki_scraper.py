import pandas as pd


def get_sp500_constituents_from_wikipedia(url: str) -> list[dict]:
    tables = pd.read_html(url)
    df = tables[0]  # first table is the constituents

    # Rename for consistency with your model
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
