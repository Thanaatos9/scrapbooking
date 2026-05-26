# Pipeline de scraping de livres

## Presentation

Ce projet est un pipeline de scraping developpe en Python. Il recupere automatiquement des informations sur les livres du site [Books to Scrape](https://books.toscrape.com/), les transforme en donnees structurees, puis les sauvegarde dans un fichier CSV.

Le programme est aussi prevu pour etre lance de maniere automatisee tous les jours a 08:00 et pour conserver des logs d'execution.

## Objectifs du projet

- Recuperer les URLs de tous les livres disponibles sur le site.
- Extraire les informations importantes de chaque livre.
- Sauvegarder les donnees dans un fichier CSV.
- Gerer les erreurs reseau, HTTP, parsing et ecriture fichier.
- Journaliser l'execution dans un fichier de logs.
- Permettre une execution locale ou via Docker.

## Donnees collectees

Pour chaque livre, le programme extrait les champs suivants :

| Champ | Description |
| --- | --- |
| `title` | Titre du livre |
| `author` | Auteur, actuellement renseigne a `N/A` car le site ne fournit pas cette information |
| `category` | Categorie du livre |
| `rating` | Note du livre convertie en valeur numerique quand possible |
| `price` | Prix affiche sur le site |
| `extraction_date` | Date et heure de l'extraction |

Les donnees sont sauvegardees dans :

```text
data/books.csv
```

## Architecture du projet

```text
V2/
+-- app/
|   +-- main.py          # Point d'entree et orchestration du pipeline
|   +-- scraper.py       # Requetes HTTP, parsing HTML et extraction des donnees
|   +-- transform.py     # Ecriture des donnees dans le CSV
|   +-- test_errors.py   # Tests manuels de gestion d'erreurs
+-- data/
|   +-- books.csv        # Fichier de sortie des donnees
+-- logs/
|   +-- scraper.log      # Fichier de logs
+-- Dockerfile           # Image Docker de l'application
+-- docker-compose.yml   # Configuration Docker Compose
+-- requirements.txt     # Dependances Python
+-- README.md            # Documentation technique
```

## Fonctionnement general

Le point d'entree est le fichier `app/main.py`.

Au demarrage, le programme :

1. Configure les logs avec `setup_logging()`.
2. Lance une premiere execution immediate du scraping avec `run_scraper()`.
3. Programme une execution quotidienne a 08:00 avec la librairie `schedule`.
4. Garde le processus actif avec une boucle qui verifie les taches planifiees toutes les minutes.

La fonction `run_scraper()` orchestre le pipeline :

1. Recuperation de toutes les URLs de livres avec `get_all_book_urls()`.
2. Extraction des details de chaque livre avec `scrape_book_detail()`.
3. Sauvegarde des livres dans le CSV avec `write_to_csv()`.

## Detail des modules

### `app/main.py`

Ce fichier coordonne l'ensemble du programme.

Il contient :

- la configuration generale du projet ;
- la configuration des logs ;
- la fonction principale `run_scraper()` ;
- la planification automatique avec `schedule`.

Parametres principaux :

| Variable | Role |
| --- | --- |
| `BASE_URL` | URL du site a scraper |
| `OUTPUT_FILE` | Chemin du fichier CSV de sortie |
| `DELAY` | Delai entre les requetes |
| `MAX_RETRIES` | Nombre maximum de tentatives en cas d'erreur |
| `RETRY_DELAY` | Temps d'attente entre deux tentatives |
| `LOG_FILE` | Chemin du fichier de logs |

### `app/scraper.py`

Ce fichier contient la logique de scraping.

Fonctions principales :

- `get_soup(url, max_retries, retry_delay)` : envoie une requete HTTP et transforme la page HTML en objet BeautifulSoup.
- `get_all_book_urls(base_url, max_retries, retry_delay, delay)` : parcourt toutes les pages du catalogue et recupere les URLs des livres.
- `scrape_book_detail(url, max_retries, retry_delay)` : extrait les donnees d'une page detail de livre.

La librairie `requests` est utilisee pour les requetes HTTP. La librairie `BeautifulSoup` est utilisee pour analyser le HTML avec des selecteurs CSS.

### `app/transform.py`

Ce fichier s'occupe de l'ecriture dans le CSV.

La fonction `write_to_csv()` :

- ouvre le fichier en mode append ;
- cree l'en-tete si le fichier n'existe pas encore ;
- ajoute chaque livre sous forme de ligne CSV ;
- utilise l'encodage UTF-8.

### `app/test_errors.py`

Ce fichier sert a tester manuellement la robustesse du programme.

Il declenche volontairement :

- une erreur HTTP 404 ;
- une erreur de connexion ;
- une erreur de parsing HTML ;
- une erreur d'ecriture CSV.

L'objectif est de verifier que les erreurs sont bien capturees et journalisees.

## Gestion des erreurs

La gestion des erreurs est un point central du projet, car un scraper depend de plusieurs elements externes : reseau, site distant, structure HTML et systeme de fichiers.

### Erreurs reseau et HTTP

Dans `get_soup()`, plusieurs exceptions sont gerees :

| Exception | Signification |
| --- | --- |
| `HTTPError` | Le serveur repond avec un statut d'erreur comme 404 ou 500 |
| `ConnectionError` | Impossible de se connecter au site |
| `Timeout` | Le serveur met trop longtemps a repondre |
| `RequestException` | Erreur generale liee a la requete HTTP |

Le programme utilise aussi un timeout de 10 secondes pour eviter de rester bloque indefiniment.

### Systeme de retry

Si une requete echoue, le programme ne s'arrete pas immediatement. Il retente la requete plusieurs fois selon la valeur de `MAX_RETRIES`.

Entre deux tentatives, il attend `RETRY_DELAY` secondes.

Ce mecanisme est utile car certaines erreurs peuvent etre temporaires : reseau instable, serveur lent ou indisponibilite momentanee.

### Strategie d'arret

La strategie depend de l'etape :

- Si la recuperation des URLs echoue completement, le job est interrompu car il n'y a rien a scraper.
- Si l'extraction d'un livre echoue, l'erreur est loggee mais le programme continue avec les autres livres.
- Si l'ecriture CSV echoue, le job s'arrete car les donnees ne peuvent pas etre sauvegardees correctement.

Cette strategie evite qu'une seule page defectueuse bloque tout le pipeline.

## Logs

Les logs sont configures dans `setup_logging()`.

Deux sorties sont utilisees :

- la console, avec le niveau `INFO` ;
- le fichier `logs/scraper.log`, avec le niveau `DEBUG`.

Le format des logs contient :

- la date et l'heure ;
- le niveau du message ;
- le nom du module ;
- le message.

Exemple :

```text
2026-05-26 08:00:00 | INFO | __main__ | Lancement : 2026-05-26 08:00:00
```

L'utilisation de `logger.exception()` permet d'enregistrer le message d'erreur ainsi que la trace complete de l'exception. C'est utile pour diagnostiquer precisement l'origine d'un probleme.

## Installation locale

### Prerequis

- Python 3.10 ou plus recent
- `pip`

### Creation d'un environnement virtuel

```bash
python -m venv .venv
```

Activation sous Windows PowerShell :

```bash
.\.venv\Scripts\Activate.ps1
```

Activation sous macOS/Linux :

```bash
source .venv/bin/activate
```

### Installation des dependances

```bash
pip install -r requirements.txt
```

### Lancement du programme

Depuis la racine du projet :

```bash
python app/main.py
```

Le programme lance une premiere extraction, puis reste actif pour executer le scraping tous les jours a 08:00.

## Execution avec Docker

### Construction et lancement

```bash
docker compose up --build
```

### Arret du conteneur

```bash
docker compose down
```

### Volumes Docker

Le fichier `docker-compose.yml` monte les dossiers suivants :

| Dossier local | Dossier dans le conteneur | Role |
| --- | --- | --- |
| `./data` | `/app/data` | Persistance du CSV |
| `./logs` | `/app/logs` | Persistance des logs |
| `.` | `/app` | Acces au code source |

Les fichiers generes restent donc disponibles sur la machine meme apres l'arret du conteneur.

Note : le service Docker expose actuellement le port `8000`, mais le programme n'est pas une API web. Il s'agit d'un scraper planifie. Ce port pourra etre utile plus tard si une API FastAPI ou Flask est ajoutee.

## Dependances principales

| Dependence | Utilisation |
| --- | --- |
| `requests` | Envoyer les requetes HTTP |
| `beautifulsoup4` | Parser le HTML |
| `schedule` | Planifier l'execution quotidienne |

## Commandes utiles

Lancer le programme en local :

```bash
python app/main.py
```

Lancer les tests manuels d'erreurs :

```bash
python app/test_errors.py
```

Lancer avec Docker :

```bash
docker compose up --build
```

Verifier la configuration Docker Compose :

```bash
docker compose config
```

## Limites connues

- Le champ `author` est actuellement renseigne a `N/A`, car il n'est pas disponible sur les pages scrapees.
- Le programme ecrit en mode append, donc plusieurs executions peuvent creer des doublons dans `books.csv`.
- La variable `MAX_WORKERS` existe dans `main.py`, mais le scraping n'est pas encore parallelise.
- Si la structure HTML du site change, les selecteurs CSS devront etre mis a jour.
- Le service Docker s'appelle `api`, mais l'application actuelle est plutot un worker de scraping.

## Ameliorations possibles

- Ajouter une detection des doublons avant l'ecriture dans le CSV.
- Utiliser `MAX_WORKERS` pour paralleliser l'extraction des details.
- Ajouter une vraie suite de tests unitaires avec `pytest`.
- Rendre les parametres configurables via le fichier `.env`.
- Ajouter une API pour consulter les donnees scrapees.
- Sauvegarder les donnees dans une base de donnees plutot que dans un CSV.

## Resume technique

Ce projet est un pipeline ETL simple :

- **Extract** : recuperation des pages HTML avec `requests`.
- **Transform** : parsing et structuration des donnees avec `BeautifulSoup`.
- **Load** : sauvegarde dans un fichier CSV.

La robustesse repose sur :

- les retries ;
- les timeouts ;
- les blocs `try except` ;
- les logs console et fichier ;
- la separation des responsabilites entre les modules.
