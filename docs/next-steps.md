# Next Steps

## Current Priorities

Review globale de simplification : `docs/product-simplification-review.md`.

Ordre recommandé :

1. réduire fortement la complexité globale du projet
2. continuer à simplifier la lecture de `Planning`
3. finaliser les états système réels si un cas faible réapparaît
4. réduire la dette legacy autour des priorités
5. garder `Trous / Free Slots` hors scope tant qu’un vrai chantier dédié n’est pas lancé

## Simplification Mandate

Le projet a dépassé une taille qui n’est plus proportionnée à son usage actuel.
L’ordre de grandeur est d’environ 18k lignes selon le comptage local complet ; même en excluant les artefacts générés, les sources applicatives et docs restent trop volumineuses pour une app personnelle de planning festival.

Objectif : réduire le code et la surface mentale avant d’ajouter de nouvelles features.

Principes :

- chaque nouvelle passe doit chercher à supprimer ou fusionner du code avant d’en ajouter
- une abstraction ne doit rester que si elle réduit vraiment la complexité d’usage ou de maintenance
- les comportements produit utiles priment sur la généricité future
- les docs doivent rester courtes et prescriptives ; `backend-import-architecture.md` peut être long comme archive technique, mais `source-of-truth.md` et `next-steps.md` doivent rester lisibles rapidement
- ne pas garder une option UI parce qu’elle existe déjà si elle n’aide pas une décision réelle
- préférer un chemin utilisateur clair à plusieurs modes équivalents
- les tests doivent protéger les règles risquées, pas figer chaque détail d’implémentation

### Simplification Targets

#### Frontend

- base UI déjà créée :
  - `UiButton`
  - `UiBadge`
  - `UiChip`
  - `UiPanel`
  - helpers BEM `uiClasses.ts`
- première migration faite dans `Planning` :
  - `ScreeningActions`
  - `getScreeningActions`
  - `ScreeningStatusPill`
  - `getScreeningStatusPresentation`
  - boutons de séance rendus par `UiButton`
- prochaine règle : continuer les migrations par petites passes, sans changer le comportement visible
- simplification UI à étudier avant d'ajouter de nouveaux variants :
  - transformer `UiButton` en primitive très fine
  - passer les classes BEM depuis les composants métier ou les vues
  - s'appuyer sur les `fallthrough attributes` Vue pour éviter une API de variants trop large
- extraire ou supprimer la logique excessive de `usePlanningModel.ts`
  - garder le composable comme orchestrateur Vue
  - déplacer le ranking dans un petit `recommendationEngine`
  - déplacer le grouping / layout visualisation seulement si cela rend le fichier plus court et testable
- réduire la densité de `PlanningView.vue`
  - éviter que summary, légende, filtres, modes, timeline et panel aient tous le même poids visuel
  - garder visibles seulement les contrôles nécessaires à la prochaine décision
- réduire les styles spécifiques dans `planning.css`
  - identifier les boutons, chips, badges, panels et rows réutilisables
  - ne pas créer de nouveau variant CSS pour chaque micro-état si un token existant suffit
- vérifier si la vue `Visualisation` apporte assez de valeur pour justifier sa complexité
  - si oui, la garder compacte et utile
  - si non, la retirer ou la cacher derrière un état expérimental

#### Backend

- rendre explicite la stratégie d’import `full_replace` vs `merge`
  - aujourd’hui, une partie de cette règle est implicite dans le traitement `nifff_html`
  - le contrat devrait être visible côté source ou bundle canonique
- réduire le nombre de couches si elles ne portent pas encore une responsabilité réelle
  - `import_catalog`, `import_bundle`, `import_pipeline`, `import_nifff`, `import_postprocessing` ont du sens, mais doivent rester fins
  - si une couche devient seulement un pass-through, la fusionner
- typer les warnings d’import au lieu d’accumuler des strings longues
  - but : résumé UI plus court et moins de bruit
- conserver strictement la séparation `real datetime` / `festival day`
  - cette règle est métier, pas une optimisation technique

#### Product / UX

- réduire le nombre d’états visibles simultanément
  - confirmation, tentative, recommandation, conflit, conflit potentiel, ignoré et must-lock doivent être distinguables, mais pas tous dominants
- clarifier les recommandations avec une explication courte et comparable
  - `priorité film`
  - `nombre d’options`
  - `conflit`
  - `préférence salle/horaire`
- corriger les messages d’erreur live/demo
  - éviter un titre `Mode démo` quand l’utilisateur vient de demander `Live`
- repousser les idées non essentielles
  - `Trous / Free Slots`
  - préférences avancées de lieux
  - fetch live des pages détail
  - nouvelle iconographie complète

### Success Criteria

Une passe de simplification est réussie si :

- elle supprime du code ou réduit un fichier critique sans perdre une règle métier validée
- elle rend un comportement plus facile à expliquer en une phrase
- elle garde les tests de non-régression importants verts
- elle évite d’ajouter une nouvelle option utilisateur sans usage clair
- elle documente seulement les décisions qui changent réellement le produit

### High-Impact Simplifications

Observations de review :

- les plus gros fichiers applicatifs sont `usePlanningModel.ts`, `planning.css`, `PlanningView.vue`, `festival.ts`, `FilmsView.vue` et `SettingsView.vue`
- les gains les plus sûrs sont côté Planning, car une même décision de séance est actuellement représentée dans plusieurs zones UI
- l’objectif n’est pas seulement de déplacer du code dans plus de fichiers, mais de réduire les duplications et les divergences possibles

Ordre recommandé :

1. créer `RecommendationChips`
   - regrouper reasons, drawbacks et blockedBy
   - remplacer les blocs répétés du panneau détail et des alternatives
   - bénéfice : réduire la duplication sans toucher au moteur de recommandation
2. extraire un petit `recommendationEngine`
   - sortir le scoring et l’ordre des recommandations de `usePlanningModel.ts`
   - garder une API pure et testable : films, screenings, settings en entrée ; recommandations annotées en sortie
   - bénéfice : rendre les recommandations explicables et testables sans Vue
3. découper `PlanningView.vue`
   - extraire `PlanningSummary`, `PlanningControls`, `PlanningTimeline`, `PlanningVisualization`, `PlanningDetailPanel`
   - garder la page comme composition de blocs, pas comme fichier qui contient tout le produit Planning
   - bénéfice : réduire la taille du fichier sans changer le comportement
4. réduire `planning.css`
   - garder `UiButton`, `UiBadge`, `UiChip`, `UiPanel` comme primitives fines
   - porter les intentions visuelles Planning par des classes BEM Planning explicites
   - éviter un nouveau variant CSS pour chaque micro-état Planning
   - bénéfice : réduire les styles spécifiques et rendre les futurs polish moins coûteux
5. simplifier la vue `Visualisation`
   - conserver le clic vers le panel et l’information compacte
   - questionner la nécessité d’une grille horaire précise à 15 minutes
   - bénéfice : garder la feature “vue visuelle” sans porter toute la complexité d’un scheduler complet
6. alléger `festival.ts`
   - extraire la persistance locale dans `persistedChoices`
   - extraire la logique demo/live/import dans un module dédié
   - bénéfice : garder le store Pinia centré sur l’état courant plutôt que sur toutes les responsabilités annexes
7. réduire les docs actives
   - garder `source-of-truth.md` et `next-steps.md` courts et prescriptifs
   - transformer les longues notes historiques en archive
   - bénéfice : retrouver rapidement les décisions actuelles

## Concrete Remaining Work

### `Films`

- clarifier la zone séance du header
- continuer le polish de la carte sans recharger l’interface
- surveiller si la nouvelle zone compteurs suffit vraiment sans recherche / tri / masquage dédiés
- éventuellement renommer plus tard `PrioritySelect` vers un nom plus produit

### `Planning`

- continuer à calmer les états visuels si certains restent trop proches ou trop forts
- surveiller la densité réelle des actions dans la timeline
- garder la méta principale courte
- continuer à fiabiliser le moteur de recommandations dès qu’un nouveau cas de collision ou de fenêtre horaire réapparaît

### Data / Tech

- continuer la séparation backend par petites passes :
  - `import_catalog` doit rester responsable du fetch + normalisation vers `CanonicalImportBundle`
  - `import_bundle` applique maintenant le bundle canonique en DB via les repositories
  - `import_pipeline` orchestre le flow générique, le `commit`, le log final et le résumé API
  - `import_postprocessing` isole la correction legacy `package_member`
  - `import_nifff` reste un wrapper spécifique NIFFF pour le choix de source et les postprocessors nécessaires
  - la route d’import API reste une façade fine qui transmet `source_mode` au service
  - les données déduites doivent remonter comme warnings, les données vraiment absentes restent `None`
  - les fins de séance non déductibles doivent aussi remonter comme warnings pour préparer le contrôle des vraies données
  - garder la séparation `real datetime` / `festival day` : iCal et conflits utilisent les vraies dates, l’affichage planning utilise le jour festival
  - garder les tests de non-régression sur les séances après minuit et sur le nettoyage des anciennes séances quand une date corrigée change le `source_key`
  - garder la séparation stricte `demo=2025 Wayback` / `prod=2026 live`, sans fallback automatique du live vers la démo
  - ne réactiver le fetch des pages détail live que si un besoin concret apparaît et avec timeouts / concurrence contrôlée
  - garder le mapping frontend des priorités legacy dans `frontend/src/lib/priorities.ts`
  - garder les règles backend de priorité dans `backend/app/core/priorities.py`
- réduire ensuite la dette `must-see` / `low` côté contrat/API public, pas en dupliquant des règles internes
- définir plus tard une stratégie si synchronisation serveur des choix devient nécessaire
- revoir la règle actuelle de persistance locale > état distant dès que les vraies données seront accessibles de manière fiable

## Open Ideas — Not Validated

Ces pistes sont compatibles ou à explorer, mais **pas verrouillées**.

### Toutes les pages

- Continuer a verifier si le shell global reste assez sobre apres le passage fond noir + `content-frame`
- Revoir plus tard si l'icone `Parametres` doit etre encore plus legere ou mieux integree au ton general

### `Films`

- `Non merci` encore plus discret : bordure seule, fond absent
- retravailler encore le dégradé / surlignage des cycles si inutile
- faire vivre progression, sauvegarde locale et navigation légère dans une même région si utile
- moins de layout shift quand il y a une seance ou non. Prevoir la place ou l'integrer d'une meilleure maniere. Et ne pas mettre cette information dans une bordure, ca alourdit trop.
- Faire attention a l'equilibre des elements en couleur. Ça peut encore etre plus sobre pour une meilleure lisibilite.
- Le fond entre un film non choisi et un film "peut-etre" est encore trop similaire. Ne pas avoir de fond quand le film n'est pas choisi.
- Se baser sur les couleurs pastilles (border et background) pour les boutons de choix
- Pour le boutons Replier, le plus utile serait un "Non merci" pour tout le cycle, mais a voir comment le formuler. Pas besoin de replier ensuite, juste passer l'etat de tous les films du cycle en "Non merci". Faire attention a la coherence si on passe avec des icones.
- Fix le contraste des boutons dans le header. Cela doit se faire avec des boutons normalise comme des composants systeme
- Verifier dans l'usage si les compteurs cumulables suffisent vraiment comme seul point d'entree de filtrage

Idealement ajouter les icones svg ajoutees a la racine depuis ici: https://icon-sets.iconify.design/solar/.
Bien discuter UX et frontend afin que ces icones permettent d'alleger visuellement, mais pas perdre le sens. Les mentions doivent au moins se faire au hover. Mais les coeurs me semblent quand meme assez comprehensibles sur les intentions. Un statut sur la carte, juste avant la seance pourrait afficher l'etat "A traiter", "Non merci", etc. pour expliciter l'icone.

### `Planning`

- continuer à simplifier les états si certaines nuances restent difficiles à lire
- réévaluer plus tard si l’action directe `Ignorer` doit changer de libellé ou de poids visuel
- continuer à tester la frontière entre `Conflit`, `Conflit potentiel`, `Recommandée` et `À sécuriser`
- continuer à surveiller les faux positifs de recommandations croisées entre films

### `Parametres`

- Continuer à ajuster le wording et les controles de confort salle si les "pastilles" restent trop verbeuses
- Les horaires a mettre a la ligne

## Rules For Next Sessions

- faire des passes courtes
- rebuild après chaque passe significative
- préférer simplification + validation à une refonte large
- mettre la doc à jour seulement si un choix réel change

## Notes en vrac
- Ajouter le panel dans la vue Films. Trigger depuis le titre du film

## Validation Command

```bash
cd frontend
npm run build
```

Pour les passes backend :

```bash
cd backend
.venv/bin/python -B -m pytest -q
```
