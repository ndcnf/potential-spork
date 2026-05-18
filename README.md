# potential-spork

Festival planner perso pour le NIFFF.

## Stack

- Backend: `FastAPI` + `SQLAlchemy` + `SQLite`
- Import: `requests` + `BeautifulSoup`
- Frontend: `Vue 3` + `Vite` + `Pinia`

## Structure

- `backend/`: API, persistence, import NIFFF, export `.ics`
- `frontend/`: proto UI/UX navigable pour `Films`, `Planning`, `Trous`

## Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn app.main:app --reload
```

API disponible sur `http://localhost:8000`.

Endpoints V1 utiles:

- `GET /health`
- `GET /api/cycles`
- `GET /api/films`
- `POST /api/imports/nifff/catalog`
- `GET /api/screenings`
- `GET /api/planning`
- `GET /api/exports/confirmed.ics`

## Frontend

```bash
cd frontend
npm install
npm run dev
```

App disponible sur `http://localhost:5173`.

Le frontend utilise l'API si elle tourne. Sinon il bascule sur des donnees mockees pour servir de proto UI/UX.

## Etat actuel

- Le vieux proof of concept Flask a ete retire de l'app
- La logique de parsing NIFFF a ete reprise dans `backend/app/services/import_nifff.py`
- L'UI actuelle sert de proto navigable, pas encore de produit fini
- L'import des seances devra etre complete quand les horaires 2026 seront publies
