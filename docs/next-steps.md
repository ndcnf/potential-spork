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
- réduire ensuite la dette `must-see` / `low`
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
