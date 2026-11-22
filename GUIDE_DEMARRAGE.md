# SmartCampus AI — Guide d’installation et de démarrage en local

Plateforme d’orientation IIT / ISB : un **frontend** React (Vite, port 3000) et un **backend** FastAPI (port 8000).
La base de données est **PostgreSQL** (avec l’extension **pgvector** pour l’index RAG lorsqu’elle est installée).

```
Navigateur ──► Frontend Vite :3000 ──(/api, /health)──► Backend FastAPI :8000 ──► PostgreSQL :5432 (base smartcampus)
```

---

## 1. Prérequis

| Outil | Version | Vérifier |
|---|---|---|
| Python | 3.11 ou plus | `python --version` |
| Node.js (avec npm) | 20 ou plus | `node --version` |
| PostgreSQL | 15 ou plus (installé, ou via Docker) | `psql --version` |
| Docker Desktop | optionnel (PostgreSQL en conteneur ou pile complète) | `docker --version` |

## 2. Préparer PostgreSQL

Le backend se connecte par défaut à :

```
postgresql+psycopg://smartcampus:smartcampus@localhost:5432/smartcampus
                     utilisateur  mot de passe  hôte    port  base
```

Choisissez **une** des deux options.

**Option A — PostgreSQL installé sur la machine** (par exemple le service Windows `postgresql-x64-17`).
Ouvrez *SQL Shell (psql)* ou pgAdmin avec le compte `postgres`, puis exécutez :

```sql
CREATE USER smartcampus WITH PASSWORD 'smartcampus';
CREATE DATABASE smartcampus OWNER smartcampus;
CREATE DATABASE smartcampus_test OWNER smartcampus;   -- pour les tests automatiques uniquement
```

Facultatif, pour l’index RAG : installer pgvector (https://github.com/pgvector/pgvector), puis, connecté à la base
`smartcampus` avec le compte `postgres` : `CREATE EXTENSION vector;`. Sans pgvector, le backend fonctionne et ignore
seulement la table `document_chunks`.

**Option B — PostgreSQL + pgvector dans Docker** : depuis `backend`, `docker compose up -d db`. L’utilisateur, le mot de
passe et la base `smartcampus` sont créés automatiquement. Base des tests :
`docker compose exec db createdb -U smartcampus smartcampus_test`. Le conteneur utilise le port 5432 : si un PostgreSQL installé
tourne déjà sur ce port, arrêtez son service, ou changez le port publié (`"5433:5432"`) et `DATABASE_URL` (`localhost:5433`).

Autre utilisateur, mot de passe ou port : modifiez `DATABASE_URL` dans `backend/.env`.
Vérifier la connexion : `cd backend` puis `.venv\Scripts\python -m app.cli check`.

## 3. Démarrage rapide (Windows)

PostgreSQL doit être démarré (section 2).

Depuis le dossier `SmartCampus` :

```bat
setup.bat
```

Installe tout une seule fois : environnement Python et dépendances du backend, fichier `backend\.env` avec une clé secrète
aléatoire, tables PostgreSQL avec les **données de démonstration**, puis dépendances du frontend (`npm ci`, versions exactes
du `package-lock.json`).

```bat
start.bat
```

Ouvre deux fenêtres (backend et frontend) puis le navigateur sur http://localhost:3000.

- Application : http://localhost:3000
- Documentation interactive de l’API : http://localhost:8000/docs
- Santé du backend : http://localhost:8000/health

## 4. Démarrage manuel (Windows, macOS, Linux)

Sous Windows `cmd`, utilisez des barres obliques inverses (`.venv\Scripts\python`). Sous PowerShell, préfixez par `.\`.
Sous macOS / Linux, remplacez `.venv\Scripts\python` par `.venv/bin/python`.

**Backend** (premier terminal) :

```bash
cd backend
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt -r requirements-dev.txt
.venv\Scripts\python -m app.cli init-env      # crée .env avec une clé secrète aléatoire
.venv\Scripts\python -m app.cli check         # vérifie la connexion à PostgreSQL
.venv\Scripts\python -m app.cli seed-demo     # tables + données de démonstration
.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
```

**Frontend** (second terminal) :

```bash
cd frontend
npm ci
npm run dev
```

Le serveur Vite envoie déjà `/api` et `/health` vers `http://localhost:8000` (`frontend/vite.config.ts`) : rien à configurer
côté frontend.

## 5. Configuration (`backend/.env`)

`backend/.env` est créé par `python -m app.cli init-env` (ou `setup.bat`) avec tous les paramètres et une clé secrète aléatoire. Les principaux :

| Paramètre | Rôle | Valeur locale |
|---|---|---|
| `ENV` | `dev` : crée les tables au démarrage | `dev` |
| `DATABASE_URL` | Connexion PostgreSQL | `postgresql+psycopg://smartcampus:smartcampus@localhost:5432/smartcampus` |
| `SECRET_KEY` | Signature des jetons de connexion (≥ 32 caractères, jamais commitée) | générée par `init-env` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Durée d’une connexion | `60` |
| `PASSWORD_MIN_LENGTH` | Longueur minimale des mots de passe (même règle que le frontend) | `12` |
| `SEED_DEMO_DATA` | Ajoute les données de démonstration au démarrage si absentes | `true` |
| `CORS_ORIGINS` | Origines autorisées à appeler l’API directement | `http://localhost:3000` |
| `GUEST_*` | Sessions visiteur : durées et limites (voir §8) | voir `backend/.env` |

`.env` n’est jamais commité (`.gitignore`). En production : `ENV=prod`, `SEED_DEMO_DATA=false`, une vraie clé secrète et un mot de passe PostgreSQL robuste.

## 6. Données de démonstration

Créées par `setup.bat`, `python -m app.cli seed-demo` ou au démarrage si `SEED_DEMO_DATA=true`. Personnes et montants **fictifs**.

**Mot de passe de tous les comptes de démonstration : `SmartCampus-Demo-2026`**

| Compte | Rôle | Arrive sur |
|---|---|---|
| `admin@demo.smartcampus.tn` | Administrateur | `/admin` |
| `iit.academique@demo.smartcampus.tn` | Responsable académique IIT | `/equipe/examen` |
| `isb.academique@demo.smartcampus.tn` | Responsable académique ISB | `/equipe/examen` |
| `entretien@demo.smartcampus.tn` | Responsable entretien | `/equipe/planning` |
| `direction@demo.smartcampus.tn` | Direction | `/direction` |
| `fatma.kchaou@demo.smartcampus.tn` | Candidate : QCM terminé, entretien confirmé | `/espace` |
| `aziz.trabelsi@demo.smartcampus.tn` | Candidat : QCM terminé, pas encore de rendez-vous | `/espace` |
| `mariem.kammoun@demo.smartcampus.tn` | Candidate ISB : pré-inscription envoyée, relais humain demandé | `/espace` |
| `sarra.ayadi@demo.smartcampus.tn` | Candidate : pré-inscription envoyée | `/espace` |
| `hedi.feki@demo.smartcampus.tn` | Candidat inscrit | `/espace` |

Catalogue : 5 formations (IIT : Licence en informatique, Cycle préparatoire, Parcours en ingénierie ; ISB : gestion, finance),
spécialités, programmes pédagogiques et matières, frais, modalités de paiement et conditions d’admission **publiés et en vigueur**,
plus un tarif et une condition en **brouillon** (invisibles des candidats).

Scénario de démonstration conseillé :
1. Visiteur : parcourir `/formations`, ouvrir une fiche (frais et conditions officiels), comparer.
2. `fatma.kchaou` : tableau de bord, résultats du QCM, rendez-vous confirmé, dépôt d’un document.
3. `iit.academique` : catalogue IIT (créer un tarif → brouillon → publier), statistiques limitées à l’IIT.
4. `entretien` : dossier d’entretien de Fatma (synthèse, QCM par thème, points à aborder).
5. `direction` : tableau de bord global IIT / ISB. 6. `admin` : comptes et rôles, catalogue complet.

## 7. Rôles et accès

| Rôle | Peut | Ne peut pas |
|---|---|---|
| Visiteur (sans compte) | lire le catalogue publié, discuter avec l’assistant (session visiteur) | données personnelles, candidature |
| Candidat | son profil, pré-inscription, QCM, rendez-vous, documents, ses conversations | rien de l’équipe |
| Responsable académique IIT / ISB | gérer le catalogue **de son établissement**, statistiques et dossiers de son établissement | l’autre établissement (lecture seule), comptes |
| Responsable entretien | dossiers prêts pour l’entretien | catalogue, statistiques |
| Direction | statistiques globales | dossiers individuels, catalogue |
| Administrateur | tout, dont comptes et rôles | supprimer le dernier administrateur actif |

- L’inscription publique crée **toujours** un compte candidat ; les rôles de l’équipe sont attribués par un administrateur.
- Un compte suspendu ne peut plus se connecter et ses jetons sont refusés immédiatement.
- Le rôle est relu en base à chaque requête : un changement de rôle s’applique sans reconnexion.
- Créer un administrateur sans passer par l’interface : `python -m app.cli create-admin --email vous@exemple.tn --name "Nom"`.

## 8. Sessions visiteur et conversation invitée (API)

Le chat reste ouvert sans compte. Le backend gère des **sessions visiteur temporaires** :

- **Création automatique** : un `POST /api/conversations` sans compte ni jeton crée une session et renvoie son jeton dans
  l’en-tête `X-Guest-Session` et dans `guest_session.token`. Le client renvoie cet en-tête à chaque appel suivant.
- **Identifiant et secret** : le jeton est `<identifiant>.<secret>` ; seule l’empreinte SHA-256 du secret est stockée.
- **Validité** : expire après `GUEST_IDLE_MINUTES` d’inactivité (prolongée à chaque message), et au plus tard
  `GUEST_MAX_HOURS` après sa création.
- **Limites** : `GUEST_MAX_MESSAGES` messages et `GUEST_MAX_CONVERSATIONS` conversations par session,
  `GUEST_MESSAGES_PER_MINUTE` messages par minute, `GUEST_SESSIONS_PER_HOUR_PER_CLIENT` nouvelles sessions par heure et par
  adresse réseau (seule une empreinte salée de l’adresse est conservée), `GUEST_MESSAGE_MAX_CHARS` caractères par message.
  Au-delà : erreur 429 (ou 422 pour un message trop long).
- **Expiration automatique** : une tâche de fond (toutes les `GUEST_PURGE_INTERVAL_MINUTES`) marque les sessions expirées,
  puis supprime, après `GUEST_RETENTION_HOURS`, celles qui n’ont pas été rattachées, avec leurs messages.
  Manuellement : `python -m app.cli purge-guests`.

| Appel | Rôle |
|---|---|
| `POST /api/conversations` | sans compte : crée la session (1re fois) et la conversation |
| `POST /api/conversations/{id}/messages` + `X-Guest-Session` | envoyer un message |
| `GET /api/guest/session` + `X-Guest-Session` | état : expiration, messages restants |
| `GET /api/guest/limits` | règles appliquées (pour les afficher) |
| `DELETE /api/guest/session` + `X-Guest-Session` | le visiteur efface sa session et ses conversations |

**Rattacher la conversation à un compte candidat** (après inscription ou connexion) :

1. `GET /api/guest/claim/preview` (Bearer candidat + `X-Guest-Session`) : ce qui serait conservé (nombre de messages,
   premier message, texte de consentement à afficher).
2. Si la personne accepte explicitement : `POST /api/guest/claim` avec `{"consent": true}` (Bearer + `X-Guest-Session`).
   La possession du jeton prouve que la session lui appartient ; `consent` doit valoir `true`, sinon erreur 400.
   La date du consentement est enregistrée. Les conversations passent sur le compte, avec tout leur historique.
3. Si elle refuse : `DELETE /api/guest/session` efface la conversation.

Seul un compte **candidat** peut rattacher une session ; une session expirée ou déjà rattachée est refusée (401 / 409).

> État actuel du frontend : le widget de chat affiche « connectez-vous » aux visiteurs sans appeler l’API, et ne propose pas
> encore le rattachement. Ces fonctions sont prêtes et testées côté backend ; il reste à brancher le chat dessus.

## 9. Commandes utiles (`backend`)

```bash
.venv\Scripts\python -m app.cli check               # connexion PostgreSQL, pgvector, état du schéma
.venv\Scripts\python -m app.cli seed-demo           # ajoute les données de démo (sans doublon)
.venv\Scripts\python -m app.cli reset-db --yes      # SUPPRIME toutes les données et recrée la base (+ --demo)
.venv\Scripts\python -m app.cli create-admin --email ... --name "..."
.venv\Scripts\python -m app.cli purge-guests
.venv\Scripts\python -m pytest                      # tests, sur la base PostgreSQL smartcampus_test
```

Les tests utilisent une base **dédiée** `smartcampus_test` (section 2), vidée et recréée à chaque lancement : vos données
de la base `smartcampus` ne sont jamais touchées. Autre adresse : variable `TEST_DATABASE_URL`, par exemple en PowerShell :

```powershell
$env:TEST_DATABASE_URL = "postgresql+psycopg://smartcampus:smartcampus@localhost:5433/smartcampus_test"
```

## 10. Option Docker

**Seulement PostgreSQL** : voir la section 2, option B.

**Pile complète** (base + backend + frontend), depuis le dossier `SmartCampus` :

```bash
docker compose up --build
```

Application sur http://localhost:8080 (nginx du frontend → `backend:8000`), API sur http://localhost:8000/docs,
données de démonstration incluses.
