# Architecture technique de SmartCampus AI

## 1. Présentation générale

SmartCampus AI est une plateforme intelligente d'orientation universitaire destinée aux futurs étudiants de l'IIT et de l'ISB.

L'architecture technique repose sur une séparation entre l'interface utilisateur, les services métier, les agents d'intelligence artificielle, les traitements automatiques et le stockage des données.

Cette organisation vise à faciliter la maintenance, la sécurité et l'évolution du système.

## 2. Diagramme d'architecture technique

Le diagramme suivant présente les composants techniques de SmartCampus AI et les principales communications entre eux.

![Architecture technique SmartCampus AI](architectureIA.drawio.svg)

## 3. Composants techniques et justification des choix

| Composant | Technologie | Rôle et justification |
|---|---|---|
| Frontend | React, Vite, TypeScript | Développement d'une interface interactive pour le chatbot, l'espace candidat et les tableaux de bord. |
| Backend | FastAPI, Python | Gestion des API REST, de l'authentification, des autorisations et des fonctionnalités métier. Python facilite l'intégration des outils IA. |
| Reverse Proxy | Nginx | Distribution des fichiers frontend et transmission des requêtes API au backend. HTTPS/TLS prévu pour le déploiement. |
| Base de données | PostgreSQL, pgvector | Stockage structuré des données métier et recherche vectorielle pour le RAG. |
| Orchestration agentique | LangGraph | Coordination des agents IA, gestion du dialogue et des différentes étapes du parcours candidat. |
| Modèle de langage | LLM open source | Compréhension des demandes et génération de réponses adaptées au français, au tunisien et à l'Arabizi. |
| Transcription audio | Whisper | Conversion des messages vocaux en texte pour leur traitement. |
| Recherche documentaire | RAG et embeddings | Recherche d'informations pertinentes dans les documents officiels IIT/ISB pour produire des réponses justifiées. |
| Stockage de fichiers | Stockage privé | Conservation des documents, justificatifs, PDF et fichiers audio. |
| Traitements automatiques | Celery, Redis, workers | Planification et exécution différée des tâches d'indexation, de relance et de notification. |
| Communication | SMTP ou API email | Envoi des confirmations, invitations et rappels autorisés. |

## 4. Architecture agentique

L'orchestration agentique proposée repose sur quatre agents spécialisés :

- **Agent RAG :** recherche les informations officielles relatives aux formations IIT et ISB.
- **Agent Profil :** collecte et analyse les informations scolaires, les intérêts et les préférences du candidat.
- **Agent Orientation :** compare les parcours et propose des recommandations justifiées.
- **Agent Parcours Candidat :** accompagne la préinscription, le QCM, les rendez-vous et le suivi du dossier.

Un superviseur LangGraph coordonne les étapes nécessaires selon la demande de l'utilisateur.

La mémoire conversationnelle conserve les informations utiles du dialogue et l'état d'avancement du candidat.

Un composant d'évaluation et de traçabilité permet de suivre les performances des agents, la qualité des réponses et les sources utilisées.

## 5. Communication entre les composants

Les principaux échanges sont organisés de la manière suivante :

1. **React → FastAPI :** transmission des requêtes via l'API REST.
2. **FastAPI ↔ PostgreSQL :** lecture et enregistrement des données métier.
3. **FastAPI → LangGraph :** déclenchement des traitements agentiques.
4. **Agents IA ↔ LLM :** compréhension et génération des réponses.
5. **Agent RAG ↔ pgvector :** recherche vectorielle dans les documents indexés.
6. **FastAPI ↔ Stockage privé :** dépôt et consultation des fichiers autorisés.
7. **FastAPI / Celery Beat → Redis → Workers :** déclenchement et distribution des tâches différées.
8. **Workers → Service email :** envoi des notifications après vérification des règles métier.

Les responsables académiques et les responsables d'entretien conservent la responsabilité des décisions officielles d'admission.

## 6. Sécurité et contrôle

L'architecture prévoit les mécanismes suivants :

- Authentification par JWT et contrôle des accès selon les rôles (RBAC).
- Validation des données avec Pydantic.
- Protection des documents et des données personnelles.
- Gestion du consentement avant les actions qui le nécessitent.
- Traçabilité des opérations et des traitements IA.
- Validation humaine des décisions officielles.

## 7. État de l'architecture

Cette architecture représente la **conception cible de SmartCampus AI**.

Le projet dispose déjà d'un socle React/Vite et FastAPI, avec SQLite utilisé par défaut en développement local.

PostgreSQL avec pgvector est prévu pour les données et la recherche documentaire. Les intégrations complètes de LangGraph, Whisper, Celery, Redis et des autres services IA restent à développer ou à confirmer avec l'équipe.

## 8. Conclusion

Cette architecture permet de séparer les responsabilités techniques et métier de SmartCampus AI.

Elle constitue une base structurée pour le développement progressif de la plateforme, l'intégration des agents IA et la gestion sécurisée du parcours d'orientation et de préinscription.
