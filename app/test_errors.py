import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from main import setup_logging, logger
from scraper import get_soup, scrape_book_detail
from transform import write_to_csv


setup_logging()

logger.info("=== Debut des tests d'erreurs ===")

# 1. Erreur HTTP 404
try:
    get_soup("https://books.toscrape.com/page-inexistante.html", max_retries=2, retry_delay=1)
except Exception:
    logger.exception("Test OK : erreur HTTP capturee")

# 2. Erreur de connexion
try:
    get_soup("http://localhost:9999", max_retries=2, retry_delay=1)
except Exception:
    logger.exception("Test OK : erreur de connexion capturee")

# 3. Erreur de parsing HTML
try:
    scrape_book_detail("https://books.toscrape.com/catalogue/page-1.html", max_retries=2, retry_delay=1)
except Exception:
    logger.exception("Test OK : erreur de parsing capturee")

# 4. Erreur d'ecriture CSV
try:
    write_to_csv([], "../dossier_inexistant/books.csv")
except Exception:
    logger.exception("Test OK : erreur CSV capturee")

logger.info("=== Fin des tests d'erreurs ===")