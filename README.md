# Application de pointage des employés

Application web simple de pointage avec:

- Login des employés
- Bouton `BONJOUR JE SUIS LA` pour l'arrivée
- Bouton `AU REVOIR` pour le départ
- Stockage SQLite
- API JSON pour enregistrer/lister les heures
- Export Excel des présences (admin)
- Tableau de bord administrateur

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Application disponible sur `http://localhost:5000`.

## Comptes de démonstration

- admin / admin123
- alice / alice123
- bob / bob123

## API

- `POST /api/presences/arrival`
- `POST /api/presences/departure`
- `GET /api/presences`

Ces routes nécessitent une session connectée.
