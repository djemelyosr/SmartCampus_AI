# SmartCampus AI – Plateforme agentique d’orientation universitaire 

# Design – Figma

Découvrez le prototype de SmartCampus AI :

 [Voir le prototype SmartCampus AI sur Figma](https://www.figma.com/design/8JBtC37rgoEJcRYiSEAf09/SmartCampusIA?node-id=0-1)

---

# SmartCampus AI – Backend (FastAPI)

Installation, configuration, données de démonstration et démarrage : voir **[../GUIDE_DEMARRAGE.md](GUIDE_DEMARRAGE.md)**.

Démarrage rapide (Windows `cmd`, depuis `backend`) :

```bash
.venv\Scripts\python -m app.cli init-env
.venv\Scripts\python -m app.cli seed-demo
.venv\Scripts\python -m uvicorn app.main:app --reload
```

SQLite par défaut (aucune installation) ; PostgreSQL + pgvector en option (`docker compose up -d db`, voir le guide).
Documentation interactive : http://localhost:8000/docs

## API

| Domaine | Routes | Accès |
|---|---|---|
| Comptes | `POST /api/auth/register` · `POST /api/auth/login` · `GET /api/auth/me` · `GET/PUT /api/auth/me/profile` | public / connecté / candidat |
| Administration | `GET/POST /api/admin/users` · `PATCH /api/admin/users/{id}` | administrateur |
| Catalogue | `/api/programs` · `/api/specialties` · `/api/curricula` · `/api/subjects` (GET liste/détail, POST, PATCH, DELETE) | lecture publique ; écriture : responsable de l’établissement ou admin |
| Informations officielles | `/api/admission-conditions` · `/api/fees` · `/api/payment-terms` (+ `POST /{id}/publish|archive|draft`) · `GET /api/programs/{id}/official-info` | public : publié et en vigueur uniquement |
| Chat | `POST /api/conversations` · `GET /api/conversations[/{id}]` · `POST /api/conversations/{id}/messages` | compte, ou session visiteur (`X-Guest-Session`) |
| Sessions visiteur | `POST /api/guest/sessions` · `GET/DELETE /api/guest/session` · `GET /api/guest/limits` · `GET /api/guest/claim/preview` · `POST /api/guest/claim` | visiteur / candidat |
| Candidature | `/api/preinscriptions` · `/api/qcm/...` · `/api/appointments/...` · `/api/documents/...` | candidat (documents : aussi l’équipe) |
| Équipe | `GET /api/stats/overview` · `GET /api/interviews/candidates[/{id}]` | direction, responsables (leur établissement), entretien, admin |

## Structure

- `app/api/routes` : une route par domaine (`catalog.py` gère les 7 ressources du catalogue de façon générique)
- `app/api/deps.py` : authentification, rôles, périmètre par établissement
- `app/models/models.py` : modèles SQLAlchemy · `app/schemas` : schémas Pydantic
- `app/services/guest.py` : sessions visiteur (création, expiration, limites, rattachement)
- `app/services/orchestrator.py` : point d’entrée de l’agent (stub, à remplacer par LangGraph)
- `app/cli.py` : commandes locales (`init-env`, `seed-demo`, `reset-db`, `create-admin`, `purge-guests`, `check`)
- `app/demo_data.py` : données de démonstration · `app/seed.py` : catalogue de base

## Tests

```bash
.venv\Scripts\python -m pip install -r requirements-dev.txt
.venv\Scripts\python -m pytest
```

SQLite en mémoire : n’utilise ni PostgreSQL ni votre base locale.
