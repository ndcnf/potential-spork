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
- mode démo explicite quand l’utilisateur choisit `Démo`
- mode live strict quand l’utilisateur choisit `Live` : si le live ne charge pas, l’UI affiche une erreur au lieu de retomber sur la démo
- confirmation explicite avant de récupérer les données live depuis `nifff.ch`
- URL source live configurable dans `Paramètres` seulement quand `Live` est sélectionné, avec placeholder `https://nifff.ch/programme/` et CTA de récupération au bout du champ
- `Live` importe l’édition courante 2026 ; `Démo` reste liée au programme 2025 Wayback
- les erreurs Live conservent le détail renvoyé par le backend quand il existe, au lieu d’afficher seulement un message générique
- fallback démo appliqué comme bundle cohérent uniquement dans le mode `Démo`, pas comme mélange partiel films réels / séances démo
- la bascule de source remplace le catalogue courant comme un set complet : cycles, films et séances viennent de la même source chargée
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
- les `package_member` ne sont pas affichés comme films à qualifier individuellement
- les `package` restent visibles comme choix planifiables
- pas de réorganisation des cartes lors d’un choix
- cartes film en grille :
  - colonne gauche = titre + contenu éditorial
  - colonne droite = contrôle de qualification
  - hint séance en bas
- `Immanquable` ressort par bordure / fond léger
- `Non merci` est plus discret dans la liste
- `PrioritySelect` visible en haut de carte
- warning `pas de séance prévue` réservé à `Immanquable`
- l'année, le pays et la durée ne sont affichés que si l'information existe
- quand une carte n'a qu'une ligne meta, par exemple une durée seule, cette ligne reste visible mais est attachée visuellement au titre pour éviter un espace vide
- les séparateurs de meta ne sont affichés que quand les deux morceaux existent
- recherche / tri / masquage dédiés retirés de la vue

### `Planning`

- timeline plus compacte
- légende raccourcie
- méta séance regroupée sur une seule ligne
- les infos film manquantes ne sont pas remplacées par des placeholders `?`
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
- les séances après minuit restent groupées sur la journée festival précédente, tout en conservant leur vraie date/heure pour les conflits et l’export iCal
- en DB, ces séances après minuit doivent donc être stockées avec la vraie date du lendemain ; le regroupement sur la veille est uniquement une règle d’affichage `festival day`
- `must-lock` limité à la vraie dernière séance viable
- panneau détail orienté décision :
  - film compact en contexte
  - séance active lisible en premier
  - alternatives comparables par rows
  - statut utilisateur dominant
  - recommendations en chips secondaires
- `Confirmée` utilise un vert doux, `Recommendation` utilise le doré, et `Tentative` / `Conflit` gardent des nuances et formes distinctes
- l’ordre des critères secondaires de recommendation est réglable dans `Paramètres`, après la priorité fixe `Immanquable` avant `Peut-être`
- la vue visualisation garde des blocs compacts, mais expose le statut de chaque séance par couleur/forme et marqueur interne
- les blocs de visualisation sont des boutons accessibles : le hover/focus affiche film, horaire, lieu si présent, et statut sans agrandir la grille
- chantier à reprendre : venues/lieux comme données explicites, puis paramètres de préférences de lieux
- suppression des pastilles dans les pills d’état
- suppression des compteurs redondants dans les headers de groupes timeline/visualisation

### `Settings`

- vue secondaire
- centrée sur les recommandations du planning
- persistance locale déjà en place
- bascule explicite `Démo (archive)` / `Live (prod)`
- `Démo (archive)` lit la DB déjà alimentée depuis Wayback, sans réimport automatique
- `Live (prod)` appelle l’import backend avec l’année 2026 et l’URL live choisie, puis recharge uniquement le catalogue live
- possibilité de relancer explicitement un import propre depuis la source active
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
- `frontend/src/lib/priorities.ts`

## Known Debts

### Product / Data

- `Priority` porte encore des valeurs legacy dans `frontend/src/types.ts`
- `must-see` et `low` existent encore pour compatibilité
- le mapping legacy est centralisé dans `frontend/src/lib/priorities.ts`
- il faut éviter de réintroduire des comparaisons directes à `must-see` ou `low` hors de ce helper

### UX

- la zone séance du header `Films` peut encore être clarifiée
- la hiérarchie visuelle de `Planning` peut encore être simplifiée
- le wording des recommandations et des conflits potentiels doit encore être surveillé sur cas réels
- les états `error` réels vs mode démo doivent rester surveillés dans les prochaines passes
