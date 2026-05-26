import io
import logging
import os
import sys
import time
from datetime import datetime

import schedule

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(__file__))

from scraper import get_all_book_urls, scrape_book_detail
from transform import write_to_csv


# CONFIGURATION
BASE_URL = "https://books.toscrape.com/"
OUTPUT_FILE = "../data/books.csv"
DELAY = 0.5
MAX_RETRIES = 3
MAX_WORKERS = 10
RETRY_DELAY = 5

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")
LOG_FILE = os.path.join(LOG_DIR, "scraper.log")
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def setup_logging():
    """Configure les logs dans la console et dans un fichier."""
    os.makedirs(LOG_DIR, exist_ok=True)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))

    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))

    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[console_handler, file_handler],
    )


logger = logging.getLogger(__name__)


def run_scraper():
    """Fonction principale executee a chaque lancement automatique."""
    logger.info("=" * 50)
    logger.info("Lancement : %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    logger.info("=" * 50)

    logger.info("[1/2] Collecte des URLs de livres...")
    try:
        book_urls = get_all_book_urls(BASE_URL, MAX_RETRIES, RETRY_DELAY, DELAY)
    except Exception:
        logger.exception("Echec de la collecte des URLs. Le job est interrompu.")
        return

    logger.info("%s livres trouves.", len(book_urls))

    logger.info("[2/2] Extraction des donnees...")
    books = []
    for i, url in enumerate(book_urls, start=1):
        try:
            book_data = scrape_book_detail(url, MAX_RETRIES, RETRY_DELAY)
            books.append(book_data)
            logger.info("[%s/%s] OK - %s", i, len(book_urls), book_data["title"][:50])
        except Exception as e:
            logger.exception("[%s/%s] Ignore apres echec : %s", i, len(book_urls), e)
        time.sleep(DELAY)

    try:
        write_to_csv(books, OUTPUT_FILE)
    except Exception:
        logger.exception("Echec de l'ecriture dans le CSV : %s", OUTPUT_FILE)
        return

    logger.info("%s livres ajoutes dans '%s'", len(books), OUTPUT_FILE)


if __name__ == "__main__":
    setup_logging()
    logger.info("=== Scraper demarre ===")
    logger.info("Planning : tous les jours a 08:00")
    logger.info("Fichier de logs : %s", LOG_FILE)

    run_scraper()

    schedule.every().day.at("08:00").do(run_scraper)

    while True:
        schedule.run_pending()
        time.sleep(60)
