# SmartCampus AI - Backend (FastAPI)

## Lancer (Docker + PostgreSQL)

La base de données est **PostgreSQL** (plus de fichier SQLite). Depuis la racine du projet (`version2\SmartCampus`) :

```bash
docker compose up -d --build
```

| Service | URL |
|---|---|
| Frontend (React + nginx) | http://localhost:3100 |
| API FastAPI (docs) | http://localhost:8100/docs · santé : http://localhost:8100/health |
| PostgreSQL | localhost:5435 (base `smartcampus_v2`) |

Au démarrage (`ENV=dev`) l'API crée les tables et insère les formations d'exemple dans PostgreSQL.
Pour repartir de zéro : `docker compose down -v` (supprime aussi le volume de la base).

### Lancer l'API hors Docker (optionnel)

```bash
docker compose up -d db
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m uvicorn app.main:app --reload
```

`DATABASE_URL` dans `.env` pointe sur `localhost:5435`.
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


## API de gestion du catalogue (responsables académiques)

Le responsable IIT / ISB gère **uniquement les éléments de son établissement** ; l'administrateur gère tout. La lecture est publique pour les éléments actifs ; `include_inactive=true` (compte équipe) renvoie aussi les éléments désactivés.
Toutes les listes acceptent `limit` (1-200, défaut 100) et `offset` ; le total est renvoyé dans l'en-tête `X-Total-Count`.

| Ressource | Routes (`GET` liste · `GET /{id}` · `POST` · `PATCH /{id}` · `DELETE /{id}`) | Recherche `q` sur | Filtres |
|---|---|---|---|
| Formations | `/api/programs` | nom, description, conditions (texte) | `institution`, `level`, `min_duration_years`, `max_duration_years` |
| Spécialités | `/api/specialties` | nom, description | `program_id`, `institution` |
| Programmes pédagogiques | `/api/curricula` (le détail contient les matières) | nom, description | `program_id`, `specialty_id`, `institution`, `academic_year` |
| Matières | `/api/subjects` | nom, code, description | `curriculum_id`, `program_id`, `specialty_id`, `institution`, `semester`, `min_credits`, `max_credits` |
| Conditions d'admission | `/api/admission-conditions` | titre, description | `program_id`, `specialty_id` (+ `include_program_wide`), `institution`, `kind`, `required` |

Suppression : une formation, une spécialité ou un programme entraîne la suppression de ce qui en dépend (spécialités, programmes, matières, conditions). Une formation liée à des préinscriptions n'est pas supprimable (409) : la désactiver avec `PATCH {"active": false}`.
Les nouvelles tables sont créées au démarrage (`ENV=dev`) sans toucher aux données existantes.


## Mémoire de session (mémoire de travail temporaire de l'agent)

Objectif : l'agent comprend les questions suivantes (« et les débouchés ? », « je veux m'inscrire », « la licence en informatique ») sans redemander ce que le candidat a déjà dit. Le dossier durable reste ailleurs (`messages`, `candidate_profiles`, profil conversationnel dans `Conversation.state`) ; la mémoire de session ne contient que ce qui sert **maintenant**. Code : `app/services/session_memory.py`, branchée dans `app/services/orchestrator.py`.

| Élément conservé | Rôle |
|---|---|
| `turns` | derniers messages (utilisateur + agent), nettoyés et tronqués |
| `last_programs` | formations évoquées dans la dernière réponse (3 max) : ce que désignent « celle-ci », « et les débouchés ? » |
| `last_intent`, `last_action` | dernière demande comprise / dernière action de l'agent |
| `pending` | question posée au candidat ; une réponse courte (≤ 8 mots) reprend la demande interrompue (préinscription, comparaison) |

**Limites** (variables d'environnement, voir `.env.example`) : `SESSION_MAX_TURNS` (6 échanges), `SESSION_MAX_CHARS` (300 par message), `SESSION_MAX_BYTES` (8 Ko par mémoire). Emails et numéros (≥ 7 chiffres) sont masqués avant stockage ; les années scolaires (« 2026-2027 ») sont conservées.

**Expiration** : inactivité `SESSION_TTL_MINUTES` (30 min, prolongée à chaque message) et durée de vie absolue `SESSION_MAX_AGE_MINUTES` (4 h, jamais prolongée). Une mémoire expirée est ignorée, réinitialisée au message suivant, et purgée au démarrage, pendant les requêtes et par une tâche de fond toutes les `SESSION_PURGE_INTERVAL_SECONDS` (5 min).

**Visiteur sans compte** : rien n'est stocké côté serveur, la mémoire voyage avec le navigateur (`state.memory`) avec les mêmes limites. Elle porte deux horodatages, `born` (début) et `seen` (dernier message), et les mêmes deux expirations s'appliquent. Une mémoire expirée, sans horodatage ou avec des horodatages incohérents (futurs, texte) est abandonnée avec le profil de session qui l'accompagne, et `meta.memory.expires_in_seconds` indique le temps restant. Le navigateur renvoie ces horodatages, ils ne sont donc pas infalsifiables : un visiteur peut seulement garder son propre contexte plus longtemps. Tests : `tests/test_guest_endpoint.py`.

**Transparence et contrôle du candidat** :
- `GET /api/conversations/{id}/memory` : ce que l'agent retient, son expiration et les limites actives ;
- `DELETE /api/conversations/{id}/memory` : l'agent oublie (l'historique et le profil ne sont pas touchés).

Chaque réponse de l'agent expose `meta.memory` (`new`, `resumed`, `expires_in_seconds`) et la trace indique `memory=new|reused`. Tests : `tests/test_session_memory.py`.


## Données de démonstration

Au démarrage avec `ENV=dev`, `init_db()` crée les tables puis insère un jeu **fictif** (à remplacer par les contenus officiels IIT/ISB). L'insertion est idempotente : relancer le backend ne crée aucun doublon. Code : `app/seed.py` (formations, comptes) et `app/seed_catalog.py` (spécialités, programmes, matières, tarifs, conditions).

| Formation | Spécialités | Programmes | Matières | Frais | Modalités | Conditions |
|---|---|---|---|---|---|---|
| IIT · Licence en informatique | 3 | 4 | 26 | 4 | 2 | 6 |
| IIT · Cycle préparatoire | 0 | 2 | 17 | 2 | 2 | 4 |
| IIT · Parcours en ingénierie | 3 | 4 | 22 | 3 | 2 | 6 |
| ISB · Parcours en gestion | 3 | 4 | 23 | 3 | 2 | 4 |
| ISB · Parcours en finance | 3 | 4 | 23 | 3 | 2 | 4 |

Les frais, modalités et conditions du jeu sont publiés et valides depuis le 01/01/2026, donc visibles des candidats et de l'agent.

**Comptes responsables** : créés uniquement si `SEED_TEAM_PASSWORD` est défini dans `.env` (aucun mot de passe par défaut, le même mot de passe pour les cinq comptes, à ne jamais utiliser hors démonstration) :

| Rôle | Email |
|---|---|
| Administrateur | `admin@smartcampus.tn` |
| Responsable IIT | `iit@smartcampus.tn` |
| Responsable ISB | `isb@smartcampus.tn` |
| Responsable entretien | `entretien@smartcampus.tn` |
| Direction | `direction@smartcampus.tn` |

Un responsable ne gère que son établissement (IIT ou ISB) ; l'administrateur gère tout.

## Modèle LLM dérija (existant, sans fine-tuning)

L'agent reste déterministe pour tout ce qui compte (intentions, planification, outils, RAG, règles humain dans la boucle). Un modèle **existant** de dialecte tunisien reformule seulement la réponse déjà sourcée en dérija (écriture arabe) ou en Arabizi, avec les derniers échanges de la mémoire de session comme contexte. Code : `app/agents/llm.py`.

- **Modèle** (poids ouverts, base Qwen3-8B, arabe tunisien + Arabizi) : `ESPRIT-Group/ESPRIT-Derja-Qwen3-8B-v2`. Utilisé tel quel, sans fine-tuning. Variables : `LLM_ENABLED`, `LLM_BASE_URL` (endpoint compatible OpenAI, se terminant par `/v1`), `LLM_MODEL=ESPRIT-Group/ESPRIT-Derja-Qwen3-8B-v2`, `LLM_API_KEY`.
- **Garde-fous** : la reformulation n'est acceptée que si elle conserve tous les chiffres et noms de formations, reste dans la bonne écriture et reste courte ; sinon (modèle indisponible, délai dépassé, réponse infidèle) la réponse déterministe est envoyée. Les textes officiels (transfert vers un conseiller, consentement, préinscription créée) et le français ne passent jamais par le modèle.
- **Traçabilité** : `meta.llm` = `{used, model, fallback?}` sur chaque réponse, utile pour l'évaluation (comparer réponse déterministe / reformulée).
- Désactivé par défaut : sans modèle, l'application fonctionne comme avant.

### Avec Docker

Le modèle est un service optionnel `llm` de `docker-compose.yml` (image vLLM, profil `llm`) : la stack habituelle (`db`, `backend`, `frontend`) n'est pas modifiée.

1. Dans `backend/.env` : `LLM_ENABLED=true` (l'URL `http://llm:8000/v1` et le nom du modèle sont déjà fournis par le compose).
2. Lancer avec le profil : `docker compose --profile llm up -d --build`.
3. Premier démarrage : téléchargement des poids (~16 Go) dans le volume `smartcampusai_hf_cache`, puis chargement en GPU ; le service est prêt quand `docker compose ps` affiche `llm` en `healthy` (quelques minutes). Si le dépôt Hugging Face exige un accès, exporter `HF_TOKEN` avant le lancement.
4. L'API du modèle est aussi exposée sur `http://localhost:8200/v1` pour les tests (`/v1/models`, `/v1/chat/completions`).

Prérequis : GPU NVIDIA (~20 Go de VRAM en bf16) avec NVIDIA Container Toolkit, ou Docker Desktop avec le support GPU WSL2 sous Windows. Tant que le service `llm` n'est pas prêt, le backend répond avec ses réponses déterministes (repli automatique). Sans GPU, ne pas activer le profil et laisser `LLM_ENABLED=false`. Image épinglable via `VLLM_IMAGE`.


## Informations officielles : frais, modalités de paiement, conditions d'admission

Ces trois ressources d'une formation (ou d'une de ses spécialités) sont des **informations officielles** : chacune a un **statut de publication** et une **période de validité**. Les candidats et l'agent IA ne voient que ce qui est **publié ET valide aujourd'hui** (date de Tunis), sous une formation active.

| Ressource | Routes | Contenu |
|---|---|---|
| Frais de scolarité | `/api/fees` | libellé, montant, devise, périodicité (`annual`, `semester`, `one_time`) |
| Modalités de paiement | `/api/payment-terms` | mode (`bank_transfer`, `cash`, `cheque`, `card`, `online`, `other`), nombre de versements, acompte %, date limite, frais concerné (`fee_id`) |
| Conditions d'admission | `/api/admission-conditions` | type, titre, seuil (ex. moyenne), obligatoire ou non |

Chacune propose `GET` (liste filtrable + `X-Total-Count`), `GET /{id}`, `POST`, `PATCH`, `DELETE` et trois actions de statut : `POST /{id}/publish`, `/{id}/archive`, `/{id}/draft`. Lecture agrégée pour le front : `GET /api/programs/{id}/official-info[?specialty_id=]` (frais + paiement + conditions officiels, avec `complete` = ce qui n'est pas encore publié).

**Cycle de vie** : `draft` (brouillon, jamais visible) → `published` (officiel pendant sa période) → `archived` (retiré, conservé pour l'historique). Un nouvel élément est créé en brouillon (`status: "published"` accepté à la création pour publier directement).
- **Validité** : `valid_from` / `valid_until` (bornes vides = ouvertes) et `academic_year` (informatif). Un tarif dont la période est terminée ou pas commencée n'est jamais montré, sans intervention humaine.
- **Contenu modifié = à re-publier** : modifier un élément publié (hors `active`) le repasse en brouillon.
- **Pas de doublon de période** : deux éléments publiés de même formation / spécialité / libellé ne peuvent pas couvrir les mêmes jours (`409`). Le nouveau tarif prend le relais le lendemain de la fin de l'ancien, ou l'ancien est archivé. Publier une période déjà terminée est refusé (`422`).
- **Droits** : lecture publique des éléments officiels ; création, modification et changement de statut réservés au responsable de l'établissement de la formation (ou à l'administrateur).
- **Vue équipe** : `include_inactive=true` (compte équipe) ajoute brouillons, archivés, à venir et expirés de son établissement ; filtres `status=draft|published|archived` et `validity=current|upcoming|expired`.

**Agent IA** : il lit uniquement `services/official_info.py`. Nouvelles intentions *frais* et *paiement* (français, dérija, Arabizi) ; « frais d'inscription » n'est pas une demande d'inscription. Sans élément officiel valide, l'agent le dit et propose un conseiller (`no_source_handoff`) au lieu d'inventer. Chaque réponse expose `meta.official` (`as_of`, `kinds`, `complete`).

**Migration** : au démarrage, les tarifs et conditions déjà saisis sont conservés et passent en `published` ; les nouveaux démarrent en brouillon. Tests : `tests/test_official_info.py`.
