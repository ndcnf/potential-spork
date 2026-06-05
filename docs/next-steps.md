# Next Steps

## Current Priorities

Ordre recommandé :

1. continuer à simplifier la lecture de `Planning`
2. finaliser les états système réels si un cas faible réapparaît
3. réduire la dette legacy autour des priorités
4. garder `Trous / Free Slots` hors scope tant qu’un vrai chantier dédié n’est pas lancé

## Concrete Remaining Work

### `Films`

- clarifier la zone séance du header
- continuer le polish de la carte sans recharger l’interface
- éventuellement renommer plus tard `PrioritySelect` vers un nom plus produit

### `Planning`

- continuer à calmer les états visuels si certains restent trop proches ou trop forts
- surveiller la densité réelle des actions dans la timeline
- garder la méta principale courte

### Data / Tech

- réduire la dette `must-see` / `low`
- définir plus tard une stratégie si synchronisation serveur des choix devient nécessaire
- revoir la règle actuelle de persistance locale > état distant dès que les vraies données seront accessibles de manière fiable

## Open Ideas — Not Validated

Ces pistes sont compatibles ou à explorer, mais **pas verrouillées**.

### Toutes les pages

- Avoir un background noir et plus de degrade a la Linear pitie
- Voir le commentaire sur la classe generique pour toutes les pages pour la coherence visuelle
- Le titre dans le `app-header__brand` devra être "PLANIFFFICATEUR" au lieu de "Festival Planner"
- Pour Paramètres, ça devrait être précede par l'icone fournie et aligne a droite.
- Exporter iCal ne devrait pas etre dans la nav a droite, car deja dans le planning.

### `Films`

- `Non merci` encore plus discret : bordure seule, fond absent
- retravailler encore le dégradé / surlignage des cycles si inutile
- faire vivre progression, sauvegarde locale et navigation légère dans une même région si utile
- moins de layout shift quand il y a une seance ou non. Prevoir la place ou l'integrer d'une meilleure maniere. Et ne pas mettre cette information dans une bordure, ca alourdit trop.
- Faire attention a l'equilibre des elements en couleur. Ça peut encore etre plus sobre pour une meilleure lisibilite.
- Le fond entre un film non choisi et un film "peut-etre" est encore trop similaire. Ne pas avoir de fond quand le film n'est pas choisi.
- Se baser sur les couleurs pastilles (border et background) pour les boutons de choix
- Pour le boutons Replier, le plus utile serait un "Non merci" pour tout le cycle, mais a voir comment le formuler. Pas besoin de replier ensuite, juste passer l'etat de tous les films du cycle en "Non merci". Faire attention a la coherence si on passe avec des icones.
- Faire en sorte que les boutons de compteurs servent de filtre et soient cumulables
- Faire attention et fix le compteur pour qu'il reste une vérité sur l'ensemble et pas juste ce qu'il montre
- Fix le contraste et l'ordre de ces boutons
- Supprimer la recherche, par prio, tri et masquer les ignores. Ca complexifie et c'est repris avec les boutons compteurs.

Idealement ajouter les icones svg ajoutees a la racine depuis ici: https://icon-sets.iconify.design/solar/.
Bien discuter UX et frontend afin que ces icones permettent d'alleger visuellement, mais pas perdre le sens. Les mentions doivent au moins se faire au hover. Mais les coeurs me semblent quand meme assez comprehensibles sur les intentions. Bien entendu, deplacer les icones dans un endroit plus approprie comme un repo "assets/icons" ou du genre. Un statut sur la carte, juste avant la seance pourrait afficher l'etat "A traiter", "Non merci", etc. pour expliciter l'icone.
Mentionner Solar dans le footer si ces icones sont utilisees pour etre correct avec la licence.

### `Planning`

- continuer à simplifier les états si certaines nuances restent difficiles à lire
- réévaluer plus tard si l’action directe `Ignorer` doit changer de libellé ou de poids visuel
- faire en sorte que les espacements du contenu soit le meme que pour les autres pages. Faire ceci de maniere generique et propre avec un classe commune entre les pages.

### `Parametres`

- Refaire une passe sur les recommandations, parce que je ne vois pas vraiment leur conséquence dans le panel "planning'. Il n'y a pas d'incentive à choisir une séance au lieu d'une autre ou surtout faire attention.
- Boxer un peu plus pour rendre les options plus agreables a lire ou mettre sur 2 colonnes
- Les horaires a mettre a la ligne

## Rules For Next Sessions

- faire des passes courtes
- rebuild après chaque passe significative
- préférer simplification + validation à une refonte large
- mettre la doc à jour seulement si un choix réel change

## Validation Command

```bash
cd frontend
npm run build
```
