# Architecture technique de SmartCampus AI

## 1. Présentation générale

SmartCampus AI est une plateforme intelligente d'orientation universitaire destinée aux futurs étudiants de l'Institut International de Technologie (IIT) et de l'International School of Business (ISB).

L'architecture technique repose sur une séparation entre l'interface utilisateur, les services métier, les agents d'intelligence artificielle, les traitements automatiques et le stockage des données.

Cette organisation vise à faciliter la maintenance, la sécurité, l'évolutivité et l'intégration progressive des fonctionnalités intelligentes.

## 2. Diagramme d'architecture technique

Le diagramme suivant présente l'architecture technique cible de SmartCampus AI, les principaux composants du système et leurs communications.

![Architecture technique SmartCampus AI](architectureIA.drawio.svg)

## 3. Composants techniques et justification des choix

| Composant | Technologie | Rôle et justification |
|---|---|---|
| Frontend | React, Vite, TypeScript | Développement des interfaces du chatbot, de l'espace candidat et des tableaux de bord. React facilite la création de composants réutilisables, tandis que Vite simplifie le développement et la compilation. |
| Backend | FastAPI, Python | Gestion des API REST, de l'authentification, des autorisations et des services métier. Python facilite l'intégration avec les bibliothèques d'intelligence artificielle. |
| Reverse Proxy | Nginx | Distribution des fichiers frontend et transmission des requêtes API vers FastAPI. HTTPS/TLS reste à configurer pour le déploiement. |
| Base de données | PostgreSQL, SQLAlchemy | Stockage des comptes, profils, formations, préinscriptions, QCM et rendez-vous. PostgreSQL assure la gestion des données relationnelles et des transactions. |
| Recherche vectorielle | pgvector | Extension de PostgreSQL permettant de stocker les embeddings et d'effectuer des recherches par similarité pour le RAG. |
| Orchestration agentique | LangGraph (cible) | Coordination des agents IA, gestion de l'état conversationnel et intégration des étapes nécessitant une intervention humaine. |
| Modèle de langage | LLM open source (à sélectionner) | Compréhension des demandes et génération de réponses adaptées au contexte universitaire, avec une évaluation spécifique du français, du tunisien et de l'Arabizi. |
| Transcription audio | Whisper (prévu) | Conversion des messages vocaux en texte. La précision sur le dialecte tunisien devra être évaluée. |
| Recherche documentaire | RAG et modèle d'embeddings | Recherche des informations pertinentes dans les documents officiels IIT/ISB pour produire des réponses contextualisées et justifiées. |
| Stockage documentaire | Fichiers privés | Conservation des PDF, justificatifs et documents. Le dossier local `uploads/` est actuellement utilisé ; MinIO ou Amazon S3 constituent des évolutions possibles. |
| Traitements automatiques | Celery, Redis et workers (prévus) | Planification, distribution et exécution différée des opérations longues, notamment l'indexation documentaire et les relances. |
| Notifications | SMTP ou API email (prévu) | Envoi des confirmations, invitations et rappels selon les règles métier et les autorisations applicables. |

## 4. Architecture agentique

L'architecture agentique proposée repose sur **quatre agents spécialisés**, coordonnés par un superviseur LangGraph.

| Agent | Responsabilité |
|---|---|
| Agent RAG | Rechercher les informations officielles des formations IIT et ISB et fournir des références documentaires. |
| Agent Profil | Collecter et analyser les résultats scolaires, les intérêts et les préférences du candidat. |
| Agent Orientation | Comparer les parcours selon le profil, les prérequis et les règles d'orientation. |
| Agent Parcours Candidat | Accompagner les étapes de préinscription, de QCM, de rendez-vous et de suivi du dossier. |

Dans l'architecture cible, le **superviseur LangGraph** coordonnera les agents selon la demande du candidat et les étapes nécessaires.

Les agents pourront partager une mémoire et un état conversationnel contenant l'historique utile, le profil du candidat et son étape actuelle. La persistance de ces informations devra être configurée selon les besoins et les règles de conservation.

Un composant d'**évaluation et de traçabilité IA** permettra de suivre les erreurs, les sources documentaires, la qualité des réponses et les performances multilingues.

Les agents proposent des actions, mais leur exécution reste soumise aux contrôles des services métier. Les décisions officielles d'admission relèvent des responsables humains habilités.

## 5. Communication entre les composants

Les principaux échanges de l'architecture sont les suivants :

1. **Frontend React ↔ Backend FastAPI :** communication via des API REST et échange des données au format JSON. HTTPS est prévu pour le déploiement.
2. **Nginx → FastAPI :** transmission des requêtes API au serveur backend.
3. **FastAPI ↔ PostgreSQL :** lecture, création et mise à jour des données métier à travers SQLAlchemy.
4. **FastAPI → Orchestrateur LangGraph :** déclenchement des traitements agentiques prévus pour les conversations et l'orientation.
5. **Orchestrateur ↔ LLM :** analyse des messages et génération des réponses.
6. **Agent RAG ↔ PostgreSQL/pgvector :** recherche des documents pertinents à partir des représentations vectorielles.
7. **FastAPI ↔ Stockage privé :** dépôt et consultation des documents après contrôle des autorisations.
8. **FastAPI ou Celery Beat → Redis → Workers :** distribution et exécution des tâches différées dans l'architecture cible.
9. **Workers → Service email :** envoi des notifications et rappels autorisés.

Les interactions avec les modèles IA, la file de tâches et les services de notification correspondent aux intégrations prévues.

## 6. Sécurité, consentement et traçabilité

Plusieurs mécanismes de sécurité sont déjà intégrés au backend :

- **Authentification JWT :** identification des utilisateurs connectés.
- **Contrôle d'accès RBAC :** limitation des opérations selon les rôles.
- **Restrictions par établissement :** mécanismes permettant de limiter certaines opérations des responsables académiques au périmètre IIT ou ISB.
- **Validation Pydantic :** vérification des données reçues par les API.

L'architecture prévoit également :

- Le chiffrement des communications externes avec HTTPS/TLS.
- La protection des documents privés et des informations personnelles.
- La vérification du consentement lorsque celui-ci est nécessaire.
- La journalisation des traitements et des événements importants.
- La traçabilité des sources utilisées par le RAG.
- La validation humaine des décisions officielles.

Ces mécanismes devront être complétés et testés au fur et à mesure du développement.

## 7. État actuel et évolutions prévues

L'architecture présentée représente la **conception cible de SmartCampus AI**. Certains composants existent déjà, tandis que d'autres restent à intégrer.

| Composant | État |
|---|---|
| React, Vite et TypeScript | Socle frontend présent |
| FastAPI et SQLAlchemy | Socle backend présent |
| Authentification JWT et contrôle RBAC | Mécanismes implémentés |
| Restriction des accès par établissement | Mécanismes présents dans le backend |
| Nginx | Configuration de reverse proxy présente ; TLS à compléter |
| SQLite | Base utilisée par défaut en développement local |
| PostgreSQL + pgvector | Pris en charge en option ; indexation RAG complète à finaliser |
| LangGraph et agents spécialisés | Architecture cible à implémenter |
| Whisper et LLM open source | Intégrations et évaluations prévues |
| Celery, Redis et workers | Solutions proposées, à confirmer avec l'équipe |
| Stockage privé | Dossier `uploads/` actuel ; MinIO/S3 possibles ultérieurement |

Les technologies cibles seront progressivement intégrées et validées selon les priorités du projet.

## 8. Conclusion

L'architecture technique de SmartCampus AI est conçue autour d'une séparation claire entre le frontend, le backend, les services métier, les composants IA, les traitements automatiques et le stockage.

Les choix technologiques visent à assurer une application modulaire, maintenable et évolutive, tout en permettant l'intégration progressive d'un système agentique d'orientation universitaire.

Cette architecture constitue une base de conception pour le développement, l'évaluation et l'amélioration continue de SmartCampus AI.
