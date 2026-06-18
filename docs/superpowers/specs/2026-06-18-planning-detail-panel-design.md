# Planning Detail Panel Design

## Goal

Remanier le panel de droite du Planning pour aider a choisir une seance plus vite, sans transformer le panel en fiche film longue.

## Scope

Inclus :

- reorganiser le panel autour de la decision de seance
- separer visuellement le statut utilisateur et la recommendation systeme
- rendre `tentative` et `confirmed` plus distincts
- garder une zone stable pour les infos de lieu futures

Exclu :

- modele backend des venues
- nouveaux reglages de lieux dans `Parametres`
- refonte complete de la timeline principale

## UX Structure

Le panel doit suivre cet ordre :

1. Film compact : titre, priorite, cycle/premiere si disponible.
2. Seance active : date, heure, salle, statut utilisateur, actions principales.
3. Comparer les seances : liste de rows compactes pour les autres options du meme film.
4. Liens externes : agenda, billetterie, fiche NIFFF, IMDb.

Les details film longs restent secondaires. Le poster reste possible, mais ne doit pas dominer l'arbitrage.

## Visual Language

Deux axes visuels doivent etre separes :

- decision utilisateur : `Confirmée`, `Tentative`, `Ignorée`, `Conflit`
- conseil systeme : recommendation, point favorable, point a surveiller

Regles :

- `Confirmée` utilise un marker plein et un vert doux.
- `Tentative` utilise une nuance neutre, un marker contour ou dashed.
- `Recommendation` utilise le dore, une chip plus petite, outline, et ne reprend pas la meme forme que le statut.
- `Conflit` doit garder un label explicite et une bordure visible ; la couleur seule ne suffit pas.

## Venues Follow-Up

Le chantier lieux doit etre repris apres ce remaniement :

- recuperer les venues/lieux comme donnees explicites
- les exposer proprement dans `Parametres`
- permettre des preferences de lieu plus claires que les scores actuels par `venue_name`

Pour ce changement, le panel garde simplement une zone stable ou ces futures infos pourront apparaitre.
