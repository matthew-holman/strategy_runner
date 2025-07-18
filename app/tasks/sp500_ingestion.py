from app.services.wiki_scraper import get_sp500_constituents_from_wikipedia
from app.utils import Log

WIKI_PAGE = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"


def daily_sp500_sync():

    records = get_sp500_constituents_from_wikipedia(WIKI_PAGE)
    Log.info(f"{len(records)} found from list of companies page.")
