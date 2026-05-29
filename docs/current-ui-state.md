# Current UI State — NIFFF Planner

Ce fichier sert de mémo d’exécution.  
Il complète `docs/ux-roadmap.md`, qui porte surtout la vision produit et la roadmap UX.

Objectif : permettre de reprendre le travail dans une nouvelle session sans refaire tout le contexte.

---

## 1. État actuel du produit

Le frontend est organisé autour de 4 vues principales :
- `Films`
- `Planning`
- `Trous / Créneaux libres`
- `Settings`

Le produit est désormais orienté :
- **film-first**
- **dark theme**
- **système visuel minimal**
- **workflow guidé en cours de clarification**

La base actuelle est bien plus cohérente qu’au début, mais le produit reste encore partiellement perçu comme un ensemble d’outils experts plutôt qu’un parcours guidé.

---

## 2. Décisions UI / design system déjà prises

### Thème
- thème sombre rétabli
- pas de retour à un thème clair “par défaut” tant que la base UX n’est pas stabilisée

### Couleurs
Système volontairement réduit à :
- `--color-background`
- `--color-foreground`
- `--color-accent`

Les états passent majoritairement par :
- accent
- foreground atténué
- opacité
- bordure

Conséquence :
- `confirmed`, `must-lock`, `recommended`, `conflict` utilisent surtout la famille accent
- `tentative`, `available`, `disabled`, `rejected` utilisent surtout la famille neutre

### Priorités film
La logique UI a été simplifiée à 3 niveaux :
- `Prioritaire`
- `Moyen`
- `Ignorer`

Compatibilité temporaire conservée avec les anciennes valeurs de données :
- `must-see` + `high` -> `Prioritaire`
- `medium` -> `Moyen`
- `low` + `ignore` -> `Ignorer`

Important :
- la donnée brute n’a pas encore été migrée partout
- la simplification est pour l’instant surtout portée par la couche UI / logique de mapping

### Règle éditoriale importante
Dans la vue `Films`, les éléments suivants sont des **critères de sélection principaux** :
- titre
- année
- tagline
- réal
- casting
- pays
- durée

La priorité ne remplace pas ces informations.

Résumé de principe :
- **priorité = à quel point je veux le voir**
- **métadonnées film = pourquoi je veux le voir**

---

## 3. État CSS / implémentation

### Fichiers clés déjà stabilisés
- `frontend/src/styles/tokens.css`
- `frontend/src/style.css`
- `frontend/src/styles/planning.css`
- `frontend/src/styles/films.css`
- `frontend/src/styles/settings.css`

### Travail déjà fait
- rétablissement d’un dark theme cohérent
- réduction massive des magic numbers dispersés
- centralisation des primitives d’espacement / radius / tailles de dots
- sortie de styles partagés UI hors de `films.css`
- nettoyage important de `planning.css`
- harmonisation progressive des contrôles entre vues

### Composants UI à retenir
- `PriorityBadge.vue`
- `PrioritySelect.vue`

Ils affichent désormais une hiérarchie simplifiée en 3 niveaux, tout en acceptant encore les anciennes valeurs.

---

## 4. État des vues

### `Films`
État actuel :
- beaucoup plus lisible qu’avant
- priorité simplifiée en 3 niveaux côté UI
- carte film encore éditoriale, ce qui est volontaire
- la sélection repose toujours sur les infos film, pas seulement sur la priorité

Déjà fait :
- simplification des badges / selecteurs de priorité
- rendu plus sobre des priorités
- cycle header plus calme
- séparation visuelle plus propre entre films

À garder en tête :
- ne surtout pas transformer cette vue en simple tableau utilitaire
- la tagline doit rester visible et utile

### `Planning`
État actuel :
- beaucoup plus propre visuellement
- cohérence sémantique restaurée sur `tentative` / `confirmed`
- logique accent + opacité en place
- encore la vue à plus forte valeur produit

Déjà fait :
- réalignement CSS / markup
- simplification des états
- réduction du bruit visuel
- documentation détaillée de P2 dans `docs/ux-roadmap.md`

À garder en tête :
- ne pas recharger la timeline avec trop de signaux
- limiter les CTA par séance
- continuer à penser “arbitrage” et non “catalogue”

### `Trous / Créneaux libres`
État actuel :
- utile fonctionnellement
- encore perçu comme une extraction logique plus que comme un assistant UX

À traiter plus tard :
- meilleure hiérarchisation des suggestions
- messages plus actionnables
- distinction plus claire entre bon match / option moyenne / rien d’utile

### `Settings`
État actuel :
- plus cohérent visuellement
- reste secondaire dans le produit

Règle :
- ne pas laisser les settings absorber des décisions produit qui devraient vivre dans le flux principal

---

## 5. Incohérences ou dettes encore présentes

### Dette produit / donnée
- le type `Priority` reste à 5 valeurs dans `frontend/src/types.ts`
- les mocks et certaines logiques métier utilisent encore `must-see` / `low`
- la simplification 3 niveaux est donc réelle en UX, mais pas encore complètement migrée en profondeur

### Dette de nomenclature tokens
Le système est stable, mais encore transitoire :
- il reste des alias (`color-text`, `color-bg`, etc.) pour compatibilité
- ce n’est pas bloquant tant qu’on ne relance pas une grosse refonte

### Dette logique
Il faut encore surveiller les endroits où la logique métier 5 niveaux peut réintroduire des distinctions non voulues dans l’interface.

---

## 6. Règles de travail pour les prochaines sessions

### À faire
- avancer par petites passes ciblées
- rebuild après chaque étape significative
- préférer simplification + validation plutôt que refonte large
- mettre à jour la doc si une décision produit ou UI change vraiment

### À éviter
- relancer une grosse refonte du design system d’un seul coup
- ajouter de nouvelles couleurs métier
- complexifier la logique de priorité avant d’avoir stabilisé le workflow
- surcharger `Planning` avec plus de badges, d’icônes ou de CTA

---

## 7. Commande de validation

À lancer après toute passe UI importante :

```bash
cd frontend
npm run build
```

Le build a déjà été utilisé comme garde-fou tout au long des dernières itérations. Il faut continuer ainsi.

---

## 8. Prochaines priorités recommandées

Ordre conseillé :

1. clarifier le workflow global à l’échelle du produit
2. renforcer `Films` comme espace de sélection éditoriale
3. transformer `Planning` en espace d’arbitrage encore plus guidé
4. faire de `Trous` un vrai assistant de complétion

Pour la suite immédiate, la roadmap de référence reste :

- `docs/ux-roadmap.md`

Et ce fichier sert de complément opérationnel.

---

## 9. Décisions désormais verrouillées pour la suite

### Workflow canonique
Le workflow produit de référence est désormais :

1. `Select films`
2. `Arbitrate conflicts`
3. `Fill remaining gaps`

Traduction de travail possible côté UI FR :

1. `Films`
2. `Planning`
3. `Trous`

Important :
- `Films` = qualification éditoriale
- `Planning` = arbitrage de séances
- `Trous` = complétion opportuniste

Le produit ne doit plus présenter ces vues comme 3 outils parallèles.
Elles forment une séquence.

### Promesse UX par vue

- `Films` : m'aider à décider quels films méritent vraiment mon attention
- `Planning` : m'aider à choisir la bonne séance quand ça entre en collision
- `Trous` : m'aider à compléter les moments libres avec les meilleures options restantes
- `Settings` : rester hors du flux principal

### Action principale par vue

- `Films` : définir la priorité du film
- `Planning` : choisir / remplacer une séance
- `Trous` : remplir un créneau
- `Settings` : enregistrer la configuration

Si une vue expose plusieurs actions de même poids, la hiérarchie est mauvaise.

### Décision spécifique sur `Films`

La vue `Films` doit maintenant être traitée comme un **workspace éditorial de tri**.

Structure recommandée à implémenter :
- header avec progression
- sections orientées priorité : `A traiter`, `Prioritaires`, `Moyens`, `Ignores`
- cartes éditoriales stabilisées
- CTA passerelle vers `Planning`

Rappel critique :
- ne pas aplatir la carte en ligne de tableau utilitaire
- ne pas rendre les signaux planning plus forts que les signaux film

### États à ne plus oublier

Pour les vues cœur (`Films`, `Planning`, `Trous`), les états suivants doivent être explicitement pensés :
- empty
- loading
- error
- transition feedback

L'absence de ces états n'est pas un détail visuel. C'est une dette UX structurelle.
