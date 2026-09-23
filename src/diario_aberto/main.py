import logging

from diario_aberto.scraper.editions import EditionScraper

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

scraper = EditionScraper()

editions = scraper.collect_editions()
