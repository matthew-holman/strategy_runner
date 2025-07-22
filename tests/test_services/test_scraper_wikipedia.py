from pathlib import Path

import pytest

from services.stock_index_service import WIKI_URL, _fetch_html, extract_constituents


def test_parse_constituents_html_snapshot():
    fixture_path = (
        Path(__file__).parent.parent / "fixtures" / "sp500_snapshot_250718.html"
    )
    html = fixture_path.read_text(encoding="utf-8")
    records = extract_constituents(html)

    assert isinstance(records, list)
    assert len(records) >= 500
    assert {"symbol", "company_name", "cik"}.issubset(records[0])


@pytest.mark.skip(reason="For debugging not for test suite runs")
def test_fetch_wikipedia_html_live():

    html = _fetch_html(WIKI_URL)
    records = extract_constituents(html)

    assert isinstance(records, list)
    assert len(records) >= 500
    assert {"symbol", "company_name", "cik"}.issubset(records[0])
