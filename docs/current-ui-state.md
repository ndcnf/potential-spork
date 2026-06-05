# Current UI State

## Product Snapshot

Le frontend courant assume :

- dark theme
- design minimal `background / foreground / accent`
- produit `film-first`
- parcours lisible mais non rigide entre `Films` et `Planning`

## Implemented Now

### Global

- navigation sans étapes numérotées
- ton UI homogène au `tu`
- mode démo explicite si les données réelles ne chargent pas
- persistance locale au refresh pour :
  - priorités film
  - sélections de séances

### `Films`

- header avec progression visible
- compteurs cliquables comme filtres légers
- compteur `Non merci` présent
- structure par cycle conservée
- liste plate de films par cycle
- cartes film en grille :
  - colonne gauche = titre + contenu éditorial
  - colonne droite = contrôle de qualification
  - hint séance en bas
- `Immanquable` ressort par bordure / fond léger
- `Non merci` est plus discret dans la liste
- `PrioritySelect` visible en haut de carte
- warning `pas de séance prévue` réservé à `Immanquable`

### `Planning`

- timeline plus compacte
- légende raccourcie
- méta séance regroupée sur une seule ligne
- note de conséquence visible seulement dans les cas utiles
- action directe `Ignorer` disponible dans la timeline
- panneau détail non sticky
- panneau détail conserve :
  - poster
  - cycle
  - tagline
  - réalisation
  - casting
  - infos séance
- suppression des pastilles dans les pills d’état
- suppression des compteurs redondants dans les headers de groupes timeline/visualisation

### `Settings`

- vue secondaire
- centrée sur les recommandations du planning
- persistance locale déjà en place

## Files To Know

Frontend principal :

- `frontend/src/views/FilmsView.vue`
- `frontend/src/views/PlanningView.vue`
- `frontend/src/views/SettingsView.vue`
- `frontend/src/stores/festival.ts`
- `frontend/src/stores/settings.ts`

Styles :

- `frontend/src/styles/films.css`
- `frontend/src/styles/planning.css`
- `frontend/src/style.css`
- `frontend/src/styles/tokens.css`

Composants :

- `frontend/src/components/ui/PrioritySelect.vue`
- `frontend/src/components/ui/PriorityBadge.vue`

## Known Debts

### Product / Data

- `Priority` porte encore des valeurs legacy dans `frontend/src/types.ts`
- `must-see` et `low` existent encore pour compatibilité
- il faut surveiller les endroits où l’ancienne logique 5 niveaux peut réapparaître dans l’UI

### UX

- la zone séance du header `Films` peut encore être clarifiée
- la hiérarchie visuelle de `Planning` peut encore être simplifiée
- les états `error` réels vs mode démo doivent rester surveillés dans les prochaines passes
