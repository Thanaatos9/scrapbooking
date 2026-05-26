import logging
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)

RATING_MAP = {
    "One": 1,
    "Two": 2,
    "Three": 3,
    "Four": 4,
    "Five": 5,
}


def get_soup(url, max_retries, retry_delay):
    """Envoie une requete GET avec gestion d'erreur et retry automatique."""
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            response.encoding = "utf-8"
            return BeautifulSoup(response.text, "html.parser")

        except requests.exceptions.HTTPError as e:
            logger.warning("Erreur HTTP (tentative %s/%s) : %s", attempt, max_retries, e)
        except requests.exceptions.ConnectionError:
            logger.warning("Erreur de connexion (tentative %s/%s)", attempt, max_retries)
        except requests.exceptions.Timeout:
            logger.warning("Timeout (tentative %s/%s)", attempt, max_retries)
        except requests.exceptions.RequestException as e:
            logger.warning(
                "Erreur inattendue (tentative %s/%s) : %s",
                attempt,
                max_retries,
                e,
            )

        if attempt < max_retries:
            logger.info("Nouvel essai dans %ss...", retry_delay)
            time.sleep(retry_delay)

    raise Exception(f"Echec apres {max_retries} tentatives : {url}")


def get_all_book_urls(base_url, max_retries, retry_delay, delay):
    """Parcourt toutes les pages du catalogue et retourne la liste des URLs."""
    book_urls = []
    page_url = base_url

    while page_url:
        logger.info("Scan de la page : %s", page_url)
        soup = get_soup(page_url, max_retries, retry_delay)

        for article in soup.select("article.product_pod"):
            relative_url = article.select_one("h3 a")["href"]
            if relative_url.startswith("catalogue/"):
                full_url = base_url + relative_url
            else:
                full_url = base_url + "catalogue/" + relative_url.replace("../", "")
            book_urls.append(full_url)

        next_btn = soup.select_one("li.next a")
        if next_btn:
            next_relative = next_btn["href"]
            page_url = page_url.rsplit("/", 1)[0] + "/" + next_relative
        else:
            page_url = None

        time.sleep(delay)

    return book_urls


def scrape_book_detail(url, max_retries, retry_delay):
    """Scrape les informations d'un livre depuis sa page detail."""
    soup = get_soup(url, max_retries, retry_delay)

    title = soup.select_one("div.product_main h1").get_text(strip=True)
    author = "N/A"

    breadcrumb = soup.select("ul.breadcrumb li")
    category = breadcrumb[-2].get_text(strip=True) if len(breadcrumb) >= 2 else "N/A"

    rating_tag = soup.select_one("p.star-rating")
    rating_word = rating_tag["class"][1] if rating_tag else "N/A"
    rating = RATING_MAP.get(rating_word, rating_word)

    price = soup.select_one("p.price_color").get_text(strip=True)
    extraction_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return {
        "title": title,
        "author": author,
        "category": category,
        "rating": rating,
        "price": price,
        "extraction_date": extraction_date,
    }
