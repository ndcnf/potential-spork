# Source Of Truth

## Product Goal

NIFFF Planner est un planner personnel **film-first**.

Promesse :

**m’aider à transformer une envie de films en planning réaliste, sans me faire penser comme un expert du festival.**

Le produit ne doit pas :

- ressembler à un agrégat d’outils experts
- forcer un tunnel rigide
- cacher sa logique derrière une optimisation opaque

## Active Scope

Vues actives :

- `Films`
- `Planning`
- `Settings` secondaire

Hors scope courant :

- `Trous / Free Slots`

## Workflow

Le workflow courant repose sur 2 espaces :

- `Films`
- `Planning`

Règles :

- ce ne sont pas des étapes verrouillées
- aller-retour libre entre `Films` et `Planning`
- pas d’étapes numérotées imposées
- pas de CTA structurel `Passer au Planning`
- la progression doit informer, pas forcer

## View Roles

### `Films`

Rôle : **qualifier les films**.

Questions auxquelles la vue doit répondre vite :

- pourquoi ce film m’intéresse
- à quel point je veux le voir
- qu’est-ce qu’il me reste à trier

Ce n’est pas :

- un tableau utilitaire
- un planner déguisé
- un dump de métadonnées

### `Planning`

Rôle : **arbitrer des séances**.

Questions auxquelles la vue doit répondre vite :

- qu’est-ce qui est déjà retenu
- où sont les conflits
- que vais-je perdre si je choisis cette séance

Ce n’est pas :

- un catalogue bis
- un écran de découverte
- une console multi-CTA

### `Settings`

Rôle : configuration secondaire.

Les réglages ne doivent pas absorber des décisions produit qui devraient vivre dans `Films` ou `Planning`.

### Data Source Switching

La source de données est un catalogue complet, pas un patch partiel.

Règles :

- `Démo` affiche uniquement cycles, films et séances de démonstration
- `Live` affiche uniquement cycles, films et séances live
- l’URL live apparaît seulement quand `Live` est sélectionné dans les paramètres ; vide, elle retombe sur `https://nifff.ch/programme/`
- choisir `Live` affiche le champ URL, puis le CTA de récupération demande une confirmation explicite avant de récupérer les données depuis `nifff.ch`
- si `Live` ne charge pas, le catalogue courant est vidé et un message d’erreur live est affiché
- le frontend ne doit pas mélanger un cycle live avec des films mock, ni des films live avec des séances démo
- un fallback démo peut exister pour le mode `Démo`, mais pas comme fallback automatique du mode `Live`
- les choix utilisateur peuvent être réhydratés par-dessus le catalogue chargé, mais le catalogue lui-même reste mono-source

## Business Rules

### Film Priority

Libellés UI :

- `Immanquable`
- `Peut-être`
- `Non merci`
- état initial : `À traiter`

Mapping legacy :

- `must-see` / `high` -> `Immanquable`
- `medium` -> `Peut-être`
- `ignore` -> `Non merci`
- `low` -> `À traiter` transitoire

Frontend :

- le mapping legacy est centralisé dans `frontend/src/lib/priorities.ts`
- l’UI doit consommer ce helper au lieu de comparer directement `must-see` ou `low`

Règles :

- un film arrive sans décision préalable
- `À traiter` est un vrai état initial
- la priorité existe au niveau film uniquement
- le cycle ne porte jamais de priorité

### `Films` Rules

La structure principale est **par cycle**.

Le cycle est :

- une structure éditoriale
- un repère de lecture

Le cycle n’est pas :

- un objet de décision
- un override de priorité

Règles :

- liste plate de films dans chaque cycle
- pas de sous-sections lourdes par statut
- le statut reste visible via contrôle, compteurs, dots éventuelles

Payload éditorial obligatoire dans la carte film :

- titre
- année
- tagline
- réalisateur
- casting
- pays
- durée

Principe :

- priorité = à quel point je veux le voir
- métadonnées = pourquoi je veux le voir

Les deux sont nécessaires.

### `Planning` Rules

La vue principale doit montrer d’abord :

- temps
- collisions
- choix déjà faits
- conséquences d’un choix

Règles :

- une action dominante par contexte
- densité d’actions basse
- pas de surcharge de badges, icônes ou tags
- le panneau détail porte la complexité utile

Exception admise :

- une action directe `Ignorer` peut rester dans la timeline
- seulement si elle évite un détour inutile
- elle doit rester visuellement secondaire

### Scheduling Hint In `Films`

`pas de séance prévue` :

- uniquement pour `Immanquable`
- jamais pour `Peut-être` ou `Non merci`

## System Requirements

États obligatoires dans `Films` et `Planning` :

- `empty`
- `loading`
- `error`
- `transition feedback`

Le fallback démo ne doit pas masquer un vrai problème de chargement.

## Persistence

Le produit ne doit pas faire perdre le travail au refresh.

Persistance minimale requise :

- priorité des films
- sélection des séances

Implémentation légère acceptée :

- `localStorage`

Règle courante d’implémentation :

- au bootstrap, l’état local persistant est réappliqué
- dans l’état actuel du produit, il prime sur l’état distant si les deux diffèrent
- après une action utilisateur réussie côté backend, la réponse backend fraîche prime sur `localStorage`
- `localStorage` doit alors être réécrit depuis l’état fraîchement rechargé pour éviter de réappliquer une ancienne sélection

Important :

- ce comportement est toléré pour la phase actuelle et le mode démo
- il devra être revu dès que les vraies données seront disponibles de façon fiable

## Visual Hierarchy

### `Films`

- les signaux film dominent les signaux planning
- la priorité doit rester visible sans écraser le contenu
- `Non merci` peut être plus discret, mais doit rester lisible
- la carte ne doit pas simuler une grande zone cliquable

### `Planning`

- le temps et les conflits dominent
- la décision actuelle doit être immédiatement lisible
- l’accent sert l’intention, pas la décoration
- la timeline ne doit pas devenir un cockpit
