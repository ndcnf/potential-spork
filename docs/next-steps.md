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

### `Films`

- `Non merci` encore plus discret : bordure seule, fond absent
- retravailler encore le dégradé / surlignage des cycles si inutile
- faire vivre progression, sauvegarde locale et navigation légère dans une même région si utile

### `Planning`

- continuer à simplifier les états si certaines nuances restent difficiles à lire
- réévaluer plus tard si l’action directe `Ignorer` doit changer de libellé ou de poids visuel

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
