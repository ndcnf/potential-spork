# Frontend DRY Components Design

Date : 2026-06-26

## Goal

Reduire la complexite du frontend Planning en centralisant les decisions repetees a un seul endroit, sans lancer un design system complet.

L'objectif n'est pas de creer beaucoup de composants. L'objectif est de rendre les decisions DRY :

- une seule source pour les variants de boutons
- une seule source pour les statuts visuels de seance
- une seule source pour les actions disponibles selon l'etat d'une seance
- moins de duplication dans `PlanningView.vue`
- moins de classes locales dans `planning.css`

## Direction

La refactorisation doit avancer en deux couches.

### 1. Components UI simples

Ces composants restent betes et reutilisables. Ils savent rendre une forme, pas prendre une decision metier.

Composants concernes :

- `UiButton`
- `UiBadge` ou `UiPill`
- `UiChip`
- `UiPanel`

Regle :

- props simples et typees
- peu de variants
- pas de logique Planning dedans
- support des attributs natifs Vue via fallthrough attrs quand c'est utile

Pour `UiButton`, viser une API courte :

- `variant`: `primary`, `secondary`, `ghost`, `state`
- `size`: `sm`, `md`
- `type`: `button`, `submit`, `reset`
- `disabled` passe comme attribut natif

Eviter une API trop combinatoire comme :

- `variant + tone + size + active + block + compact + elevated`

Cette forme parait DRY, mais elle produit trop de combinaisons possibles et devient difficile a predire.

### 2. Components metier Planning

Ces composants savent quelle decision afficher pour le domaine Planning.

Composants prioritaires :

- `ScreeningActions`
- `ScreeningStatusPill`
- `RecommendationChips`

Composants plus tardifs :

- `PlanningTimelineItem`
- `PlanningDetailPanel`
- `PlanningControls`
- `PlanningSummary`

Regle :

- un composant metier peut utiliser les composants UI
- il expose une interface claire au parent
- il evite de faire remonter toutes les branches `v-if` dans `PlanningView.vue`

## First Implementation Slice

Le premier chantier doit etre `UiButton` + `ScreeningActions`.

### Why this slice

`PlanningView.vue` repete aujourd'hui les actions de seance dans plusieurs contextes :

- timeline
- seance active dans le panel detail
- alternatives du meme film dans le panel detail

Les libelles et conditions sont proches mais dupliques. C'est le meilleur endroit pour obtenir un vrai gain DRY sans changer le comportement produit.

### Target API

Exemple d'usage cible :

```vue
<ScreeningActions
  :screening="screening"
  @select="applyScreeningSelection(screening.id, $event)"
  @clear="removeScreeningSelection(screening.id)"
/>
```

`ScreeningActions` rend des `UiButton`.

Events proposes :

- `select(status)` pour `tentative`, `confirmed`, `rejected`
- `clear()` pour remettre la selection a `none`

### Central action mapping

La logique de decision doit etre centralisee dans une fonction pure.

Nom possible :

- `getScreeningActions`

Emplacement possible :

- `frontend/src/lib/screeningActions.ts`

Responsabilite :

- recevoir une seance annotee ou un petit objet d'etat
- retourner une liste d'actions affichables

Exemple conceptuel :

```ts
type ScreeningAction =
  | { kind: "select"; status: "confirmed" | "tentative" | "rejected"; label: string; variant: "primary" | "secondary" | "ghost" }
  | { kind: "clear"; label: string; variant: "ghost" }
  | { kind: "state"; label: string; variant: "state" }
```

La fonction doit couvrir les decisions existantes :

- `Confirmer cette seance`
- `Mettre une option`
- `Remplacer par cette seance`
- `Ignorer`
- `Ignore`
- `Annuler`
- `Retirer du planning`
- `Repasser en tentative`

## Visual Strategy

Garder les pills, car elles sont appreciees et utiles.

Simplifier le reste :

- utiliser `UiButton` pour les boutons d'action
- utiliser un seul composant pour les statuts de seance
- utiliser un seul composant pour les chips de recommendation
- reduire les variantes locales `planning__action--*`

Le CSS doit suivre cette regle :

- tokens globaux pour couleurs, rayons, espacements
- classes UI pour boutons/badges/chips/panels
- classes Planning seulement pour le layout specifique de Planning

Autrement dit :

- `ui-button--primary` est une decision systeme
- `planning__timeline-item` est une decision de layout Planning
- `planning__action--confirm` devrait disparaitre si `UiButton` couvre le cas

## Boundaries

Ce qu'il faut faire :

- centraliser les decisions repetees
- reduire `PlanningView.vue`
- reduire `planning.css`
- garder le comportement visible equivalent
- garder les labels francais existants au debut
- garder les pills

Ce qu'il ne faut pas faire dans cette premiere passe :

- refondre tout `PlanningView.vue`
- extraire tout le panel detail d'un coup
- toucher au store `festival.ts`
- changer le moteur de recommendation
- changer les regles de conflit
- ajouter une nouvelle dependance UI
- lancer un design system complet

## Testing Strategy

Ajouter des tests ciblant les decisions, pas chaque classe CSS.

Tests recommandes :

- `getScreeningActions` retourne les bons labels pour `none`, `tentative`, `confirmed`, `rejected`
- `getScreeningActions` retourne `Remplacer par cette seance` pour une alternative/disabled
- `ScreeningActions` emet `select("confirmed")` quand on clique sur confirmer
- `ScreeningActions` emet `clear()` quand on clique sur annuler ou retirer
- `UiButton` garde des classes previsibles pour chaque variant

Ne pas ajouter de snapshots massifs du markup Planning.

## Agent Handoff

Pour l'agent qui reprend ce chantier :

1. Commencer par lire :
   - `docs/product-simplification-review.md`
   - ce document
   - `frontend/src/views/PlanningView.vue`
   - `frontend/src/components/ui/UiButton.vue`
   - `frontend/src/components/ui/uiClasses.ts`
   - `frontend/src/styles/planning.css`
2. Ne pas demarrer par un grand decoupage de `PlanningView.vue`.
3. Faire une premiere passe etroite : `UiButton` + mapping d'actions + `ScreeningActions`.
4. Verifier que la passe supprime vraiment de la duplication dans les trois zones d'actions.
5. Supprimer les classes CSS locales remplacees seulement apres migration effective.
6. Ajouter les tests avant ou pendant le refactor, en visant les decisions visibles.
7. Ne pas modifier les fichiers sans accord explicite de l'utilisatrice.

Definition of done pour la premiere passe :

- les actions de seance sont rendues par `ScreeningActions` dans les trois contextes principaux
- les boutons passent par `UiButton`
- les labels et events sont testes
- `PlanningView.vue` est plus court
- `planning.css` perd des classes `planning__action--*` devenues inutiles
- aucun comportement Planning volontairement change

## Sources

- Vue component basics : https://vuejs.org/guide/essentials/component-basics.html
- Vue fallthrough attributes : https://vuejs.org/guide/components/attrs.html
- Review locale : `docs/product-simplification-review.md`
