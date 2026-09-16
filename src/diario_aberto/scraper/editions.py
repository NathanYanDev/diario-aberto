import datetime as dt
import logging
import re
from dataclasses import dataclass

import httpx
from bs4 import BeautifulSoup

from diario_aberto.config import settings

logger = logging.getLogger(__name__)

MONTHS_PT = {
    "janeiro": 1,
    "fevereiro": 2,
    "março": 3,
    "abril": 4,
    "maio": 5,
    "junho": 6,
    "julho": 7,
    "agosto": 8,
    "setembro": 9,
    "outubro": 10,
    "novembro": 11,
    "dezembro": 12,
}

_DATE_RE = re.compile(
    r"(?P<day>\d{1,2})\s+de\s+(?P<month>\w+)\s+de\s+(?P<year>\d{4})",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ListedEdition:
    number: int
    publication_date: dt.date
    page_url: str


class EditionScraper:
    def collect_editions(self) -> list[ListedEdition]:
        response = httpx.get(
            settings.scraper_base_url,
            headers={"User-Agent": settings.scraper_user_agent},
            timeout=30.0,
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        raw_items = soup.find_all("li", class_="edicao-atual")

        editions: list[ListedEdition] = []

        for item in raw_items:
            number = self._parse_number(item)
            publication_date = self._parse_date(item)
            page_url = self._parse_page_url(item)

            if number is None or publication_date is None or page_url is None:
                logger.warning(
                    "Falha ao parsear item: number=%r date=%r url=%r html=%r",
                    number,
                    publication_date,
                    page_url,
                    item.get_text(strip=True)[:80],
                )
                continue

            editions.append(ListedEdition(number, publication_date, page_url))

        return editions

    @staticmethod
    def _parse_number(item) -> int | None:
        if item.strong is None:
            return None
        match = re.search(r"\d+", item.strong.get_text(strip=True))
        return int(match.group()) if match else None

    @staticmethod
    def _parse_date(item) -> dt.date | None:
        date_tag = item.select_one(".data-lista > div:nth-of-type(2)")
        if date_tag is None:
            return None
        date_ext = date_tag.get_text(strip=True)

        match = _DATE_RE.search(date_ext)
        if not match:
            return None

        month = MONTHS_PT.get(match["month"].lower())
        if month is None:
            return None

        return dt.date(int(match["year"]), month, int(match["day"]))

    @staticmethod
    def _parse_page_url(item) -> str | None:
        if item.a is None:
            return None

        return item.a.get("href")
