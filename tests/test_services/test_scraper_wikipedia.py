from pathlib import Path

import pytest

from services.wiki_scraper import fetch_wikipedia_html, parse_sp500_constituents_html
from tasks.sp500_ingestion import WIKI_PAGE


def test_parse_constituents_html_snapshot():
    fixture_path = (
        Path(__file__).parent.parent / "fixtures" / "sp500_snapshot_250718.html"
    )
    html = fixture_path.read_text(encoding="utf-8")
    records = parse_sp500_constituents_html(html)

    assert isinstance(records, list)
    assert len(records) >= 500
    assert {"symbol", "company_name", "cik"}.issubset(records[0])


@pytest.mark.skip(reason="For debugging not for test suite runs")
def test_fetch_wikipedia_html_live():

    html = fetch_wikipedia_html(WIKI_PAGE)
    records = parse_sp500_constituents_html(html)

    assert isinstance(records, list)
    assert len(records) >= 500
    assert {"symbol", "company_name", "cik"}.issubset(records[0])
