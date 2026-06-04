# Current UI State — NIFFF Planner

Ce fichier sert de mémo d’exécution.  
Il complète `docs/ux-roadmap.md`, qui porte surtout la vision produit et la roadmap UX.

Objectif : permettre de reprendre le travail dans une nouvelle session sans refaire tout le contexte.

---

## 1. État actuel du produit

Le frontend est organisé autour de 3 vues principales :
- `Films`
- `Planning`
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
- `Immanquable`
- `Peut-etre`
- `Non merci`

Mais l'état initial produit est désormais explicite :
- `A traiter`

Compatibilité temporaire conservée avec les anciennes valeurs de données :
- `must-see` + `high` -> `Immanquable`
- `medium` -> `Peut-etre`
- `ignore` -> `Non merci`
- `low` -> ancien legacy a faire migrer vers `A traiter`

Important :
- l'état initial attendu n'est plus une pseudo-priorité basse
- un film doit arriver **sans sélection préalable**
- la couche UI et le store convertissent encore les anciennes valeurs `low` vers un vrai état de tri initial

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
- étape `2 sur 2` désormais explicite dans l'UI
- guidage en tête de vue désormais orienté arbitrage
- panneau de détail recentré sur la comparaison de séances et leurs conséquences
- hiérarchie d'actions simplifiée dans la timeline et dans le panneau : une action principale, puis actions secondaires limitées

Déjà fait :
- réalignement CSS / markup
- simplification des états
- réduction du bruit visuel
- documentation détaillée de P2 dans `docs/ux-roadmap.md`
- suppression des anciennes grilles d'actions de même poids dans `Planning`
- recentrage des CTA sur `choisir / remplacer`, puis `confirmer` en second temps

À garder en tête :
- ne pas recharger la timeline avec trop de signaux
- limiter les CTA par séance
- continuer à penser “arbitrage” et non “catalogue”

### `Trous / Créneaux libres`
Statut actuel :
- retiré du frontend courant
- reporté à une V2 ou V3

Décision :
- ne plus maintenir cette vue dans le MVP actuel
- si le sujet revient, le reprendre comme un vrai chantier produit séparé, pas comme un reste du flux principal

### `Settings`
État actuel :
- plus cohérent visuellement
- reste secondaire dans le produit

Règle :
- ne pas laisser les settings absorber des décisions produit qui devraient vivre dans le flux principal

---

## 5. Incohérences ou dettes encore présentes

### Dette produit / donnée
- le type `Priority` porte encore des valeurs legacy dans `frontend/src/types.ts`
- les anciennes valeurs `must-see` et `low` existent encore pour compatibilité
- `low` ne doit plus être lu comme une préférence réelle, mais comme un reliquat à migrer vers l'état initial `A traiter`

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

1. compléter les états guidés restants (`loading`, `error`, `transition feedback`) sur les vues cœur actives
2. poursuivre l’allègement de `Planning` si de nouveaux points de friction apparaissent dans la timeline
3. garder `Trous` hors scope jusqu'à une V2 ou V3 explicite

Déjà acté et implémenté dans le frontend :

- workflow principal visible en `1. Films` / `2. Planning`, sans troisième étape active dans le frontend courant
- `Films` renforcé comme espace de sélection éditoriale avec progression visible et CTA passerelle vers `Planning`
- `Planning` recentré comme espace d’arbitrage avec guidage explicite et hiérarchie d’actions simplifiée

Pour la suite immédiate, la roadmap de référence reste :

- `docs/ux-roadmap.md`

Et ce fichier sert de complément opérationnel.

---

## 9. Décisions désormais verrouillées pour la suite

### Workflow canonique
Le workflow produit de référence pour la version courante est désormais :

1. `Select films`
2. `Arbitrate conflicts`

`Fill remaining gaps` est explicitement reporté à une V2 ou V3.

Traduction de travail possible côté UI FR :

1. `Films`
2. `Planning`

Important :
- `Films` = qualification éditoriale
- `Planning` = arbitrage de séances

Le produit ne doit plus présenter les vues actives comme des outils parallèles.
La séquence courante est un parcours explicite en 2 étapes : `Films` puis `Planning`.

### Promesse UX par vue

- `Films` : m'aider à décider quels films méritent vraiment mon attention
- `Planning` : m'aider à choisir la bonne séance quand ça entre en collision
- `Settings` : rester hors du flux principal

### Action principale par vue

- `Films` : définir la priorité du film
- `Planning` : choisir / remplacer une séance
- `Settings` : enregistrer la configuration

Si une vue expose plusieurs actions de même poids, la hiérarchie est mauvaise.

### Décision spécifique sur `Films`

La vue `Films` doit maintenant être traitée comme un **workspace éditorial de tri**.

Structure recommandée à implémenter :
- header avec progression
- structure principale par `cycle`
- liste plate de films dans chaque cycle
- cartes éditoriales stabilisées
- CTA passerelle vers `Planning`

Règle produit :
- la priorité se décide au niveau **film uniquement**
- le cycle reste une structure éditoriale de lecture
- aucun `PrioritySelect` au niveau cycle dans le MVP

Décisions UI désormais actées :
- header global avec progression visible
- CTA `Passer au Planning` conditionné par au moins un film `Prioritaire`
- CTA `Passer au Planning` conditionné par au moins un film `Immanquable`
- dots de progression conservées au niveau cycle comme **signal de synthèse**, pas comme contrôle
- pas de sous-sections visuelles `A traiter / Prioritaires / Moyens / Ignores` dans chaque cycle
- distinction des cycles portée d'abord par la typographie, pas par des pastilles couleur
- headers de cycle renforcés par un traitement plus organique, type surlignage / encre, sans tomber dans l'effet décoratif gratuit
- cartes film raffinées typographiquement : titre plus dense, tagline plus lisible, métadonnées plus discrètes et ligne séance traitée comme un chip éditorial léger
- la carte film reste un support de lecture, pas une fausse zone cliquable
- les états d'interaction forts vivent sur les vrais contrôles, pas sur tout le bloc carte
- à l'initialisation, les films arrivent en état **`A traiter`**, sans sélection préalable
- le rappel `pas de seance prevue` ne concerne que les films `Prioritaires`
- le statut reste lisible via le contrôle dans la carte, les dots et les compteurs, sans bruit structurel supplémentaire

Rappel critique :
- ne pas aplatir la carte en ligne de tableau utilitaire
- ne pas casser le regroupement par cycle : c'est un critère éditorial primaire
- ne pas rendre les signaux planning plus forts que les signaux film

### États à ne plus oublier

Pour les vues cœur actives (`Films`, `Planning`), les états suivants doivent être explicitement pensés :
- empty
- loading
- error
- transition feedback

L'absence de ces états n'est pas un détail visuel. C'est une dette UX structurelle.

---

## 10. Plan d’implémentation concret — Vue `Films`

### Lecture franche de l’existant

La base actuelle de `Films` n’est pas mauvaise. Et il faut être clair :
le regroupement par `cycle` est une force du produit, pas un défaut à corriger.

Concrètement, l’implémentation actuelle dans `frontend/src/views/FilmsView.vue` pose 3 limites :

1. le header n’exprime pas la progression utilisateur
2. l’état de tri à l’intérieur des cycles reste peu visible
3. la vue montre encore des signaux de structure interne qui peuvent être mieux convertis en signaux de progression

Le choix à faire est simple :
**garder le cycle comme structure principale, puis rendre la progression de tri explicite à l’intérieur de chaque cycle.**

Direction visuelle désormais retenue :
**une gestion papier stylisée, simple et organique, portée d'abord par la typographie et un accent de surlignage sobre sur les titres de cycle.**

### Fichiers concernés

#### Vue
- `frontend/src/views/FilmsView.vue`

#### Styles
- `frontend/src/styles/films.css`

#### Composants existants à stabiliser
- `frontend/src/components/ui/PrioritySelect.vue`
- `frontend/src/components/ui/PriorityBadge.vue`

#### Dette connue liée au modèle
- `frontend/src/types.ts`

### Objectif V1

Faire de `Films` un espace de tri éditorial piloté par les cycles, avec une progression utilisateur visible dans chaque cycle, sans relancer une grosse refonte de données.

Le point important :
**on ne refond pas toute l’architecture. On réordonne la vue pour qu’elle serve enfin le workflow.**

Autre règle importante :
**on supprime la priorité au niveau cycle. La décision de préférence vit uniquement sur les films individuels.**

### Ce qu’il faut changer, dans l’ordre

#### Étape 1 — Refaire le header de vue

But : orienter, montrer la progression, ouvrir la porte vers `Planning`.

À implémenter dans `FilmsView.vue` :
- titre : `Films`
- support line : `Qualifiez les films avant d'arbitrer les seances.`
- 3 compteurs visibles :
  - `Prioritaires`
  - `Moyens`
  - `Restants a trier`
- 1 CTA dominant : `Passer au Planning`

Règle :
- le CTA ne doit pas être juste décoratif
- s’il est désactivé, il faut expliquer pourquoi

Exemple de microcopy :
- `Selectionnez quelques films prioritaires pour lancer un arbitrage utile.`

À calculer côté vue :
- `highCount`
- `mediumCount`
- `untriagedCount` = films dont la priorité simplifiée est encore faible / ignorée selon la règle retenue

Point de vigilance :
- si `ignore` est traité comme une vraie décision, il ne faut pas le compter dans `Restants a trier`
- si vous voulez un vrai bucket `A traiter`, il faut introduire une notion métier distincte plus tard

Donc pour V1, la version saine est :
- `Restants a trier` = films visibles en état `unreviewed`

#### Étape 2 — Garder la logique par cycle comme structure principale

But : préserver le premier critère éditorial tout en ajoutant une lecture de progression.

La structure principale recommandée reste :
- `Cycle`
- `Liste de films`

Le cycle doit rester le conteneur principal de la page.

Ce choix est important :
la structure par cycle porte la logique de programmation et de désir.
Ce qu’il faut corriger n’est pas le cycle lui-même, mais l’absence de sous-structure claire pour le tri.

Implémentation recommandée :
- conserver `store.groupedFilms` comme base
- garder une liste plate de films dans chaque cycle
- utiliser les compteurs et dots pour résumer la progression sans resegmenter visuellement la liste
- règle transitoire : `unreviewed` = `A traiter`, `high/must-see` = `Prioritaires`, `medium` = `Moyens`, `ignore` = `Ignores`

Contenu enrichi utile par film :
- `cycle_name`
- `cycle_color`
- `selectedScreening`
- `screeningCount`

Le cycle reste donc la structure éditoriale de premier niveau, ce qui est la bonne hiérarchie.
Il ne doit pas porter de décision de priorité.

#### Étape 3 — Stabiliser la carte film comme carte éditoriale

But : conserver le pouvoir de sélection du contenu sans le transformer en ligne utilitaire.

La carte actuelle est proche de la bonne direction, mais il faut corriger sa hiérarchie.

Structure cible dans chaque `film-card` :
- ligne 1 : titre + année + `PrioritySelect`
- ligne 2 : tagline
- ligne 3 : réalisateur
- ligne 4 : casting
- ligne 5 : pays · durée · cycle
- ligne 6 : hint de séance si utile

Traitement typographique désormais retenu :
- titre plus affirmé, serré, avec meilleure densité éditoriale
- tagline plus présente mais toujours secondaire
- métadonnées compactes et plus silencieuses
- ligne pays / durée / cycle en registre plus utilitaire, quasi-légende
- hint de séance rendu comme un petit chip calme plutôt qu'une ligne flottante banale

États visuels désormais retenus :
- pas de hover global trompeur sur la carte
- pas de traitement `selected` appliqué au conteneur complet
- le focus visible doit rester porté par les éléments réellement interactifs
- la séparation entre cartes doit rester simple, calme et lisible

### Clarification composant — `PrioritySelect`

Le nom actuel est trompeur.

Dans l'interface, `PrioritySelect` n'est pas un "sélecteur de priorité" abstrait.
C'est en réalité le **contrôle principal de qualification d'un film**.

Sa fonction exacte :
- décider si un film est `Immanquable`, `Peut-etre` ou `Non merci`
- rendre cette décision immédiate, locale, explicite
- éviter un détour par un panneau, un menu ou un formulaire secondaire

Ce composant n'est donc pas caduc dans son rôle.
Mais son **nom technique** l'est peut-être.

Nom produit / UX plus juste :
- `FilmPriorityToggle`
- ou `FilmPriorityPills`

Microcopy désormais retenue dans l'interface :
- `Immanquable`
- `Peut-etre`
- `Non merci`

Raison :
- plus explicite que `I / M / P`
- plus humain que `Prioritaire / Moyen / Ignorer`
- plus proche d'une logique de choix réel que d'un jargon de système

Règle importante :
- c'est **le vrai point d'action de la carte**
- la carte elle-même ne doit pas simuler une action plus large qu'elle n'offre

Correction nécessaire :
- aujourd’hui, le `PrioritySelect` est trop relégué en bas comme statut secondaire
- c’est une erreur, car c’est l’action principale de la vue

Il doit remonter dans la zone haute de la carte.

#### Étape 4 — Réduire le bruit “cycle header” actuel

But : retirer les éléments qui sursignalisent la structure cycle.

À réduire ou simplifier dans V1 :
- complexité visuelle superflue dans les headers de cycle
- `PrioritySelect` au niveau cycle comme action dominante
- nuages de dots de priorité par cycle
- bouton `Replier / Ouvrir` si son poids visuel dépasse l'utilité réelle

Décision MVP :
- le `PrioritySelect` au niveau cycle doit être retiré
- la priorité se gère uniquement carte film par carte film

Pourquoi :
- ces signaux racontent l’organisation des données
- ils ne racontent pas le travail que l’utilisateur doit faire

Le cycle header doit rester fort, mais plus utile :
- nom du cycle
- traitement typographique fort
- compteurs locaux
- état d’avancement du tri

Il ne doit plus porter une logique d’override ou d’héritage de priorité.

Décision récente :
- les pastilles couleur spécifiques aux cycles sont retirées
- les dots de progression restent utiles et sont conservées
- les titres de cycle peuvent recevoir un traitement de surlignage organique léger pour renforcer la lecture sans alourdir l'interface

#### Étape 5 — Garder l’indice de séance, mais à sa juste place

But : rappeler la faisabilité sans déplacer le centre de gravité vers le planning.

Conserver uniquement des hints sobres :
- séance choisie : `ven 04.07 18h30-21h00`
- pas de séance prévue : seulement pour `Prioritaire` ou `Moyen`
- nombre de séances : si utile, en texte simple

Ne pas remettre dans `Films` :
- liste complète des séances
- conflits détaillés
- plusieurs CTA de scheduling par carte

#### Étape 6 — Formaliser les états système manquants

But : arrêter de livrer une vue fonctionnelle mais incomplète.

États minimum à implémenter :

##### Loading
- skeleton header
- skeleton toolbar
- 4 à 8 skeleton cards

##### Empty global
Cas : aucun film visible après filtre  
Message : `Aucun film ne correspond a vos filtres.`  
Action : `Reinitialiser les filtres`

##### Empty section
Cas : section vide  
Exemple : `Aucun film prioritaire pour l'instant.`

##### Error
Cas : chargement impossible  
Message : `Impossible de charger les films pour le moment.`  
Action : `Reessayer`

Aujourd’hui, l’absence de ces états affaiblit la promesse de workflow guidé.

#### Étape 7 — Simplifier la toolbar

But : en faire une utility bar, pas une console.

Garder :
- recherche
- filtre priorité
- tri simple

Réévaluer :
- le wording des filtres une fois la migration legacy terminée

Ce libellé est transitoire et sent la dette de migration.
Il faudra soit :
- le reformuler clairement côté utilisateur
- soit le supprimer après nettoyage des données

Recommandation V1 :
- utiliser `Masquer les films ignores`

### Ordre de livraison recommandé

#### Passe 1
- nouveau header
- compteurs
- CTA vers `Planning`

#### Passe 2
- computed de sous-sections par décision à l’intérieur de chaque cycle
- rendu par cycles, puis sections `A traiter / Prioritaires / Moyens / Ignores`

#### Passe 3
- refonte de la hiérarchie interne de `film-card`
- `PrioritySelect` remonté dans le header de carte

#### Passe 4
- retrait du `PrioritySelect` au niveau cycle
- simplification du cycle header

#### Passe 5
- nettoyage CSS de `films.css`
- simplification des patterns devenus trop bruyants autour des cycles

#### Passe 6
- empty / loading / error states

#### Passe 7
- microcopy de transition et polish accessibilité

### Refactor technique minimal recommandé

Sans sur-ingénierie.

Si la vue commence à gonfler, extraire :
- `FilmSectionBlock.vue`
- `FilmCard.vue`
- `FilmsProgressHeader.vue`

Ne pas extraire trop tôt tout un mini design system local.
Ce serait du zèle inutile.

### Ajustements CSS concrets

Dans `frontend/src/styles/films.css`, prévoir :

- nouvelle zone `films-progress`
- nouvelle grille ou stack pour les compteurs
- styles de `film-card__header`
- styles de `film-card__meta`
- styles de `film-card__schedule-hint`
- styles d’empty sections
- styles skeleton

À réduire fortement :
- `.cycle-header__priority-dots`
- logique de `.cycle-actions` comme centre de gravité
- bruit visuel qui concurrence la lecture éditoriale des cycles

À supprimer si confirmés dans le code :
- contrôles de priorité attachés au cycle
- affordances qui suggèrent une priorité héritée cycle → film

### Validation UX attendue après implémentation

Le résultat doit permettre ceci en quelques secondes :
- voir combien de films sont déjà vraiment retenus
- comprendre ce qu’il reste à trier
- qualifier un film sans chercher l’action
- sentir que `Planning` est l’étape suivante naturelle

Si après implémentation la vue lit comme `selection éditoriale par cycle avec progression de tri visible`, alors la direction est bonne.
Si elle lit encore comme `catalogue par cycle avec contrôles`, elle reste incomplète.

Mais la progression doit rester un signal de synthèse.
Si elle introduit plus de bruit structurel que d'aide, elle est mal placée.

### Piste visuelle pour plus tard

À explorer dans une passe ultérieure, pas maintenant :
- titres de cycle encore plus affirmés
- traitement plus organique, type `surlignage / stabilo`
- sensation de gestion papier stylisée, sans perdre la lisibilité ni la sobriété

Important :
- ce futur langage visuel doit rester au service de la décision
- il ne doit pas transformer l’interface en décoration nostalgique

### Commande de validation

Comme pour le reste :

```bash
cd frontend
npm run build
```

### Suite logique après cette passe

Une fois `Films` restructuré correctement, la prochaine étape cohérente sera :
- brancher les signaux de progression avec `Planning`
- faire remonter les conflits non arbitrés comme conséquence naturelle du tri

Pas avant.
Sinon on recomplexifie le produit avant d’avoir verrouillé l’entrée du parcours.
