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

État actuel : la route d’import transmet `source_mode`, `year` et `schedule_url` à `import_nifff_catalog`.
Elle ne choisit plus directement entre `NifffArchiveHtmlSource` et `NifffLiveHtmlSource`.

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

#### `POST /api/user-choices/reset`

But : repartir d’un état utilisateur propre sans disperser la logique de reset côté frontend.

Effets attendus :

- remet les priorités film au défaut legacy `low`, exposé côté UI comme `À traiter`
- remet les sélections de séances à `none`
- laisse les données catalogue intactes

Sortie minimale :

```json
{
  "films_reset": 0,
  "screenings_reset": 0
}
```

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

## App Factory And Test Isolation

Le backend ne doit pas forcer les tests API à dépendre du moteur global de production ou de développement.

### Problem To Avoid

Un `app = FastAPI(...)` global avec startup branché directement sur l’engine global crée un couplage dangereux :

- `TestClient` déclenche les hooks de startup
- ces hooks peuvent créer ou migrer la vraie base locale
- les tests deviennent moins déterministes
- la suite de tests peut modifier un environnement développeur par erreur

### Required Pattern

Préférer :

```python
def create_app(*, run_startup_hooks: bool = True) -> FastAPI:
    app = FastAPI(...)
    ...
    if run_startup_hooks:
        @app.on_event("startup")
        def on_startup() -> None:
            ...
    return app


app = create_app()
```

But :

- garder un point d’entrée standard pour `uvicorn`
- permettre aux tests d’instancier une app sans startup side effects
- injecter proprement les dépendances de test

### Test Rule

Les tests API doivent :

- utiliser `create_app(run_startup_hooks=False)`
- surcharger `db_session`
- utiliser une SQLite de test isolée
- ne jamais dépendre de l’engine global de `app.core.database`

### Practical Consequence

Tant que ce pattern n’est pas respecté, la suite API est fragile même si les assertions métier sont bonnes.

## Current Skeleton Introduced

Une première ossature source-agnostique a été posée pour éviter que la prochaine refactor reparte de zéro.

### Added files

- `backend/app/schemas/imported.py`
- `backend/app/sources/base.py`
- `backend/app/sources/nifff_html/source.py`
- `backend/app/sources/nifff_html/normalizer.py`
- `backend/app/services/import_catalog.py`
- `backend/app/services/import_bundle.py`
- `backend/app/services/import_pipeline.py`
- `backend/app/services/import_postprocessing.py`

### Current responsibility split

#### `sources/nifff_html/source.py`

Responsabilité :

- fetch listing
- déléguer le parsing du listing HTML au parser NIFFF HTML
- enrichir avec le détail si disponible
- retourner un `NifffHtmlCatalogPayload` source-specific contenant les `ParsedFilm`

Cette couche connaît encore la source NIFFF et les URLs, mais ne doit pas orchestrer directement `BeautifulSoup` ou les cartes DOM.
Le payload explicite évite que `fetch_catalog()` retourne un `object` ou une liste ambiguë.

#### `sources/nifff_html/parser.py`

Responsabilité :

- transformer un HTML de listing en collection de `ParsedFilm`
- isoler `BeautifulSoup`, les sélecteurs DOM et les heuristiques de cards
- enrichir un `ParsedFilm` depuis un HTML de détail

Cette couche est la seule qui doit connaître les détails DOM NIFFF.

#### `sources/nifff_html/normalizer.py`

Responsabilité :

- transformer `ParsedFilm` en `ImportedFilm`
- construire les `source_key`
- construire les cycles canoniques associés

Cette couche ne doit pas connaître SQLAlchemy.

#### `services/import_catalog.py`

Responsabilité :

- dépendre d’un `FestivalSource`
- normaliser le payload source-specific explicite
- produire un `CanonicalImportBundle`
- préparer un `ImportReport`

Cette couche ne fait pas d’écriture DB. Elle reste donc testable sans SQLAlchemy et sans session.

#### `services/import_bundle.py`

Responsabilité :

- appliquer un `CanonicalImportBundle` en DB
- appeler les repositories d’upsert
- mettre à jour les compteurs de `ImportReport`
- signaler les incohérences génériques du bundle, par exemple une séance qui référence un film absent

Cette couche est source-agnostic : elle ne doit pas importer `sources/nifff_html`, `BeautifulSoup`, ni de logique de parsing.

#### `services/import_pipeline.py`

Responsabilité :

- orchestrer le pipeline générique `import_catalog -> import_bundle -> postprocessors`
- gérer le `commit`
- produire le log final d’import
- convertir `ImportReport` en `ImportSummary`

Cette couche est source-agnostic. Elle reçoit un `FestivalSource` et une liste optionnelle de postprocessors.

#### `services/import_nifff.py`

Responsabilité transitoire :

- choisir la source NIFFF (`demo` / `prod`)
- appeler `run_import_pipeline`
- fournir le postprocessor legacy `package_member`

Le fichier reste spécifique NIFFF, mais il ne porte plus l’orchestration générique de l’import, ni le `commit`, ni le log final.

#### `services/import_postprocessing.py`

Responsabilité :

- isoler les corrections de données post-import qui ne sont ni du parsing, ni de la normalisation, ni de l’upsert générique
- appliquer aujourd’hui la correction legacy `package_member` sur les films déjà présents

Cette couche reste transitoire. Elle existe pour que `import_nifff.py` ne redevienne pas un fichier fourre-tout pendant la migration.

### Transitional rule

Le but de cette ossature n’est pas encore de finir l’architecture. Le but est de couper la dépendance directe :

- avant : `HTML -> parser -> SQLAlchemy direct`
- maintenant : `HTML -> source -> parser -> normalizer -> bundle canonique -> import_pipeline -> import_bundle -> repositories -> postprocessing -> DB commit`

Ce n’est pas l’état final, mais c’est déjà une dépendance bien moins fragile.

## Repository Step Introduced

Une première couche repository a été ajoutée pour sortir les writes ORM les plus évidents du service d’import.

### Added files

- `backend/app/repositories/cycles.py`
- `backend/app/repositories/films.py`

### Current scope

Pour l’instant, ces repositories gèrent seulement :

- lookup par clé actuelle disponible (`slug`)
- création si l’entité n’existe pas
- mise à jour des champs pilotés par l’import
- `flush()` contrôlé

### Important limitation

Ce n’est pas encore la cible finale, parce que :

- le lookup repose encore sur `slug`
- il n’y a pas encore de `source_key` persisté en base
- `Venue` et `Screening` n’ont pas encore leur repository dédié

### Immediate benefit

Malgré cette limite, on a déjà réduit un anti-pattern concret :

- avant : le service d’import faisait lui-même tous les writes SQLAlchemy
- maintenant : le service orchestre, les repositories persistent

Le service devient donc plus simple à lire, plus testable, et plus facile à remplacer quand les `source_key` arriveront en base.

## Source Key Transition Started

La transition a commencé pour `Cycle` et `Film`.

### Current state

- `Cycle.source_key` ajouté
- `Film.source_key` ajouté
- compatibilité SQLite prévue via `run_sqlite_schema_upgrades()`
- repositories mis à jour pour chercher d’abord par `source_key`, puis fallback sur `slug`

### Why this fallback exists

Le fallback `slug` est transitoire et volontaire.

Il sert à :

- reprendre des lignes legacy déjà importées
- backfiller `source_key` au passage d’un réimport
- éviter une rupture brutale pendant la migration

### Explicit rule

Ordre de lookup actuel :

1. `source_key`
2. `slug` en fallback legacy

Règle future cible :

1. `source_key`
2. plus de fallback une fois la migration terminée

### Important limitation

Le modèle n’impose pas encore `source_key` non-null en base.

C’est volontaire à ce stade, parce qu’on est encore dans une phase de transition SQLite/legacy. Une fois les données backfillées et les migrations stabilisées, il faudra durcir :

- `source_key` obligatoire
- index/contrainte réellement exploités comme clé d’upsert principale

## Source Key Extension To Venue And Screening

La même transition a été étendue à `Venue` et `Screening`.

### Current state

- `Venue.source_key` ajouté
- `Screening.source_key` ajouté
- `Screening.source_url` ajouté pour préparer un vrai lien source stable
- compatibilité SQLite prévue pour ces colonnes

### Repository coverage added

Première couverture repository ajoutée pour :

- `VenueRepository`
- `ScreeningRepository`

Ces repositories sont encore minimaux, mais ils posent les invariants suivants :

- lookup principal par `source_key`
- fallback legacy raisonnable quand nécessaire
- mise à jour contrôlée des champs importés

### Important note

Le pipeline canonique ne persiste pas encore réellement `venues` et `screenings` depuis la source HTML actuelle. Cette étape prépare la suite. Le but ici est d’éviter de devoir improviser les contrats de persistence au moment où les screenings arriveront.

## Source Modes: Demo/Archive vs Prod/Live

Convention retenue :

- `demo` = source archive
- `prod` = source live

### Meaning

#### `demo` / archive

But :

- alimenter le produit avant dévoilement officiel
- faire tourner le planning avec des données plausibles
- sécuriser les tests de non-régression avec snapshots historiques
- conserver en DB une copie utilisable sans rappeler la source externe à chaque chargement

Sources typiques :

- Wayback Machine, uniquement sur réimport manuel rare
- archives locales HTML
- snapshots de debug

Règle NIFFF 2025 :

- le mode `demo` ne doit jamais interroger directement `nifff.ch`
- les séances passées doivent venir de la capture 2025 `archive.org`
- une fois importées, les séances sont relues depuis la DB
- changer de source vers `demo` ne doit pas déclencher de nouvel appel Wayback

#### `prod` / live

But :

- servir le vrai programme courant
- faire foi une fois le programme dévoilé

Sources typiques :

- page programme live
- pages détail live
- plus tard éventuellement API live

### Architectural rule

Le backend ne doit pas disperser des `if archive else live` dans toute la logique métier.

La distinction doit vivre au niveau de l’adapter source.

Exemples propres :

- `NifffArchiveHtmlSource`
- `NifffLiveHtmlSource`

Les deux doivent produire le même contrat canonique.

### Operational rule

- avant dévoilement : le mode `demo` est la source opérationnelle utile
- après dévoilement : le mode `prod` devient la référence
- `demo` reste utile pour fixtures, debug, fallback, historique
- le réimport `demo` est une action explicite, pas un effet de bord du chargement UI

### Current implementation state

Une première séparation explicite a été posée :

- `NifffArchiveHtmlSource`
- `NifffLiveHtmlSource`
- alias transitoire `NifffHtmlSource` conservé pour compatibilité

Ce n’est pas encore le choix runtime final, mais l’intention d’architecture est maintenant claire et codée.

### API import contract

Le payload d’import peut explicitement porter :

- `source_mode="demo"` pour archive
- `source_mode="prod"` pour live

But :

- éviter une logique implicite côté backend
- permettre plus tard une bascule contrôlée depuis l’UI ou la config

Le choix runtime `demo` / `prod` est centralisé dans `services/import_nifff.py`.
La route API reste une façade fine autour du service.

### UI recommendation for Settings

Oui, un CTA dans `Settings` est possible.

Mais il doit rester :

- secondaire
- explicite sur son impact
- formulé comme une bascule de source de données, pas comme une décision produit centrale

Recommandation de wording :

- `Source de données : Démo (archive) / Live (prod)`

Règle UX :

- ne pas mettre ce CTA au coeur du parcours principal
- le laisser dans `Settings`, car c’est une capacité technique/opérationnelle

### Live source failure handling

Le mode `prod` dépend d’une source HTML externe vivante. Cette source peut :

- changer d’URL
- répondre `404`
- répondre partiellement
- devenir temporairement indisponible

Règle backend :

- une erreur réseau ou HTTP de la source ne doit pas remonter en `500` brut non qualifié
- l’API d’import doit traduire cela en erreur `502`
- le message doit indiquer que la source NIFFF est indisponible
- en mode `prod`, une page récupérée mais parsée avec `0` film n’est pas un succès : l’import doit renvoyer une erreur explicite, car cela signale probablement une URL live incorrecte ou un parser HTML dépassé

Pourquoi :

- `500` fait croire à un bug applicatif interne
- `502` exprime correctement une dépendance distante défaillante
- le frontend peut alors afficher un message d’état plus juste à l’utilisateur

### Current live URL default

Le défaut actuel pour le mode `prod` vise :

- `https://nifff.ch/programme/`

et non :

- `https://nifff.ch/programme/?type=film`

Ce choix est plus robuste pour la phase actuelle, car le point d’entrée live ne garantit pas forcément le même schéma de query que l’archive.

## Current Regression Fixes And Known Limits

### Film default status on fresh import

Règle produit attendue :

- un film importé arrive en état `À traiter`

Conséquence technique actuelle :

- la priorité par défaut d’un film importé ne doit pas être `medium`
- elle doit retomber sur l’équivalent legacy de `À traiter`, donc `low`

Règle de migration transitoire appliquée :

- les films nouvellement importés reçoivent `low`
- les anciennes bases où tous les films étaient encore à `medium` sont normalisées vers `low` par la migration SQLite
- les choix explicites existants (`medium`, `high`, `must-see`, `ignore`) sont préservés pendant l’upsert
- la règle backend est centralisée dans `app/core/priorities.py`

### Runtime display for durations

Dans l’UI, la durée film ne doit pas être affichée brutalement en minutes si la lecture produit attend un format plus humain.

Règle :

- préférer un affichage `2h26` à `146 min` dès que la durée dépasse une heure

### Shorts programs / film packages

Règle métier importante.

Les `film-package` ou programmes de courts ne se comportent pas comme un film simple.

Règle métier :

- le choix se fait par séance / package projeté
- pas par pseudo-film aplati comme un long métrage standard
- le modèle canonique distingue :
  - `standalone` : un film planifiable directement
  - `package` : un programme projeté comme une séance unique
  - `package_member` : un contenu inclus dans un package, conservé en donnée mais non planifié seul

Conséquence :

- si un programme shorts apparaît dans la source, il ne faut pas le traiter naïvement comme un film classique sans modéliser le package et ses séances
- l'UI de décision doit présenter le `package`, pas chaque `package_member` comme choix indépendant

Statut :

- implémenté dans le pipeline `parser -> normalizer -> import service -> repositories -> DB`
- le normalizer classe les URLs `/film-package/` comme `package`
- les films sans séance dans une catégorie où un package existe sont classés `package_member`
- l'import resynchronise aussi les anciens films déjà présents en DB pour éviter un état mixte après reimport

## Bundle Persistence Extended

Le wrapper legacy `import_nifff.py` persiste maintenant aussi les `venues` et `screenings` présents dans le bundle canonique.

### Current behavior

Si `import_catalog()` renvoie :

- des `ImportedVenue`
- des `ImportedScreening`

alors le service :

1. upsert les `Cycle`
2. upsert les `Film`
3. upsert les `Venue`
4. upsert les `Screening`

### Guard rail added

Une `ImportedScreening` dont le `film_source_key` ne correspond à aucun film importé est ignorée avec warning explicite.

Pourquoi :

- éviter une ligne orpheline incohérente
- éviter un plantage opaque plus bas dans la persistence
- rendre le défaut visible en logs

### Important limitation

La source HTML NIFFF actuelle ne produit pas encore réellement ces screenings dans le pipeline standard. La persistence est prête, la collecte source ne l’est pas encore totalement.

## Screening Parsing Skeleton Started

Le parsing HTML commence maintenant à exposer une structure de screenings côté source-specific.

### Current shape

Le parser NIFFF peut désormais produire, au niveau d’un film enrichi :

- une liste de `ParsedScreening`

Chaque `ParsedScreening` porte au minimum :

- `starts_at`
- `ends_at`
- `venue_name`
- `ticket_url`
- `source_url`

### Important scope

Ce parsing reste volontairement un squelette heuristique. Il sert à poser le contrat entre parser et normalizer, pas à prétendre que le DOM NIFFF est déjà totalement maîtrisé sur les screenings.

### Immediate benefit

Grâce à cette étape :

- le normalizer peut produire des `ImportedVenue`
- le normalizer peut produire des `ImportedScreening`
- le service d’import peut persister ces objets si la source les fournit

Autrement dit, le pipeline complet existe maintenant conceptuellement aussi pour les screenings, même si les heuristiques HTML devront encore être durcies sur de vrais cas source.

## Import Report Now Carries Operational Counters

Le backend expose maintenant un résumé d’import plus utile, même avant d’avoir les vraies données finales.

### Current counters

Le résumé d’import remonte désormais :

- `cycles_created`
- `films_created`
- `films_updated`
- `venues_created`
- `venues_updated`
- `screenings_created`
- `screenings_updated`
- `warnings_count`
- `errors_count`
- `warnings`
- `errors`

### Why this matters now

Même avec des données Wayback non parfaitement fidèles, ces compteurs sont précieux pour :

- détecter une duplication anormale
- vérifier que des screenings remontent bien dans le pipeline
- voir rapidement si le parse produit beaucoup d’objets mais peu de persistence
- repérer des warnings structurels lors d’un essai sur snapshot historique
- lire les messages de warning sans devoir aller chercher les logs backend

### Missing vs inferred data

Règle actuelle :

- si une donnée source est absente et ne peut pas être déduite proprement, le backend conserve `None`
- si une donnée est déduite, le normalizer doit rendre cette déduction visible via `CanonicalImportBundle.warnings`
- exemple actuel : si `ends_at` manque sur une séance mais que `duration_minutes` existe, `ends_at` est inféré et un warning est ajouté
- si `ends_at` manque et que `duration_minutes` manque aussi, `ends_at` reste `None` et un warning signale que la fin de séance ne peut pas être déduite

But : ne pas présenter une donnée déduite comme si elle venait directement de la source NIFFF.

### Real datetime vs festival day

Les séances doivent garder deux notions séparées :

- `starts_at` / `ends_at` représentent la vraie date et heure de projection
- le `festival day` représente le jour éditorial utilisé pour l’affichage et le grouping

Règle actuelle :

- une séance indiquée par la source comme `05.07, 01:00` appartient au festival day `2025-07-05`
- sa vraie date de projection est `2025-07-06T01:00`
- le premier jour suit la même règle : une séance indiquée comme `04.07, 00:45` appartient au festival day `2025-07-04`, mais sa vraie projection est `2025-07-05T00:45`
- le cutoff de journée festival est `06:00`
- l’export iCal utilise toujours `starts_at` / `ends_at`, donc les vraies dates/heures, jamais le festival day

Cette séparation évite de casser les conflits réels, l’export calendrier et l’affichage par journée festival.

Quand une correction de parsing change une vraie date de séance, le `source_key` peut changer car il contient `starts_at`.
L’import du catalogue doit alors reconnaître la séance corrigée, mettre à jour l’ancienne ligne en conservant le choix utilisateur, puis supprimer les anciennes séances source-keyées qui ne sont plus présentes dans le bundle courant.

### About Wayback data

Des snapshots Wayback de l’année passée sont utiles, même s’ils ne sont pas 1:1 avec la version courante.

Bon usage :

- en faire des fixtures réalistes de non-régression
- tester la robustesse des heuristiques DOM
- valider la forme générale du pipeline

À ne pas faire :

- considérer ces snapshots comme vérité métier finale
- verrouiller des sélecteurs trop spécifiques uniquement à cette version archivée

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

### Transitional Hardening Rule

Tant que le service legacy `import_nifff.py` existe encore, il ne doit plus contenir d’échec silencieux.

Minimum acceptable :

- conserver la donnée listing si le détail échoue
- émettre un warning structuré côté logs
- garder le comportement d’import principal inchangé

Refus explicite :

- `except requests.RequestException: pass`

Pourquoi :

- ce pattern masque une rupture source
- il empêche de comprendre pourquoi un film est importé partiellement
- il rend les régressions scraper beaucoup plus coûteuses à diagnostiquer

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

## Pytest Test Matrix By File

Objectif : avoir une cartographie concrète des tests à écrire pour détecter les régressions utiles, sans tester des détails d’implémentation triviaux.

Principe :

- un fichier de tests cible une responsabilité
- on teste le comportement observable
- les fixtures HTML servent à figer les cas réalistes de parsing
- les mocks servent à isoler le réseau, pas à masquer la logique métier

### `backend/tests/sources/nifff_html/test_client.py`

Responsabilité : couche transport HTTP.

Déjà présent :

- `build_session()` positionne le `User-Agent`
- `fetch_html()` renvoie `response.text`
- propagation d’erreur HTTP

À ajouter :

- timeout personnalisé transmis à `session.get()`
- propagation de `requests.Timeout`
- propagation de `requests.ConnectionError`
- vérification qu’aucune logique de parsing ne vit dans le client

Nom de tests recommandés :

- `test_fetch_html_uses_custom_timeout`
- `test_fetch_html_propagates_timeout`
- `test_fetch_html_propagates_connection_error`

### `backend/tests/sources/nifff_html/test_parser.py`

Responsabilité : parsing HTML pur, sans DB.

Déjà présent :

- `slugify()`
- `extract_runtime()`
- `extract_year()`
- `clean_text()`
- `field_after_heading()`
- `extract_table_value()`
- `extract_archive_cards()`
- `parse_listing_card()`
- `enrich_from_detail()`

À ajouter :

- `slugify()` sur chaîne vide ou accentuée
- `extract_runtime()` quand le format est non reconnu
- `extract_year()` quand plusieurs années apparaissent
- `extract_poster_url()` avec `data-src`, `src`, `og:image`, puis fallback
- `extract_short_description()` fallback meta description
- `parse_listing_card()` quand le lien est absent
- `parse_listing_card()` quand le titre est absent
- `parse_listing_card()` avec infos partielles
- `enrich_from_detail()` quand certains champs ne sont pas présents
- `field_after_heading()` si plusieurs blocs non pertinents s’intercalent

Nom de tests recommandés :

- `test_slugify_returns_unknown_for_empty_value`
- `test_extract_runtime_returns_none_for_unrecognized_format`
- `test_extract_poster_url_prefers_header_image_data_src`
- `test_extract_poster_url_falls_back_to_og_image`
- `test_extract_short_description_falls_back_to_meta_description`
- `test_parse_listing_card_returns_none_without_link`
- `test_parse_listing_card_returns_none_without_title`
- `test_enrich_from_detail_preserves_existing_values_when_missing`

### `backend/tests/sources/nifff_html/test_parser_fixtures.py`

Responsabilité : parser sur snapshots HTML réalistes versionnés.

À créer :

- fixtures de listing réel simplifié
- fixtures de détail réel simplifié
- fixtures volontairement dégradées

Cas à couvrir :

- listing nominal multi-cartes
- page détail nominale
- page détail sans distribution
- page détail sans poster
- structure HTML légèrement modifiée

Nom de tests recommandés :

- `test_listing_snapshot_extracts_expected_number_of_cards`
- `test_listing_snapshot_parses_expected_film_fields`
- `test_detail_snapshot_extracts_expected_optional_fields`
- `test_detail_snapshot_tolerates_missing_distribution`
- `test_detail_snapshot_tolerates_missing_poster`

### `backend/tests/core/test_database.py`

Responsabilité : compatibilité SQLite et upgrades de schéma.

Déjà présent :

- ajout des colonnes manquantes
- idempotence de l’upgrade

À ajouter :

- aucun effet si la table n’existe pas
- aucun effet sur une URL non SQLite
- `_engine_connect_args()` renvoie bien `check_same_thread=False` pour SQLite

Nom de tests recommandés :

- `test_run_sqlite_schema_upgrades_skips_missing_tables`
- `test_run_sqlite_schema_upgrades_noops_for_non_sqlite_engine`
- `test_engine_connect_args_enable_check_same_thread_for_sqlite`

### `backend/tests/services/test_screenings.py`

Responsabilité : logique métier de disponibilité et de sélection des séances.

À créer.

Cas à couvrir :

- `screenings_overlap()` faux si même `id`
- `screenings_overlap()` faux si date manquante
- `screenings_overlap()` vrai si chevauchement réel
- `derive_screening_state()` retourne `past`
- `derive_screening_state()` retourne `selected` pour `tentative`
- `derive_screening_state()` retourne `selected` pour `confirmed`
- `derive_screening_state()` retourne `disabled` si une autre séance du même film est retenue
- `derive_screening_state()` retourne `conflict` si chevauchement avec séance retenue
- `derive_screening_state()` retourne `available` sinon
- `sync_film_screening_status()` remet les séances soeurs à `none` après un `confirmed`
- `sync_film_screening_status()` ne modifie rien si la séance n’est pas `confirmed`

Nom de tests recommandés :

- `test_screenings_overlap_returns_false_for_same_screening`
- `test_screenings_overlap_returns_false_when_boundaries_missing`
- `test_screenings_overlap_returns_true_for_overlapping_ranges`
- `test_derive_screening_state_returns_past_for_elapsed_screening`
- `test_derive_screening_state_returns_selected_for_confirmed_screening`
- `test_derive_screening_state_returns_disabled_when_sibling_is_selected`
- `test_derive_screening_state_returns_conflict_when_selected_screening_overlaps`
- `test_sync_film_screening_status_resets_siblings_when_confirmed`

### `backend/tests/services/test_export_ics.py`

Responsabilité : export iCal pur.

À créer.

Cas à couvrir :

- création d’un calendrier valide avec une séance
- exclusion d’une séance sans `starts_at`
- fallback sur `film_duration_minutes` si `ends_at` absent
- fallback à `120` minutes si durée absente
- conservation de la timezone festival
- compatibilité avec dict et objet attributaire

Nom de tests recommandés :

- `test_build_calendar_creates_event_for_valid_screening`
- `test_build_calendar_skips_screening_without_start`
- `test_build_calendar_uses_duration_fallback_when_end_missing`
- `test_build_calendar_uses_default_duration_when_missing_everywhere`
- `test_ensure_local_datetime_converts_aware_datetime_to_festival_timezone`
- `test_row_value_supports_mapping_and_object_inputs`

### `backend/tests/services/test_import_nifff.py`

Responsabilité : service legacy actuel tant qu’il existe.

À créer.

Cas à couvrir :

- import nominal avec création cycle + film
- import relancé sans duplication film
- mise à jour d’un film existant
- enrichissement détail indisponible mais import listing conservé
- plusieurs cartes avec même cycle
- carte invalide ignorée

Important :

- mocker le réseau
- utiliser une DB SQLite de test
- vérifier le résultat métier en base, pas le détail des appels internes

Nom de tests recommandés :

- `test_import_nifff_catalog_creates_cycles_and_films`
- `test_import_nifff_catalog_is_idempotent_for_existing_film`
- `test_import_nifff_catalog_updates_existing_film_fields`
- `test_import_nifff_catalog_keeps_listing_data_when_detail_fetch_fails`
- `test_import_nifff_catalog_skips_invalid_cards`

### `backend/tests/services/test_import_catalog.py`

Responsabilité : futur orchestrateur source-agnostic.

À créer quand `services/import_catalog.py` existe.

Cas à couvrir :

- sélection de la source attendue
- orchestration `fetch -> parse -> normalize -> persist`
- remontée des warnings du normalizer
- import report final complet
- erreur source traduite en erreur applicative explicite

Nom de tests recommandés :

- `test_import_catalog_orchestrates_source_parser_normalizer_and_repositories`
- `test_import_catalog_copies_normalizer_warnings_to_report`
- `test_import_catalog_raises_explicit_error_when_source_fetch_fails`

### `backend/tests/repositories/test_cycles.py`

Responsabilité : upsert cycle par clé stable.

À créer quand les repositories existent.

Cas à couvrir :

- création sur clé inconnue
- réutilisation sur clé existante
- mise à jour des champs autorisés
- conservation des champs non pilotés par la source si nécessaire

Nom de tests recommandés :

- `test_cycle_repository_creates_cycle_when_source_key_unknown`
- `test_cycle_repository_updates_existing_cycle_when_source_key_known`

### `backend/tests/repositories/test_films.py`

Responsabilité : upsert film.

Cas à couvrir :

- création film initiale
- mise à jour film existant
- rattachement au cycle attendu
- non-duplication sur réimport
- gestion d’un champ optionnel manquant

Nom de tests recommandés :

- `test_film_repository_creates_film_from_imported_model`
- `test_film_repository_updates_existing_film_without_duplication`
- `test_film_repository_preserves_identity_across_reimports`

### `backend/tests/repositories/test_venues.py`

Responsabilité : upsert venue.

Cas à couvrir :

- création venue
- réutilisation venue existante par clé stable
- variation de nom traitée selon la règle définie

### `backend/tests/repositories/test_screenings.py`

Responsabilité : upsert screening.

Cas à couvrir :

- création screening initiale
- mise à jour horaire d’une screening existante
- rattachement film / venue correct
- non-duplication sur même `source_key`
- collision de clé détectée proprement

### `backend/tests/api/test_health.py`

Responsabilité : contrat minimal de santé.

À créer.

Cas à couvrir :

- `200 OK`
- payload exact attendu

Nom de test recommandé :

- `test_healthcheck_returns_ok_status`

### `backend/tests/api/test_films.py`

Responsabilité : contrat HTTP des films.

À créer.

Cas à couvrir :

- liste ordonnée de films
- filtre `q`
- filtre `cycle_id`
- filtre `priority`
- `PATCH` met à jour la priorité
- `PATCH` sur id inconnu renvoie `404`
- `PATCH` invalide renvoie `422`

Nom de tests recommandés :

- `test_list_films_returns_ordered_films`
- `test_list_films_filters_by_query`
- `test_list_films_filters_by_cycle_id`
- `test_list_films_filters_by_priority`
- `test_update_film_updates_priority`
- `test_update_film_returns_404_for_unknown_id`

### `backend/tests/api/test_screenings.py`

Responsabilité : contrat HTTP des séances.

À créer.

Cas à couvrir :

- liste avec `derived_state`
- `PATCH` met à jour `selection_status`
- `PATCH` répercute la règle sur les séances soeurs
- `PATCH` sur id inconnu renvoie `404`
- `PATCH` invalide renvoie `422`

Nom de tests recommandés :

- `test_list_screenings_returns_derived_states`
- `test_update_screening_updates_selection_status`
- `test_update_screening_resets_sibling_states_when_confirmed`
- `test_update_screening_returns_404_for_unknown_id`

### `backend/tests/api/test_planning.py`

Responsabilité : groupement planning.

À créer.

Cas à couvrir :

- groupement par date ISO
- exclusion des séances sans `starts_at`
- ordre stable des jours

Nom de tests recommandés :

- `test_get_planning_groups_screenings_by_day`
- `test_get_planning_skips_screenings_without_start`
- `test_get_planning_returns_days_in_sorted_order`

### `backend/tests/api/test_export.py`

Responsabilité : contrat HTTP de l’export iCal.

À créer.

Cas à couvrir :

- `200 OK`
- `media_type` correct
- header `Content-Disposition`
- seules les séances `confirmed` sont exportées

Nom de tests recommandés :

- `test_export_confirmed_ics_returns_calendar_response`
- `test_export_confirmed_ics_only_contains_confirmed_screenings`

### `backend/tests/api/test_imports.py`

Responsabilité : contrat HTTP de lancement d’import.

À créer.

Cas à couvrir :

- payload minimal valide
- `schedule_url` valide accepté
- payload invalide renvoie `422`
- service appelé avec les bons paramètres
- propagation propre d’une erreur métier d’import

Nom de tests recommandés :

- `test_import_catalog_accepts_minimal_payload`
- `test_import_catalog_accepts_schedule_url`
- `test_import_catalog_returns_422_for_invalid_payload`

### `backend/tests/api/conftest.py`

Responsabilité : fixtures partagées API.

À créer.

Doit fournir :

- application de test
- session DB isolée
- override de dépendance `db_session`
- helpers de seed (`film`, `cycle`, `venue`, `screening`)

Règle :

- pas de dépendance à la base locale développeur
- base de test recréée ou rollbackée proprement pour chaque test

### `backend/tests/conftest.py`

Responsabilité : fixtures transverses backend.

À créer ou enrichir.

Doit fournir selon besoin :

- factory de datetime timezone-aware
- snapshots HTML chargés depuis `tests/fixtures/`
- factory d’objets `ImportedFilm` futurs
- utilitaires de session SQLite de test

## Fixtures Directory Recommendation

Structure recommandée :

```text
backend/tests/
  fixtures/
    nifff_html/
      listing_nominal.html
      listing_missing_title.html
      detail_nominal.html
      detail_missing_distribution.html
      detail_missing_poster.html
```

Règles :

- nommer les fixtures par scénario métier, pas par date arbitraire
- garder les fixtures assez petites pour rester lisibles
- ne pas anonymiser au point de casser la structure DOM utile

## Minimum Test Pack To Build First

Si le temps est court, commencer exactement par ces fichiers :

1. `backend/tests/services/test_screenings.py`
2. `backend/tests/services/test_export_ics.py`
3. `backend/tests/services/test_import_nifff.py`
4. `backend/tests/api/conftest.py`
5. `backend/tests/api/test_films.py`
6. `backend/tests/api/test_screenings.py`
7. `backend/tests/api/test_export.py`

Pourquoi :

- ce sont les zones où une régression aurait un impact produit direct
- ce sont aussi les zones actuellement les moins couvertes
- elles sécurisent le futur refactor vers un backend source-agnostic

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


## notes humaines

Le reset des choix utilisateur est désormais porté par `POST /api/user-choices/reset` côté backend. Il remet les films à `low`, puis le frontend affiche cet état legacy comme `À traiter`.
Pour les seances shorts, au final pour la construction d'un choix de film, il faut se baser sur ce qui constitue une seance dans le programme.
Quand une métadonnée éditoriale comme l'année ou le pays est absente, l'UI doit masquer cette partie au lieu d'afficher un placeholder de type `année ?` ou `Pays ?`. Les autres morceaux disponibles, par exemple une durée seule, restent affichables ; seul le séparateur médian est supprimé quand un côté manque.
