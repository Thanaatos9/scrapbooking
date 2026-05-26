import csv
import logging
import os


logger = logging.getLogger(__name__)

FIELDNAMES = ["title", "author", "category", "rating", "price", "extraction_date"]


def write_to_csv(books, output_file):
    """
    Ecrit les livres dans le CSV en mode append.
    Le header n'est ecrit que si le fichier n'existe pas encore.
    """
    file_exists = os.path.isfile(output_file)

    with open(output_file, "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES)

        if not file_exists:
            writer.writeheader()
            logger.info("Header ecrit (nouveau fichier)")
        else:
            logger.info("Fichier existant detecte : ajout sans reecrire le header")

        for book in books:
            writer.writerow(book)
