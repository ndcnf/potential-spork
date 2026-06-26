# Product Simplification Review

Date : 2026-06-26

Scope : produit complet NIFFF Planner, pas seulement la branche courante.

Objectif : garder les decisions produit et les fonctionnalites utiles, mais reduire fortement le code et la charge mentale pour rendre le projet maintenable par une personne.

## Verdict Court

Le produit a une bonne direction : il est `film-first`, il separe `Films`, `Planning` et `Settings`, et il a des regles metier importantes deja clarifiees.

Le probleme principal n'est pas une feature precise. Le probleme est que plusieurs decisions valides sont implementees plusieurs fois, a plusieurs niveaux :

- dans les vues Vue
- dans les composables
- dans les stores
- dans les CSS specifiques
- dans les docs historiques

La refonte doit donc etre une simplification structurelle, pas un redesign visuel complet.

## Decisions A Preserver

Ces decisions sont bonnes et ne doivent pas etre perdues pendant la reduction de code.

### Produit

- `Films` sert a qualifier les films.
- `Planning` sert a arbitrer les seances.
- `Settings` reste secondaire.
- Le workflow reste libre : pas de tunnel et pas d'etapes numerotees.
- `Trous / Free Slots` reste hors scope tant que le produit principal n'est pas plus simple.

### Donnees

- `Demo` et `Live` sont deux sources completes, pas deux jeux de donnees melanges.
- En mode `Live`, pas de fallback automatique vers la demo.
- Le catalogue courant doit etre remplace comme un set complet : cycles, films, lieux, seances.
- `package_member` est conserve en donnee mais non planifie seul.
- `package` reste planifiable.

### Temps Festival

- Les vraies dates/heures restent les valeurs de reference pour les conflits et l'export iCal.
- Le `festival day` est une regle d'affichage.
- Les seances apres minuit peuvent etre groupees sur la journee festival precedente, sans modifier leur vraie date.

### Planning

- `Immanquable` passe avant `Peut-etre` dans les recommendations.
- Les criteres secondaires de recommendation peuvent etre ordonnes par l'utilisateur.
- `Confirme`, `Tentative`, `Ignore`, `Conflit` et `Recommendation` doivent rester distinguables.
- `Confirme` utilise le vert doux.
- `Recommendation` utilise le dore.
- `Ignore` affiche un etat `Ignore` et une action `Annuler`.

### UI

- Les informations absentes ne doivent pas afficher de placeholder visuel.
- Les separateurs de meta ne s'affichent que quand les deux morceaux existent.
- Le panneau de detail Planning doit rester accessible sans remonter en haut de page.
- La visualisation doit montrer le statut de chaque bloc sans ajouter du texte permanent partout.

## Diagnostic Global

### Frontend

Le frontend est le plus gros levier de simplification.

Fichiers les plus critiques :

- `frontend/src/composables/usePlanningModel.ts` : environ 1053 lignes
- `frontend/src/styles/planning.css` : environ 978 lignes
- `frontend/src/style.css` : environ 818 lignes
- `frontend/src/views/PlanningView.vue` : environ 559 lignes apres la premiere extraction `ScreeningActions`
- `frontend/src/stores/festival.ts` : environ 520 lignes
- `frontend/src/views/FilmsView.vue` : environ 443 lignes
- `frontend/src/views/SettingsView.vue` : environ 424 lignes

Probleme principal :

- `Planning` porte trop de responsabilites au meme endroit.
- Les actions de seance existent dans plusieurs contextes avec des variations proches.
- Les statuts visuels sont exprimes a la fois en logique Vue, en classes BEM locales et en nouveaux composants UI.
- Le store `festival` gere a la fois catalogue, source de donnees, import, persistance locale et choix utilisateur.

Conclusion :

Le frontend doit etre reduit par extraction de composants metier reutilisables, puis suppression des classes et branches devenues redondantes.

### Backend

Le backend est plus petit et plus sain que le frontend.

Points positifs :

- les routes sont fines
- les repositories sont relativement courts
- l'import est deja separe entre source, normalisation, bundle, pipeline et postprocessing
- les tests backend couvrent beaucoup de regles critiques

Risques :

- le nombre de couches d'import peut devenir trop eleve si certaines couches deviennent de simples pass-through
- les warnings d'import sont encore tres textuels
- la strategie `full_replace` vs `merge` doit rester explicite
- la separation `real datetime` / `festival day` ne doit jamais etre simplifiee en une seule date

Conclusion :

Le backend ne doit pas etre refondu largement maintenant. Il faut seulement consolider les contrats de source et garder les couches qui portent une vraie responsabilite.

### UX

La direction UX est bonne, mais l'interface donne parfois trop de signaux simultanes.

Risques :

- trop de badges
- trop de variantes de boutons
- trop de nuances proches entre etat utilisateur et recommendation systeme
- trop de details visibles dans `Planning` alors que la decision principale est simple : confirmer, mettre une option, ignorer, annuler

Conclusion :

La simplification UX doit reduire les choix visibles, pas seulement deplacer le CSS.

### Documentation

La documentation contient beaucoup de bonnes decisions, mais elle grossit trop.

Problemes :

- `docs/backend-import-architecture.md` est une archive longue et utile, mais difficile a lire vite
- `docs/next-steps.md` melange priorites, notes, idees, dette, plan de refactor et rappels historiques
- les plans `superpowers` sont utiles comme trace, mais ne doivent pas devenir la source active

Conclusion :

Il faut separer :

- docs actives courtes : decisions et prochaines actions
- archives : raisonnement historique, plans detailles, explorations

## Findings Priorises

### P1 - Le produit a besoin d'une reduction reelle, pas seulement d'une base UI

La branche ajoute des composants UI generiques (`UiButton`, `UiBadge`, `UiChip`, `UiPanel`) et des styles globaux.

La premiere extraction utile a maintenant ete faite : `ScreeningActions` consomme `UiButton` et remplace les actions de seance repetees dans `Planning`.

Risque :

- si les migrations suivantes s'arretent ici, on garde deux manieres de construire badges, chips et panels
- une junior dev doit comprendre l'ancien systeme et le nouveau systeme
- le nombre de lignes baisse dans `PlanningView.vue`, mais la dette restante est encore dans les pills, chips et panels locaux

Decision recommandee :

- continuer uniquement les extractions qui suppriment du code dans `PlanningView.vue` ou `planning.css`
- prochaine cible recommandee : `ScreeningStatusPill` et `RecommendationChips`

### P1 - `Planning` doit etre le premier chantier de reduction

`Planning` concentre la plupart des decisions complexes :

- selection utilisateur
- conflit
- recommendation
- visualisation
- alternatives
- panel detail
- actions directes

Le premier composant metier extrait est `ScreeningActions`.

Responsabilite proposee :

- afficher l'action dominante d'une seance
- afficher les actions secondaires autorisees
- gerer les libelles `Confirmer`, `Mettre une option`, `Ignore`, `Ignorer`, `Annuler`, `Retirer du planning`
- rester reutilisable dans timeline, panel actif et alternatives

Pourquoi c'est prioritaire :

- c'est une duplication visible
- c'est un endroit ou les regressions UX arrivent vite
- cela reduit a la fois Vue et CSS

### P1 - Le moteur de recommendation doit sortir de Vue

`usePlanningModel.ts` contient de la logique reactive Vue et de la logique metier.

Ce qui devrait rester dans le composable :

- `computed`
- etat actif de la vue
- selection du jour
- interaction avec les stores

Ce qui devrait sortir :

- scoring des recommendations
- tri par criteres
- detection des reasons/drawbacks
- choix de la meilleure option par film

Module cible :

- `frontend/src/lib/recommendationEngine.ts`

Forme ideale :

- input : films, screenings, selections, settings
- output : screenings annotees avec score, rang, reasons, drawbacks

Benefice :

- testable sans Vue
- plus facile a expliquer
- moins de risque de casser la reactivity pendant un refactor

### P1 - Le store `festival` porte trop de responsabilites

`festival.ts` gere :

- catalogue
- source demo/live
- import
- erreurs
- persistance locale
- priorites film
- selections de seances
- recomputation des etats derives

Extraction recommandee :

- `persistedFestivalState.ts` pour `localStorage`
- `catalogSource.ts` pour demo/live/import/reload
- garder le store comme orchestrateur d'etat Pinia

Attention :

Il ne faut pas extraire juste pour multiplier les fichiers. On extrait seulement si le store devient plus court et plus lisible.

### P2 - La CSS doit arreter de modeliser chaque micro-etat

Les styles Planning sont longs parce qu'ils portent beaucoup d'etats visuels.

Regle recommandee :

- un composant metier decide l'etat
- une classe systeme rend l'etat
- on evite une nouvelle classe pour chaque cas local

Exemples de classes a migrer progressivement :

- `planning__action`
- `planning__decision-badge`
- `planning__recommendation-chip`
- `ghost-button`
- variantes locales de panels et chips

Chaque migration doit supprimer des lignes de CSS.

### P2 - La base UI doit avoir une API moins combinatoire

L'API actuelle de `UiButton` combine `variant`, `tone`, `size`, `active`, `block`.

Risque :

- trop de combinaisons possibles
- certaines combinaisons se contredisent visuellement
- la CSS devient difficile a predire

Approche plus simple :

- partir d'intentions produit
- exemples : `primary`, `secondary`, `confirm`, `tentative`, `danger`, `ghost`
- ne pas permettre des combinaisons qui n'ont pas de sens

Reference Vue :

- avec `<script setup>`, garder des props typees simples
- utiliser les fallthrough attrs avec prudence
- reserver `aria-pressed` aux vrais boutons toggle

### P2 - Le theme `bujo` et les fonts doivent etre decides

La branche contient un theme et des fonts, mais ce n'est pas encore une simplification produit.

Options :

1. Retirer le theme et les fonts de cette PR.
2. Les garder seulement si un ecran les utilise vraiment et si la decision visuelle est assumee.
3. Les deplacer dans une branche separee `visual-theme`.

Recommendation :

- retirer ou reporter tant que le chantier principal est la maintenabilite

### P2 - La doc active doit etre plus courte

La doc active doit aider a travailler vite.

Structure recommandee :

- `docs/source-of-truth.md` : decisions produit stables
- `docs/current-ui-state.md` : etat courant verifie
- `docs/next-steps.md` : 5 a 10 prochaines actions maximum
- `docs/product-simplification-review.md` : review detaillee de refonte
- `docs/backend-import-architecture.md` : archive technique backend
- `docs/superpowers/*` : plans historiques

Regle :

Quand une decision est acceptee, elle va dans `source-of-truth.md`.
Quand une action est prochaine, elle va dans `next-steps.md`.
Quand une analyse est longue, elle reste dans une review/archive.

### P3 - Les tests frontend doivent monter d'un cran, mais sans tout figer

Les tests frontend actuels protegent deja certaines fonctions pures.

Il manque surtout :

- tests du futur `recommendationEngine`
- tests des actions de seance via un composant metier
- tests des transitions `Live` / `Demo`
- tests de non-regression pour les infos absentes dans les metas

Il ne faut pas tester chaque detail CSS.

Ce qu'il faut tester :

- la decision visible
- le libelle
- l'action emise
- les cas metier critiques

## Plan De Reduction Global

### Phase 1 - Stabiliser La PR De Review

But : documenter clairement la strategie avant d'ecrire une grosse refonte.

Actions :

- garder cette review comme document de reference
- ne pas ajouter de nouvelle feature
- corriger ou documenter les problemes de branche avant PR
- decider quoi faire du theme `bujo` et des fonts

Definition of done :

- la PR explique ce qui doit etre preserve
- la PR explique ce qui doit etre simplifie
- la PR ne pretend pas avoir deja reduit le code si ce n'est pas le cas

### Phase 2 - Continuer Le Gain Frontend

But : continuer a reduire `Planning` sans changer le comportement.

Actions :

- poursuivre apres `ScreeningActions` avec `ScreeningStatusPill`
- creer `RecommendationChips`
- supprimer les classes CSS remplacees apres migration effective
- ajouter des tests ciblant les labels, tones et actions visibles

Definition of done :

- moins de lignes dans `PlanningView.vue`
- moins de lignes dans `planning.css`
- comportement visuel equivalent ou plus lisible

### Phase 3 - Sortir Le Recommendation Engine

But : separer metier et Vue.

Actions :

- creer `recommendationEngine`
- deplacer scoring, tri, reasons/drawbacks
- ajouter tests purs
- garder `usePlanningModel` comme orchestrateur

Definition of done :

- recommandations testables sans composant Vue
- `usePlanningModel.ts` baisse nettement en taille
- les regles `Immanquable > Peut-etre` et criteres secondaires restent couvertes

### Phase 4 - Simplifier Le Store

But : clarifier source de donnees et persistance.

Actions :

- extraire lecture/ecriture `localStorage`
- extraire chargement demo/live/import
- garder Pinia pour l'etat courant

Definition of done :

- `festival.ts` devient plus court
- les regles demo/live restent explicites
- pas de fallback live vers demo

### Phase 5 - Nettoyer La Documentation Active

But : rendre les prochaines sessions plus faciles.

Actions :

- reduire `next-steps.md`
- deplacer les notes longues en archive
- garder `source-of-truth.md` prescriptif

Definition of done :

- une nouvelle session peut comprendre le produit en moins de 10 minutes

## Ce Qu'il Ne Faut Pas Faire

- Ne pas refaire tout le design system avant d'avoir supprime de la duplication.
- Ne pas fusionner `real datetime` et `festival day`.
- Ne pas melanger demo et live pour "rendre l'UI moins vide".
- Ne pas ajouter une vue ou un mode tant que `Planning` reste trop gros.
- Ne pas transformer les docs actives en journal de bord.
- Ne pas ajouter une dependance de test frontend juste pour tester des styles.

## PR Review De La Branche Courante

La branche `post-2026-simplification` est utile comme point de depart, mais elle doit etre presentee honnetement :

- elle ajoute une base UI
- elle commence a la consommer dans `Planning` via `ScreeningActions`
- elle reduit maintenant une duplication concrete, mais ne simplifie pas encore tout le frontend
- elle ajoute aussi un theme et des fonts qui semblent hors scope maintenabilite

Points a traiter avant merge ou dans une decision explicite :

- confirmer si `bujo-theme.css` et les fonts restent dans cette PR
- les fichiers de licence des fonts ont ete normalises en `LF`; le point restant est uniquement produit : garder ces assets futurs ou les deplacer dans une branche theme dediee
- clarifier l'API `UiButton`
- choisir le premier composant metier a migrer
- eviter que `next-steps.md` devienne la spec detaillee permanente

## Sources Locales

- `docs/source-of-truth.md`
- `docs/current-ui-state.md`
- `docs/next-steps.md`
- `frontend/src/views/PlanningView.vue`
- `frontend/src/composables/usePlanningModel.ts`
- `frontend/src/stores/festival.ts`
- `frontend/src/styles/planning.css`
- `frontend/src/style.css`
- `backend/app/services/import_pipeline.py`
- `backend/app/services/import_bundle.py`
- `backend/app/sources/nifff_html/parser.py`

## Sources Techniques

- Vue `<script setup>` : https://vuejs.org/api/sfc-script-setup.html
- Vue fallthrough attributes : https://vuejs.org/guide/components/attrs.html
- Vue component events : https://vuejs.org/guide/components/events.html
