# Document de vérité — NIFFF Planner

Ce document tranche les ambiguïtés restantes dans `docs/current-ui-state.md` et `docs/ux-roadmap.md`.

Il sert de référence de travail pour les prochaines itérations.

En cas de contradiction avec une note plus ancienne, **ce document fait foi**.

---

## 1. Position produit

NIFFF Planner est un outil personnel de planification **film-first**.

Sa promesse n’est pas :
- d’exposer un système expert,
- d’optimiser de manière opaque,
- de forcer un tunnel rigide.

Sa promesse est :

**m’aider à transformer une envie de films en planning réaliste, sans me faire penser comme un expert du festival.**

---

## 2. Workflow de référence

Le produit repose sur 2 espaces principaux actifs :
- `Films`
- `Planning`

Important :
- ce sont des **espaces de travail complémentaires**,
- pas des étapes verrouillées,
- pas un tunnel rigide,
- pas un wizard séquentiel.

L’utilisateur peut revenir de `Planning` vers `Films` à tout moment.
Ce va-et-vient fait partie du comportement normal du produit.

Conséquence directe :
- **pas d’étapes numérotées obligatoires** dans l’interface principale si cela rigidifie artificiellement le parcours,
- la progression doit être visible comme **état d’avancement**, pas comme tunnel imposé.

---

## 3. Rôle exact de chaque vue

### `Films`
Rôle : **qualifier les films**.

La vue doit aider à répondre rapidement à :
- pourquoi ce film m’intéresse,
- est-ce que je le veux vraiment,
- qu’est-ce qu’il me reste à trier.

`Films` est un **workspace éditorial de tri**.
Ce n’est pas :
- un tableau utilitaire,
- un pseudo planner,
- un dump de métadonnées.

### `Planning`
Rôle : **arbitrer des séances**.

La vue doit aider à répondre rapidement à :
- qu’est-ce qui est déjà retenu,
- où sont les conflits,
- que vais-je perdre si je choisis cette séance.

`Planning` est un **workspace d’arbitrage**.
Ce n’est pas :
- un écran de découverte,
- un catalogue bis,
- une console multi-CTA.

### `Settings`
Rôle : configuration secondaire, hors flux principal.

Les `Settings` ne doivent pas absorber des décisions produit qui devraient vivre dans `Films` ou `Planning`.

---

## 4. Vérité produit sur `Films`

### 4.1 Structure principale

La structure de `Films` est **par cycle**.

Le cycle est :
- une structure éditoriale de lecture,
- un univers de programmation,
- un repère d’orientation.

Le cycle n’est pas :
- un objet de décision,
- un niveau de priorité,
- un contrôle d’override.

### 4.2 Décision verrouillée sur la structure interne

**Direction retenue : Direction A.**

Dans chaque cycle :
- on garde une **liste plate de films**,
- on n’introduit **pas** de sous-sections visuelles lourdes du type :
  - `À traiter`
  - `Immanquables`
  - `Peut-être`
  - `Non merci`

Pourquoi :
- segmenter visuellement la liste par statuts casserait la logique éditoriale du cycle,
- cela augmenterait la charge cognitive,
- cela ferait dériver la vue vers un outil de gestion de statuts plutôt que vers un espace de sélection.

Les statuts doivent rester lisibles via :
- le contrôle inline,
- les compteurs,
- les signaux de progression,
- éventuellement les dots de synthèse.

Pas via une re-segmentation structurelle lourde.

### 4.3 Payload de décision obligatoire

La carte film doit conserver visibles les éléments suivants :
- titre
- année
- tagline
- réalisateur
- casting
- pays
- durée

Règle non négociable :
- **la priorité ne remplace pas ces informations**,
- **la tagline n’est pas décorative**.

La priorité répond à :
- `à quel point je veux le voir`

Les métadonnées film répondent à :
- `pourquoi je veux le voir`

Les deux sont nécessaires.

### 4.4 Action principale

L’action principale de `Films` est :
- **qualifier un film**

Le contrôle associé est aujourd’hui `PrioritySelect`, même si ce nom technique pourra évoluer.

Règles :
- ce contrôle doit être visible,
- il doit être haut dans la hiérarchie de la carte,
- il doit être immédiat,
- il doit être accessible clavier,
- il ne doit pas être relégué comme statut secondaire.

La carte film ne doit pas simuler une grande zone cliquable si ce n’est pas son vrai comportement.
Les affordances imbriquées sont une erreur.

### 4.5 Priorités visibles

Libellés UI retenus :
- `Immanquable`
- `Peut-être`
- `Non merci`

État initial attendu :
- `À traiter`

Règle produit :
- les films arrivent sans décision préalable,
- `À traiter` est un vrai état initial de tri,
- ce n’est pas une pseudo-priorité basse déguisée.

---

## 5. Vérité produit sur `Planning`

`Planning` doit rester centré sur l’arbitrage.

La vue principale doit montrer d’abord :
- la structure temporelle,
- les collisions,
- les choix déjà faits,
- les conséquences d’un choix.

Le panneau de détail porte la complexité utile.
La timeline ne doit pas devenir un cockpit.

Règles :
- une action dominante par contexte,
- pas de multiplication de CTA par séance,
- pas de surcharge de badges, d’icônes ou de tags,
- les conséquences d’une action doivent être explicites.

---

## 6. Position verrouillée sur la navigation

Décision :
- **pas de CTA dominant obligatoire `Passer au Planning`** comme pivot structurel du produit.

Raison :
- le parcours n’est pas rigide,
- l’utilisateur peut arbitrer puis revenir qualifier,
- une navigation trop dirigiste trahirait l’usage réel.

Cela n’interdit pas :
- des signaux de progression,
- des liens de navigation utiles,
- des invitations contextuelles légères.

Mais cela exclut :
- une logique de passage forcé,
- un verrou de type étape suivante obligatoire,
- une mise en scène de wizard numéroté qui ment sur la nature réelle du flux.

---

## 7. Règle verrouillée sur `pas de séance prévue`

Décision finale :

**`pas de séance prévue` ne concerne que les films `Immanquables`.**

Cette alerte ne doit pas être affichée pour :
- `Peut-être`
- `Non merci`

Pourquoi :
- sinon on injecte trop tôt une anxiété planning dans une vue qui doit rester d’abord éditoriale,
- pour un film moyen, ce signal est du bruit,
- l’alerte doit rester rare et significative.

---

## 8. États système non négociables

Pour `Films` et `Planning`, les états suivants doivent être explicitement traités :
- `empty`
- `loading`
- `error`
- `transition feedback`

Ce n’est pas du polish.
C’est une condition de crédibilité du produit.

Point critique :
- le fallback mock ne doit pas masquer un vrai état `error`,
- un échec réel de chargement doit être compréhensible et visible comme tel.

---

## 9. Règles de hiérarchie visuelle

### Dans `Films`
- les signaux film dominent les signaux planning,
- la lecture éditoriale domine la mécanique de statut,
- la priorité doit être visible sans écraser le contenu,
- pas de hover global trompeur sur la carte,
- le focus visible vit sur les vrais éléments interactifs.

### Dans `Planning`
- le temps et les conflits dominent,
- la décision actuelle est immédiatement lisible,
- l’accent sert l’intention forte, pas la décoration,
- la densité d’actions doit rester basse.

---

## 10. Ce qu’on ne relance pas maintenant

Hors scope immédiat :
- retour de `Trous / Créneaux libres` dans le flux actif,
- nouvelle complexification des priorités,
- segmentation lourde de `Films` par statuts,
- navigation en pseudo-wizard,
- enrichissement visuel décoratif qui affaiblit la clarté.

---

## 11. Conséquences opérationnelles pour la suite

Pour les prochaines itérations, cela implique :

1. Auditer `Films` contre cette vérité :
   - structure plate par cycle,
   - hiérarchie de carte,
   - contrôle de qualification vraiment central,
   - absence de faux tunnel de navigation.

2. Auditer `Planning` contre cette vérité :
   - arbitrage lisible,
   - densité de CTA maîtrisée,
   - conséquences explicites.

3. Finaliser les états système réels :
   - empty,
   - loading,
   - error,
   - feedback de transition.

4. Réserver `pas de séance prévue` aux seuls `Immanquables`.

---

## 12. Résumé ultra-court

- `Films` = espace éditorial de tri par cycle
- `Planning` = espace d’arbitrage de séances
- pas de tunnel rigide
- pas d’étapes numérotées imposées
- pas de segmentation lourde des films par statuts dans chaque cycle
- `pas de séance prévue` = `Immanquable` uniquement
- vrais états `empty/loading/error` obligatoires

Fin.
