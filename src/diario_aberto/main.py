import logging

from diario_aberto.scraper.editions import EditionScraper

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)

scraper = EditionScraper()

editions = scraper.collect_editions()
editions_with_pdf = scraper.collect_pdf_urls(editions)
