# Backend Import Architecture

## Goal

Construire une chaîne d’import robuste pour NIFFF qui :

- supporte d’abord le scraping HTML
- puisse accepter plus tard une API sans refonte métier
- garde le reste de l’application agnostique de la source
- évite que le DOM ou un JSON vendor-specific contaminent le modèle produit

## Problem With Current State

Le service actuel `app/services/import_nifff.py` mélange trop de responsabilités :

- transport HTTP
- parsing HTML
- heuristiques de scraping
- enrichissement détail
- mapping métier
- upsert SQLAlchemy

Conséquences :

- fort couplage au DOM
- faible testabilité
- évolution difficile si une API apparaît
- gestion d’erreur trop grossière
- risque élevé de fragilité annuelle

## Design Principle

Le coeur de l’application ne doit dépendre ni :

- du HTML NIFFF
- de sélecteurs CSS
- d’une structure JSON externe

Le backend doit dépendre uniquement d’un **modèle canonique d’import**.

## Target Layers

### 1. Source Adapter

Responsabilité : récupérer la donnée brute.

Exemples :

- `NifffHtmlSource`
- `NifffApiSource`
- plus tard éventuellement `CachedSource`

Cette couche connaît :

- URL
- headers
- auth si nécessaire
- timeouts
- retries
- récupération de pages / endpoints

Elle ne connaît pas :

- SQLAlchemy
- modèles métier internes
- logique d’upsert

### 2. Parser

Responsabilité : transformer le raw en objets intermédiaires proches de la source.

Exemples :

- `HtmlFilmCard`
- `HtmlFilmDetail`
- `HtmlScreeningRow`
- ou côté API : `ApiFilmPayload`, `ApiScreeningPayload`

Cette couche connaît :

- DOM
- BeautifulSoup
- structure JSON source

Elle ne connaît pas :

- la DB
- les routes FastAPI
- les modèles finaux de l’app

### 3. Normalizer

Responsabilité : convertir les objets source-specific en modèle canonique interne.

Exemples cibles :

- `ImportedCycle`
- `ImportedFilm`
- `ImportedVenue`
- `ImportedScreening`

Cette couche porte :

- normalisation des strings
- timezone
- durées en minutes
- URLs absolues
- dédoublonnage léger
- mapping de champs optionnels

Le reste du backend doit dépendre de ce contrat.

### 4. Import Service

Responsabilité : orchestrer l’import.

Exemples :

- choisir la source
- récupérer le raw
- parser
- normaliser
- appeler les repositories d’upsert
- produire un rapport d’import

Cette couche ne doit pas contenir de sélecteurs DOM.

### 5. Repository Layer

Responsabilité : écrire en base via un contrat stable.

Exemples :

- `CycleRepository`
- `FilmRepository`
- `VenueRepository`
- `ScreeningRepository`

Cette couche gère :

- lookup par identifiants stables
- upsert
- transactions
- règles de mise à jour

## Proposed Directory Structure

```text
backend/app/
  core/
  api/
  models/
  schemas/
  repositories/
    cycles.py
    films.py
    venues.py
    screenings.py
  sources/
    base.py
    nifff_html/
      client.py
      parser.py
      normalizer.py
    nifff_api/
      client.py
      normalizer.py
  services/
    import_catalog.py
    export_ics.py
    screenings.py
```

Optionnel plus tard :

```text
  sources/
    snapshots/
```

pour la persistance des raw fetches ou fixtures de debug.

## Canonical Import Model

Le point central est de définir un schéma canonique indépendant de la source.

Exemple minimal :

```python
from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class ImportedCycle:
    source_key: str
    name: str
    slug: str
    color: str | None = None


@dataclass(slots=True)
class ImportedFilm:
    source_key: str
    title: str
    slug: str
    source_url: str | None
    cycle_source_key: str | None
    directors: str | None
    year: int | None
    countries: str | None
    duration_minutes: int | None
    tagline: str | None
    premiere_label: str | None
    short_description: str | None
    cast: str | None
    synopsis: str | None
    language: str | None
    age_rating: str | None
    poster_url: str | None


@dataclass(slots=True)
class ImportedVenue:
    source_key: str
    name: str


@dataclass(slots=True)
class ImportedScreening:
    source_key: str
    film_source_key: str
    venue_source_key: str | None
    starts_at: datetime | None
    ends_at: datetime | None
    source_url: str | None = None
    ticket_url: str | None = None
```

## Source Keys

Sujet critique.

Il faut distinguer :

- `db id` interne
- `source_key` stable issu de la source

Le modèle actuel repose surtout sur `slug` pour les films. Ce n’est pas forcément assez robuste.

Recommandation :

- ajouter progressivement des champs de type `source_key` / `external_id`
- si la source n’en fournit pas, construire une clé stable explicite

Exemples :

- film : slug source ou URL canonique
- cycle : slug normalisé du nom
- screening : hash déterministe de `film + venue + starts_at`

La clé doit être documentée et testée.

## Source Contract

Créer un contrat clair côté source.

Exemple :

```python
from typing import Protocol


class FestivalSource(Protocol):
    def fetch_catalog(self, year: int) -> object: ...
```

Version plus propre si on veut séparer les flux :

```python
class FestivalSource(Protocol):
    def fetch_cycles(self, year: int) -> object: ...
    def fetch_films(self, year: int) -> object: ...
    def fetch_screenings(self, year: int) -> object: ...
```

Le service d’import dépend du contrat, pas d’une implémentation HTML spécifique.

## Transport Rules

Pour toute source réseau, imposer :

- `requests.Session`
- `User-Agent` explicite
- timeout explicite
- retry limité avec backoff
- erreurs réseau typées

Refus :

- fetch sans timeout
- `except Exception: pass`
- logique réseau dispersée dans le parser

## Parsing Rules For HTML

Le parser HTML doit être robuste mais pas illusionné.

Privilégier :

- ancrages sémantiques
- libellés visibles
- relations de voisinage
- structure répétitive métier
- URLs spécifiques au contenu

Éviter :

- sélecteurs CSS trop profonds
- classes décoratives
- dépendance au `nth-child`
- suppositions implicites non testées

Le parser doit remonter explicitement :

- champs manquants
- blocs non reconnus
- cardinalités inattendues

## Keep Raw Snapshots

Recommandation forte : conserver le raw fetché, au moins en debug ou en mode snapshot.

Pourquoi :

- rejouer un parse sans refetch
- comparer deux versions de site
- écrire des tests de parsing réalistes
- auditer les ruptures quand le DOM change

Formes possibles :

- HTML brut timestampé
- JSON brut source
- hash + date + URL

## Import Report

Chaque import devrait produire un rapport structuré.

Exemple :

```python
@dataclass(slots=True)
class ImportReport:
    source_name: str
    year: int
    cycles_created: int
    cycles_updated: int
    films_created: int
    films_updated: int
    venues_created: int
    screenings_created: int
    screenings_updated: int
    warnings: list[str]
    errors: list[str]
```

Ce rapport est utile pour :

- logs
- observabilité
- endpoint d’admin
- tests

## Idempotence Rules

L’import doit être relançable sans dégrader la base.

Donc :

- upsert, pas append naïf
- lookup sur clés stables
- transaction bornée
- politique claire sur les suppressions / disparitions source

Recommandation initiale :

- ne pas supprimer automatiquement en première version
- marquer ou journaliser ce qui a disparu
- traiter la suppression plus tard avec prudence

## SQLAlchemy Recommendations

Le service d’import ne doit pas manipuler directement trop de logique ORM.

Préférer :

- repositories dédiés
- requêtes ciblées
- `select()` explicites
- `flush()` contrôlés
- transaction unique par import ou sous-lots cohérents

Si les données grossissent :

- précharger les entités existantes par lots
- éviter les `select` dans des boucles profondes

Le code actuel fait des lookups DB dans la boucle film par film. C’est acceptable pour un petit catalogue, mais c’est une pente glissante.

## Proposed Migration Path From Current Code

Execution recommendation:

- start with passes 1 and 2 only
- keep behavior identical
- do not refactor DB writes in the same pass
- validate after each pass before introducing the canonical model

### Step 1

Extraire le code HTTP de `import_nifff.py` vers :

- `sources/nifff_html/client.py`

Concrete result expected:

- session builder centralisé
- `User-Agent` centralisé
- `fetch_html()` unique avec timeout explicite

### Step 2

Extraire les helpers BeautifulSoup vers :

- `sources/nifff_html/parser.py`

Concrete result expected:

- `ParsedFilm` déplacé
- helpers DOM isolés
- parsing listing / detail réutilisable et testable sans DB

### Test-first checkpoint before Step 3

Avant d’introduire le modèle canonique et les repositories, priorité aux tests sur les passes 1 et 2.

But :

- figer le comportement actuel utile
- sécuriser les prochains refactors
- détecter vite une rupture liée au DOM ou aux helpers de parsing

Minimum à couvrir tout de suite :

- `build_session()`
- `fetch_html()`
- `extract_runtime()`
- `extract_year()`
- `parse_listing_card()`
- `enrich_from_detail()`

### Step 3

Introduire les modèles canoniques dans :

- `app/schemas/imported.py`
  ou
- `app/import_models.py`

### Step 4

Créer un normalizer HTML :

- `sources/nifff_html/normalizer.py`

### Step 5

Créer un service d’orchestration :

- `services/import_catalog.py`

### Step 6

Créer les repositories d’upsert.

### Step 7

Faire de `app/api/routes/imports.py` un simple appel au service.

## Testing Strategy

Minimum requis :

### Unit tests

- parsing runtime
- parsing year
- normalisation des URLs
- construction des `source_key`

### Parser fixture tests

- HTML listing réel sauvegardé
- HTML détail réel sauvegardé
- cas avec champs absents
- cas avec structure modifiée

### Import service tests

- import initial
- import relancé idempotent
- upsert film existant
- screening nouvelle vs screening existante

### Failure tests

- timeout réseau
- page invalide
- HTML incomplet
- collision de clé source

## Current Model Gaps To Anticipate

Le modèle SQLAlchemy actuel n’est pas encore idéal pour ce design.

Gaps probables :

- pas de `source_key` explicite sur `Film`, `Cycle`, `Screening`, `Venue`
- `Screening` n’a pas encore de `source_url`
- `Venue` devra probablement porter un identifiant stable lui aussi
- l’import des screenings devra être pensé comme un vrai flux, pas un append artisanal

## Final Recommendation

Le point critique n’est pas seulement “faire un scraper”.

Le point critique est de construire un **pipeline d’import source-agnostic**.

La bonne dépendance est :

`source -> parser -> normalizer -> import service -> repositories -> DB`

Pas :

`HTML -> BeautifulSoup -> SQLAlchemy direct`

Le jour où une API apparaît, tu dois pouvoir changer l’adapter, pas le produit.
