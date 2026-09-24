import datetime as dt
import logging
import re
import time
from dataclasses import dataclass

import httpx
from bs4 import BeautifulSoup, Tag
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_incrementing,
)

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

MAX_PAGES = 300  # Margem de segurança contra loop infinito - São conhecidas 247 páginas do portal

_DATE_RE = re.compile(
    r"(?P<day>\d{1,2})\s+de\s+(?P<month>\w+)\s+de\s+(?P<year>\d{4})",
    re.IGNORECASE,
)
_NEXT_PAGE_RE = re.compile("próxima", re.IGNORECASE)
_PAGES_RE = re.compile(r"página\s+(\d+)\s+de\s+(\d+)", re.IGNORECASE)


@dataclass(frozen=True)
class ListedEdition:
    number: int
    publication_date: dt.date
    page_url: str


class EditionScraper:
    def collect_editions(self) -> list[ListedEdition]:
        editions: list[ListedEdition] = []
        url: str | None = settings.scraper_base_url
        pages_visited = 0

        while url and pages_visited < MAX_PAGES:
            soup = self._fetch_soup(url)
            current_page, last_page = self._get_current_and_last_page(soup) or (0, 0)

            remaining_pages = last_page - current_page

            if current_page != 0:
                logger.info("Iniciando coleta na página %d", current_page)
            else:
                logger.info("Iniciando coleta")

            editions.extend(self._parse_page(soup))

            if current_page != 0:
                logger.info(
                    "Edições coletadas da página %d com sucesso, faltam %d páginas",
                    current_page,
                    remaining_pages,
                )
            else:
                logger.info("Edições coletadas com sucesso")

            pages_visited += 1

            url = self._find_next_page_url(soup)
            if url:
                time.sleep(settings.scraper_delay_seconds)

        if pages_visited >= MAX_PAGES:
            logger.warning(
                f"Atingiu o limite de {MAX_PAGES} páginas - verifique se a paginação não entrou em loop"
            )

        logger.info(
            f"Coleta finalizada: {pages_visited} páginas, {len(editions)} edições."
        )
        return editions

    @staticmethod
    @retry(
        retry=retry_if_exception_type(
            (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPStatusError)
        ),
        stop=stop_after_attempt(settings.scraper_fetch_attempts),
        wait=wait_incrementing(start=settings.scraper_wait_seconds, increment=5.0),
        reraise=True,
    )
    def _fetch_soup(url: str) -> BeautifulSoup:
        response = httpx.get(
            url,
            headers={"User-Agent": settings.scraper_user_agent},
            timeout=30.0,
        )
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")

    def _parse_page(self, soup: BeautifulSoup) -> list[ListedEdition]:
        editions: list[ListedEdition] = []
        for item in soup.find_all("li", class_="edicao-atual"):
            number = self._parse_number(item)
            publication_date = self._parse_date(item)
            page_url = self._parse_page_url(item)

            if number is None or publication_date is None or page_url is None:
                logger.warning(
                    f"Falha ao parsear item: number = {number} date = {publication_date} url = {page_url} html = {item.get_text(strip=True)[:80]}",
                )
                continue

            editions.append(ListedEdition(number, publication_date, page_url))
        return editions

    @staticmethod
    def _get_current_and_last_page(soup: BeautifulSoup) -> tuple[int, int] | None:
        pages = soup.find(
            "span",
            class_=re.compile("page", re.IGNORECASE),
            string=re.compile("página", re.IGNORECASE),
        )

        if pages is None:
            logger.warning("Elemento de páginação não encontrado")
            return None

        match = _PAGES_RE.search(pages.get_text(strip=True))

        if not match:
            logger.warning("Falha ao buscar as páginas")
            return None

        current_page, last_page = map(int, match.groups())

        return current_page, last_page

    @staticmethod
    def _find_next_page_url(soup: BeautifulSoup) -> str | None:
        next_link = soup.find("a", string=_NEXT_PAGE_RE)
        if next_link is None:
            return None
        return str(next_link.get("href")) if next_link.get("href") is not None else None

    @staticmethod
    def _parse_number(item: Tag) -> int | None:
        if item.strong is None:
            return None
        match = re.search(r"\d+", item.strong.get_text(strip=True))
        return int(match.group()) if match else None

    @staticmethod
    def _parse_date(item: Tag) -> dt.date | None:
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
    def _parse_page_url(item: Tag) -> str | None:
        if item.a is None:
            return None

        return str(item.a.get("href")) if item.a.get("href") is not None else None
