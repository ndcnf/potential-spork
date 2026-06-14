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
- fallback démo appliqué comme bundle cohérent, pas comme mélange partiel films réels / séances démo
- source `Démo` chargée comme environnement de validation cohérent tant que les vraies données ne sont pas disponibles
- source `Live` réservée à l’intégration backend réelle, avec signal explicite si les séances ne sont pas encore chargées
- titre de marque `PLANIFFFICATEUR`
- `Paramètres` renvoyé en navigation secondaire avec icône
- export iCal retiré du header global
- fond plus noir avec shell partagé `content-frame`
- statut de source de données visible dans le footer global
- mention Solar dans le footer global
- persistance locale au refresh pour :
  - priorités film
  - sélections de séances

### `Films`

- header avec progression visible
- compteurs cliquables comme filtres légers
- compteurs cumulables
- compteurs calculés sur l’ensemble des films, pas sur la vue filtrée
- compteur `Non merci` présent
- structure par cycle conservée
- liste plate de films par cycle
- pas de réorganisation des cartes lors d’un choix
- cartes film en grille :
  - colonne gauche = titre + contenu éditorial
  - colonne droite = contrôle de qualification
  - hint séance en bas
- `Immanquable` ressort par bordure / fond léger
- `Non merci` est plus discret dans la liste
- `PrioritySelect` visible en haut de carte
- warning `pas de séance prévue` réservé à `Immanquable`
- recherche / tri / masquage dédiés retirés de la vue

### `Planning`

- timeline plus compacte
- légende raccourcie
- méta séance regroupée sur une seule ligne
- note de conséquence visible seulement dans les cas utiles
- action directe `Ignorer` disponible dans la timeline
- panneau détail non sticky
- centrage horizontal aligné sur les autres pages
- recommandations visibles surtout dans le panneau détail, pas dans la timeline elle-même
- distinction explicite entre `Conflit` et `Conflit potentiel`
- recommandations protégées contre :
  - conflits avec des séances déjà retenues
  - conflits entre recommandations concurrentes
- logique horaire des recommandations alignée sur la journée festival
- `must-lock` limité à la vraie dernière séance viable
- panneau détail conserve :
  - poster
  - cycle
  - tagline
  - réalisation
  - casting
  - infos séance
  - comparatif `Pour cette séance` / `Pour pas cette séance`
- suppression des pastilles dans les pills d’état
- suppression des compteurs redondants dans les headers de groupes timeline/visualisation

### `Settings`

- vue secondaire
- centrée sur les recommandations du planning
- persistance locale déjà en place
- bascule explicite `Démo (archive)` / `Live (prod)`
- possibilité de relancer un import propre depuis la source active
- possibilité de reset les choix utilisateur pour repartir d’un état propre
- résumé visible des signaux qui font remonter une séance
- préférences salles réduites à 3 états simples

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
- le wording des recommandations et des conflits potentiels doit encore être surveillé sur cas réels
- les états `error` réels vs mode démo doivent rester surveillés dans les prochaines passes
