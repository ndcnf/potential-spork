# Docs Map

Ordre de lecture recommandé :

1. `docs/source-of-truth.md`
2. `docs/current-ui-state.md`
3. `docs/next-steps.md`
4. `docs/product-simplification-review.md` si travail de refonte / reduction de code
5. `docs/backend-import-architecture.md` si travail backend import

Rôle de chaque fichier :

- `source-of-truth.md` : but du produit, règles métier, choix verrouillés.
- `current-ui-state.md` : état réellement implémenté dans le frontend.
- `next-steps.md` : dettes, travaux restants, idées ouvertes non validées.
- `product-simplification-review.md` : review globale produit / UX / frontend / backend / docs pour reduire le code sans perdre les decisions.
- `backend-import-architecture.md` : design backend cible pour une chaîne d’import agnostique de la source.

Règle :

- si une note ancienne contredit `source-of-truth.md`, `source-of-truth.md` gagne.
- `current-ui-state.md` décrit ce qui existe vraiment dans le code.
- `next-steps.md` ne verrouille rien à lui seul.
