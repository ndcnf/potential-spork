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

## API Contracts To Stabilize

Le backend a besoin de contrats HTTP explicites pour éviter que le frontend dépende d’implémentations implicites ou de champs accidentels.

Principe :

- les routes exposent des schémas stables
- les services portent la logique métier
- les erreurs applicatives sont traduites explicitement en erreurs HTTP
- un router ne contient ni heuristique de scraping, ni logique d’upsert, ni SQL complexe dispersé

### Current Routes To Formalize

#### `GET /health`

But : vérifier que l’application répond.

Réponse minimale :

```json
{"status": "ok"}
```

#### `GET /api/films`

Entrées :

- `q`: recherche libre optionnelle
- `cycle_id`: filtre optionnel
- `priority`: filtre optionnel

Sortie : collection ordonnée de films enrichis avec leur cycle.

Contrat attendu :

- ordre stable
- aucun champ source-specific NIFFF
- priorité issue du modèle produit, pas d’un vocabulaire vendor-specific

#### `PATCH /api/films/{film_id}`

Entrée : mise à jour partielle bornée aux champs éditables côté produit.

Version actuelle minimale :

- `priority`

Erreurs attendues :

- `404` film introuvable
- `422` payload invalide

#### `GET /api/screenings`

Sortie : liste des séances avec état dérivé calculé côté backend.

Le frontend ne doit pas réimplémenter :

- détection de conflit
- statut `past`
- désactivation d’une autre séance du même film

#### `PATCH /api/screenings/{screening_id}`

Entrée : changement de `selection_status`.

Erreurs attendues :

- `404` séance introuvable
- `422` statut invalide
- plus tard potentiellement `409` si une règle métier bloque l’opération

#### `GET /api/planning`

Sortie : séances groupées par jour.

Le groupement temporel doit rester côté backend pour garantir une lecture cohérente du planning.

#### `GET /api/exports/confirmed.ics`

Sortie : calendrier iCal construit uniquement à partir des séances confirmées.

Exigences :

- timezone explicite
- fallback explicite si `ends_at` est absent
- exclusion des séances sans `starts_at`

### Error Mapping Recommendation

Créer à terme des exceptions applicatives explicites, par exemple :

- `SourceFetchError`
- `SourceParseError`
- `ImportConflictError`
- `EntityNotFoundError`

Puis les mapper proprement vers :

- `502` si la source distante est indisponible
- `422` si l’entrée client est invalide
- `404` si l’entité demandée n’existe pas
- `409` si une règle métier ou une collision stable empêche l’opération

## Screening Selection Rules

Ces règles doivent être documentées et testées côté backend. Elles ne doivent pas dériver d’un comportement opportuniste du frontend.

### Current States

Pour l’état persistant de sélection, le backend porte actuellement :

- `none`
- `tentative`
- `confirmed`

Le backend dérive ensuite un état de lecture, par exemple :

- `past`
- `selected`
- `disabled`
- `conflict`
- `available`

### Rules To Preserve

#### 1. Past dominates

Si une séance est déjà passée, son état dérivé doit être `past` même si d’autres signaux existent.

#### 2. Selected dominates for the current row

Si une séance est `tentative` ou `confirmed`, son état dérivé doit être `selected` pour cette ligne.

#### 3. Same-film exclusivity

Si une autre séance du même film est déjà `tentative` ou `confirmed`, la séance courante doit devenir `disabled`.

But :

- éviter plusieurs choix concurrents pour le même film
- centraliser la règle d’exclusivité au backend

#### 4. Time conflict detection

Si une séance chevauche une autre séance déjà retenue, son état dérivé doit être `conflict`.

La règle de chevauchement doit être pure, testable et indépendante du transport HTTP.

#### 5. Confirmed sibling reset

Lorsqu’une séance passe à `confirmed`, les autres séances du même film ne doivent pas rester dans un état concurrent.

Politique actuelle :

- les séances soeurs non rejetées sont remises à `none`

Cette règle doit rester documentée tant qu’un autre workflow n’est pas défini.

### Rule Gap To Clarify

Le backend actuel ne documente pas encore :

- si `tentative` doit aussi réinitialiser les autres séances du même film
- si un statut `rejected` doit exister explicitement dans le contrat public
- si une opération invalide doit être refusée ou simplement normalisée

Ces points doivent être verrouillés avant d’étoffer la logique planning.

## Data Model And Persistence Invariants

Le backend a besoin d’invariants documentés. Sans eux, les imports deviennent fragiles et l’idempotence devient accidentelle.

### Domain Entities

Entités métier visées :

- `Cycle`
- `Film`
- `Venue`
- `Screening`

### Mandatory Distinction

Toujours distinguer :

- identifiant interne de base (`id`)
- identifiant stable de source (`source_key`)

Le `slug` peut aider, mais il ne doit pas être confondu avec une clé d’import garantie.

### Invariants To Document And Test

#### `Cycle`

- porte un rôle éditorial
- ne porte pas la priorité produit
- doit avoir un `source_key` stable si la source en fournit un ou si une clé dérivée est construite

#### `Film`

- la priorité existe uniquement au niveau film
- un film doit pouvoir être réimporté sans changer d’identité interne
- `source_url` ne suffit pas toujours comme clé stable ; documenter le vrai `source_key`

#### `Venue`

- nécessite aussi un identifiant stable
- le nom seul peut être insuffisant si la source varie légèrement son libellé

#### `Screening`

- doit être identifiable indépendamment du `id` SQL
- devrait porter à terme un `source_key`
- devrait porter à terme `source_url` si la source fournit une page ou un lien stable

### Import Invariants

- un import relancé ne doit pas dupliquer les entités déjà connues
- un import partiel ne doit pas corrompre les données existantes
- les warnings d’enrichissement détail ne doivent pas être silencieux
- la transaction d’import doit être bornée explicitement
- la politique de disparition d’une entité source doit être documentée avant toute suppression automatique

### Legacy Compatibility To Phase Out

Le backend porte encore des traces legacy qui contredisent la cible produit :

- `Cycle.priority` alors que la priorité doit vivre uniquement sur `Film`
- valeurs de priorité `ignore / low / medium / high / must-see`

Recommandation :

- documenter une phase de compatibilité
- définir un mapping de migration explicite
- supprimer progressivement les états legacy du contrat public

## Concrete Migration Plan

Objectif : migrer sans casser le comportement utile déjà en place, tout en augmentant la testabilité et l’agnosticisme de la source.

Principe d’exécution :

- une passe = une responsabilité claire
- comportement métier inchangé tant que possible
- tests ajoutés avant ou pendant chaque passe
- pas de refonte ORM + parsing + API dans la même passe

### Phase 0 — Baseline de sécurité

But : arrêter de refactorer à l’aveugle.

À faire :

1. exécuter et stabiliser la suite de tests backend
2. ajouter les dépendances de qualité minimales (`pytest`, puis idéalement `ruff`, `mypy`)
3. créer des fixtures HTML réalistes pour listing et détail
4. documenter la commande unique de validation backend

Livrables attendus :

- suite de tests exécutable localement
- fixtures de parsing versionnées
- point d’entrée de validation clair pour les prochaines passes

### Phase 1 — Couvrir le comportement actuel par des tests

But : figer l’existant utile avant de déplacer les responsabilités.

À tester immédiatement :

#### Parsing / source

- `build_session()`
- `fetch_html()`
- `extract_runtime()`
- `extract_year()`
- `parse_listing_card()`
- `enrich_from_detail()`
- résolution d’URL absolue
- champs absents

#### Services métier

- `screenings_overlap()`
- `derive_screening_state()`
- `sync_film_screening_status()`
- `build_calendar()`

#### API minimale

- `GET /health`
- `GET /api/films`
- `PATCH /api/films/{id}`
- `GET /api/screenings`
- `PATCH /api/screenings/{id}`
- `GET /api/planning`
- `GET /api/exports/confirmed.ics`

Livrables attendus :

- couverture de non-régression sur les helpers critiques
- premiers tests API de contrat
- suppression des zones non testées les plus risquées

### Phase 2 — Assainir l’import actuel sans changer son résultat

But : garder le même import fonctionnel, mais retirer les anti-patterns.

À faire :

1. supprimer `except requests.RequestException: pass`
2. introduire des warnings d’import explicites
3. centraliser les erreurs réseau avec exceptions nommées
4. préparer un rapport d’import structuré avec `warnings` et `errors`

À ne pas faire dans cette phase :

- changer encore le schéma SQL principal
- introduire l’upsert repository sur toutes les entités d’un coup

Livrables attendus :

- import plus observable
- erreurs réseau non silencieuses
- base prête pour un vrai orchestrateur d’import

### Phase 3 — Introduire le modèle canonique d’import

But : couper le lien direct entre parsing source-specific et modèle métier SQLAlchemy.

À créer :

- `app/schemas/imported.py` ou `app/import_models.py`

Types minimum :

- `ImportedCycle`
- `ImportedFilm`
- `ImportedVenue`
- `ImportedScreening`
- `ImportReport`

Règle :

- aucun router FastAPI ne dépend de ces modèles pour l’instant
- le service d’import, lui, doit en dépendre explicitement

Livrables attendus :

- contrat canonique source-agnostic
- base stable pour supporter HTML puis API sans refonte métier

### Phase 4 — Introduire un contrat de source explicite

But : permettre plusieurs implémentations de source sans changer le service métier.

À créer :

- `app/sources/base.py`

Avec par exemple :

- `FestivalSource`
- ou des contrats séparés `fetch_cycles`, `fetch_films`, `fetch_screenings`

Première implémentation :

- `NifffHtmlSource`

Livrables attendus :

- dépendance du service sur un protocole et non sur un module HTML concret
- porte ouverte à une future source API ou snapshot local

### Phase 5 — Ajouter un normalizer HTML

But : transformer les objets parser-specific en objets canoniques.

À créer :

- `app/sources/nifff_html/normalizer.py`

Responsabilités :

- construire les `source_key`
- normaliser les chaînes
- rendre les URLs absolues
- porter les durées et années correctement
- préparer les structures d’upsert

Règle :

- aucune écriture DB dans le normalizer

Livrables attendus :

- séparation nette parser / normalizer
- mapping métier testable sans SQLAlchemy

### Phase 6 — Extraire les repositories

But : sortir les writes SQLAlchemy du service d’import.

À créer :

- `app/repositories/cycles.py`
- `app/repositories/films.py`
- `app/repositories/venues.py`
- `app/repositories/screenings.py`

Responsabilités :

- lookup par clé stable
- upsert
- règles de mise à jour
- `flush()` contrôlés

Attention :

- ne pas faire de `select` profonds dans des boucles sans nécessité
- préparer du préchargement par lots si le catalogue grossit

Livrables attendus :

- SQLAlchemy isolé
- import service plus lisible et plus testable

### Phase 7 — Créer un orchestrateur d’import unique

But : déplacer la coordination complète dans un vrai service métier.

À créer :

- `app/services/import_catalog.py`

Responsabilités :

- choisir la source
- fetcher
- parser
- normaliser
- appeler les repositories
- produire le rapport final

Le fichier legacy `services/import_nifff.py` doit alors :

- soit disparaître
- soit devenir un simple wrapper transitoire

Livrables attendus :

- orchestration centralisée
- code d’import testable de bout en bout avec mocks ciblés

### Phase 8 — Introduire les `source_key` en base

But : garantir l’idempotence autrement que par des heuristiques fragiles.

À faire :

1. ajouter progressivement `source_key` sur `Cycle`, `Film`, `Venue`, `Screening`
2. ajouter les contraintes/index utiles
3. documenter précisément comment chaque clé est construite
4. tester les collisions et réimports

Attention :

- migration SQLite à soigner proprement
- si la pression d’évolution augmente, évaluer PostgreSQL plutôt que multiplier les contournements SQLite

Livrables attendus :

- idempotence documentée
- imports rejouables sans duplication silencieuse

### Phase 9 — Aligner le backend sur les règles produit finales

But : supprimer les contradictions entre doc produit et code backend.

À faire :

1. retirer progressivement `Cycle.priority`
2. introduire un contrat de priorité produit clair
3. conserver temporairement un mapping legacy si nécessaire
4. nettoyer `/gaps` si le placeholder ne correspond plus au produit

Livrables attendus :

- backend cohérent avec `source-of-truth.md`
- disparition graduelle des valeurs legacy du contrat public

### Phase 10 — Finaliser la documentation et les garde-fous CI

But : rendre le système maintenable, pas seulement fonctionnel.

À faire :

1. documenter les contrats API finaux
2. documenter les invariants DB
3. documenter la stratégie de snapshots HTML
4. exécuter automatiquement tests + lint dans CI

Recommandation minimale CI :

- `python -m pytest`
- `ruff check`
- `ruff format --check`
- `mypy` si le typage strict est enclenché

## Recommended File Targets By Phase

### Court terme

- `backend/tests/sources/nifff_html/test_client.py`
- `backend/tests/sources/nifff_html/test_parser.py`
- `backend/tests/core/test_database.py`
- nouveaux tests pour `services/screenings.py`
- nouveaux tests pour `services/export_ics.py`
- nouveaux tests API via `TestClient`

### Moyen terme

- `backend/app/sources/base.py`
- `backend/app/sources/nifff_html/normalizer.py`
- `backend/app/services/import_catalog.py`
- `backend/app/repositories/*.py`
- `backend/app/schemas/imported.py`

### Refactor legacy à faire disparaître

- `backend/app/services/import_nifff.py`
- `backend/app/api/routes/imports.py` comme simple façade fine
- `backend/app/models/cycle.py` pour retirer la priorité cycle
- `backend/app/schemas/common.py` pour sortir des priorités legacy

## Recommended Order If Time Is Tight

Si tu dois maximiser le ratio valeur / risque, l’ordre strict recommandé est :

1. tests unitaires et API sur l’existant
2. suppression des erreurs silencieuses d’import
3. modèle canonique d’import
4. contrat de source
5. normalizer
6. repositories
7. `source_key`
8. nettoyage du legacy métier

Cet ordre évite le refactor cosmétique. Il sécurise d’abord le comportement, puis coupe les dépendances fragiles, puis aligne enfin le modèle produit.

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
