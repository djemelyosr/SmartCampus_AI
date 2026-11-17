# SmartCampus AI – Plateforme agentique d’orientation universitaire 

# Design – Figma

Découvrez le prototype de SmartCampus AI :

 [Voir le prototype SmartCampus AI sur Figma](https://www.figma.com/design/8JBtC37rgoEJcRYiSEAf09/SmartCampusIA?node-id=0-1)


---

# SmartCampus AI - Backend (FastAPI)

## Lancer (sans Docker ni PostgreSQL)

Par défaut le backend utilise SQLite : un simple fichier `smartcampus.db`, créé au premier démarrage
avec les 5 formations d'exemple. Rien d'autre à installer.

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m uvicorn app.main:app --reload
```

Sous PowerShell, préfixer par `.\` (ex. `.\.venv\Scripts\python ...`).

Docs interactives : http://localhost:8000/docs · Santé : http://localhost:8000/health

Le frontend (`npm run dev`, port 3000) envoie déjà `/api` vers le port 8000.

Pour repartir de zéro, arrêter l'API puis supprimer `smartcampus.db` et le dossier `uploads/`.

### Avec PostgreSQL + pgvector (optionnel)

Nécessaire pour l'index RAG (table `document_chunks`), ignorée en mode SQLite.

```bash
docker compose up -d db
```

Puis, dans `.env` : `DATABASE_URL=postgresql+psycopg://smartcampus:smartcampus@localhost:5432/smartcampus`

## Structure

- `app/api/routes` : auth, programmes, conversations, préinscriptions
- `app/models` : SQLAlchemy (users, profils, programmes, RAG chunks pgvector, conversations, QCM, rendez-vous)
- `app/services/orchestrator.py` : point d'entrée de l'agent (stub, à remplacer par LangGraph)
- `app/agents` : futurs agents (profil, RAG, orientation, QCM, relance)

## Prochaines étapes

STT Whisper, ingestion RAG, graphe LangGraph, QCM, emails/calendrier, migrations Alembic.

## Routes ajoutées

| Route | Rôle |
|---|---|
| `GET /api/qcm/current` | QCM de la dernière pré-inscription (créé au besoin, sans corrigé) |
| `PUT /api/qcm/{id}/answers` | Enregistrer les réponses (`finish: true` pour terminer et noter) |
| `GET /api/qcm/{id}/results` | Bilan par thème |
| `GET /api/appointments/slots` | Créneaux de 30 min (jours ouvrés, heure de Tunis) |
| `POST /api/appointments` · `GET /me` · `DELETE /{id}` | Réserver, lister, annuler un entretien |
| `POST /api/documents` · `GET /api/documents` · `GET /{id}/file` | Dépôt PDF/JPG/PNG (10 Mo max), accès propriétaire ou équipe |

## Tests

Les tests utilisent SQLite en mémoire : pas besoin de PostgreSQL.

```bash
.venv\Scripts\python -m pip install -r requirements-dev.txt
.venv\Scripts\python -m pytest
```
