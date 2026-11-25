# SmartCampus AI — Spécification des API REST

**Périmètre :** candidats, conversations et documents.  
**Architecture :** React, FastAPI, PostgreSQL + pgvector.  
**Base URL :** `/api/v1`.

Ce document propose le contrat des API à développer à partir des deux pages du diagramme `architectureSmart.drawio.svg`. Il ne décrit pas nécessairement les routes déjà implémentées.

## 1. Utilisateurs et autorisations

| Rôle | Autorisations dans ce périmètre |
|---|---|
| Visiteur (V) | Utiliser le chatbot public, uniquement dans sa propre session anonyme. |
| Candidat (C) | Gérer son profil, ses consentements, ses dossiers, ses conversations et ses pièces justificatives. |
| Responsable IIT/ISB (R) | Consulter les dossiers transmis, les profils et pièces nécessaires à leur traitement ; valider les dossiers ; gérer les sources officielles autorisées. |
| Direction (D) | Accéder aux indicateurs agrégés (API hors périmètre) ; aucun accès individuel par défaut. |
| Administrateur (A) | Gérer les sources officielles ; aucun accès automatique aux dossiers, aux documents personnels ni aux conversations privées. |

**Règles communes :** JWT Bearer pour les comptes authentifiés ; jeton de session anonyme distinct pour les visiteurs. `C` désigne le propriétaire de la ressource ; `R` désigne un responsable habilité pour l'établissement et, si applicable, le dossier concerné. FastAPI vérifie ces droits à chaque requête. L'inscription, la connexion, le renouvellement et la déconnexion relèvent du module d'authentification, prérequis non détaillé ici. Le profil candidat est créé lors de l'inscription.

## 2. API de gestion des candidats

### 2.1 Profil et consentements

| Méthode et endpoint | Données reçues | Réponse attendue | Accès | Erreurs spécifiques |
|---|---|---|---|---|
| `GET /candidates/me` | — | `200` Profil personnel | C | `404` Profil absent |
| `PATCH /candidates/me` | `phone`, `education`, `interests`, `preferences`, `preferred_language` (champs facultatifs) | `200` Profil modifié | C | `422` Données invalides |
| `GET /candidates/{candidate_id}` | Identifiant du candidat | `200` Profil utile à l'instruction du dossier | R | `404` Profil inaccessible |
| `GET /candidates/me/consents` | — | `200` Liste des consentements | C | `401` Session invalide |
| `PUT /candidates/me/consents/{purpose}` | `granted`, `notice_version` | `200` Consentement enregistré | C | `422` Finalité inconnue ; `409` Notice obsolète |

**Données du profil :** `id`, `full_name`, `email`, `phone`, `education` (niveau, diplôme, spécialité, moyenne, barème, année), `interests[]`, `preferences`, `preferred_language`, `updated_at`.

**Consentement :** `purpose`, `granted` (booléen), `notice_version`, `updated_at`. Finalités proposées : préinscription (`APPLICATION_SUBMISSION`), partage (`DATA_SHARING`), rappels (`REMINDERS`). Le retrait bloque les usages futurs correspondants, sous réserve des obligations applicables. Les règles exactes sont à valider avec les établissements.

### 2.2 Dossiers de préinscription

| Méthode et endpoint | Données reçues | Réponse attendue | Accès | Erreurs spécifiques |
|---|---|---|---|---|
| `POST /applications` | `program_id` | `201` Dossier créé en `DRAFT` | C | `404` Formation indisponible ; `409` Dossier actif existant |
| `GET /applications` | Filtres facultatifs : `status`, `institution_id`, `program_id` | `200` Liste des dossiers autorisés | C, R | `422` Filtre invalide |
| `GET /applications/{application_id}` | Identifiant du dossier | `200` Détail du dossier et de ses pièces | C, R | `404` Dossier inaccessible |
| `PATCH /applications/{application_id}` | `motivation`, `additional_information` (facultatifs) | `200` Dossier modifié | C | `409` Dossier verrouillé ; `422` Données invalides |
| `POST /applications/{application_id}/submit` | Aucun corps | `200` Dossier `SUBMITTED` | C | `403` Consentement absent ; `409` Statut incompatible ; `422` Dossier incomplet |
| `POST /applications/{application_id}/withdraw` | `reason` (facultatif) | `200` Dossier `WITHDRAWN` | C | `409` Retrait impossible |
| `POST /applications/{application_id}/review` | `action` : `START_REVIEW` ou `REQUEST_CHANGES` ; `comment` si correction demandée | `200` Dossier `UNDER_REVIEW` ou `CHANGES_REQUESTED` | R | `409` Transition impossible ; `422` Commentaire requis |
| `POST /applications/{application_id}/decision` | `decision` : `ACCEPTED` ou `REJECTED` ; `reason` | `200` Dossier avec décision officielle | R | `409` Statut ou prérequis incompatibles ; `422` Décision/justification invalide |

**Données du dossier :** `id`, `candidate_id`, `program_id`, `institution_id`, `status`, `motivation`, `additional_information`, `created_at`, `updated_at`, `submitted_at`, `decision` (ou `null`), `review_comment` (ou `null`). La décision contient `status`, `reason`, `decided_at` ; l'identité du responsable est conservée côté serveur.

Le serveur déduit le candidat du JWT et l'établissement de la formation. Un dossier est modifiable en `DRAFT` ou `CHANGES_REQUESTED`. Le responsable ne voit pas les brouillons privés. La soumission vérifie les pièces obligatoires et les consentements ; la décision officielle nécessite une instruction humaine et les étapes obligatoires du parcours (QCM, entretien, si requis). Les agents IA ne décident jamais de l'admission. Les API des formations, QCM et rendez-vous sont hors périmètre ici.

## 3. API de gestion des conversations

| Méthode et endpoint | Données reçues | Réponse attendue | Accès | Erreurs spécifiques |
|---|---|---|---|---|
| `POST /conversations` | `language`, `title` (facultatifs) | `201` Conversation créée ; jeton anonyme si nouvelle session visiteur | V, C | `429` Quota dépassé |
| `GET /conversations` | Pagination | `200` Liste des conversations du candidat | C | `401` Session invalide |
| `GET /conversations/{conversation_id}/messages` | Identifiant, pagination | `200` Historique chronologique des messages | V, C | `404` Conversation inaccessible |
| `POST /conversations/{conversation_id}/messages` | `content`, `language` (facultatif) | `201` Message utilisateur et réponse IA | V, C | `422` Message vide/invalide ; `429` Quota ; `503` IA indisponible |
| `POST /conversations/{conversation_id}/audio` | `file` audio, `language` (facultatif), multipart | `201` Transcription, message utilisateur et réponse IA | V, C | `413` Taille ; `415` Format ; `422` Audio illisible ; `503` Whisper/IA indisponible |
| `DELETE /conversations/{conversation_id}` | Identifiant | `204` Conversation retirée de l'historique accessible | V, C | `404` Conversation inaccessible |

**Conversation :** `id`, `title`, `language`, `created_at`, `updated_at`. À la création, la réponse contient `conversation` et, pour une nouvelle session visiteur, `anonymous_session_token`, `expires_in` (secondes).

**Message :** `id`, `conversation_id`, `role` (`USER` ou `ASSISTANT`), `content`, `language`, `citations[]`, `proposed_actions[]`, `created_at`. Une citation contient `document_id`, `title`, `page` (si connue), `source_url` (si disponible), `excerpt`. Une action proposée contient `type`, `parameters`.

**Exemple — envoyer un message**

`POST /api/v1/conversations/{conversation_id}/messages`

```json
{
  "content": "Quelles formations propose l'IIT ?",
  "language": "fr"
}
```

Réponse `201 Created` : objet contenant `user_message`, `assistant_message`, `transcription` (`null` pour le texte), `request_id`. Les deux messages suivent le modèle ci-dessus.

Le texte ou l'audio transcrit est traité par l'assistant IA. Le RAG s'appuie sur les sources officielles actives et indexées ; en l'absence de source pertinente, l'assistant le signale. Les actions proposées par l'IA ne contournent ni les autorisations ni le consentement. Un visiteur n'accède qu'aux conversations de sa propre session valide, sans accès aux dossiers. Le texte peut être en français, tunisien ou Arabizi ; la transcription audio et l'orchestration LangGraph correspondent à la cible du diagramme.

## 4. API de gestion des documents

### 4.1 Documents privés des candidats

| Méthode et endpoint | Données reçues | Réponse attendue | Accès | Erreurs spécifiques |
|---|---|---|---|---|
| `POST /applications/{application_id}/documents` | `file`, `type` (multipart) | `201` Métadonnées de la pièce créée | C | `409` Dossier verrouillé ; `413` Taille ; `415` Format ; `422` Fichier invalide |
| `GET /applications/{application_id}/documents` | `type` (facultatif) | `200` Liste des pièces et états de validation | C, R | `404` Dossier inaccessible |
| `GET /documents/{document_id}/download` | Identifiant | `200` Contenu binaire du fichier | C, R | `404` Pièce inaccessible ; `409` Fichier non disponible |
| `DELETE /documents/{document_id}` | Identifiant | `204` Pièce retirée du dossier | C | `404` Pièce inaccessible ; `409` Dossier verrouillé |

**Données retournées :** `id`, `application_id`, `type`, `filename`, `mime_type`, `size_bytes`, `validation_status` (`PENDING`, `AVAILABLE`, `REJECTED`), `uploaded_at`, `error_code` (ou `null`). Types proposés : `DIPLOMA`, `TRANSCRIPT`, `CV`, `OTHER`.

Les fichiers sont privés, leurs métadonnées sont dans PostgreSQL. Seuls les fichiers validés sont téléchargeables et satisfont les exigences du dossier. Les pièces sont modifiables uniquement lorsque le dossier le permet. Les formats (PDF, JPEG, PNG) et la limite de 10 Mio sont des choix proposés et configurables. Vérifier le type réel, la taille et la sécurité du fichier. Ne jamais exposer son chemin interne ni indexer une pièce personnelle dans le RAG public.

### 4.2 Documents officiels et RAG

| Méthode et endpoint | Données reçues | Réponse attendue | Accès | Erreurs spécifiques |
|---|---|---|---|---|
| `POST /knowledge/documents` | `file`, `title`, `institution_id`, `category`, `source_url` et `published_at` (facultatifs pour les deux derniers), multipart | `202` Document enregistré, indexation planifiée | R, A | `413` Taille ; `415` Format ; `422` Données invalides ; `503` Tâche non enregistrable |
| `GET /knowledge/documents` | Filtres facultatifs : `institution_id`, `category`, `index_status` | `200` Liste des documents autorisés | R, A | `422` Filtre invalide |
| `GET /knowledge/documents/{document_id}` | Identifiant | `200` Métadonnées et état d'indexation | R, A | `404` Document inaccessible |
| `POST /knowledge/documents/{document_id}/reindex` | Aucun corps | `202` Réindexation planifiée | R, A | `409` Indexation en cours ou document archivé ; `503` Tâche non enregistrable |
| `DELETE /knowledge/documents/{document_id}` | Identifiant | `204` Document archivé et exclu du RAG | R, A | `404` Document inaccessible |

**Données retournées :** `id`, `institution_id`, `title`, `category`, `source_url`, `published_at`, `index_status` (`PENDING`, `PROCESSING`, `INDEXED`, `FAILED`), `active`, `created_at`, `indexed_at`, `error_code` (ou `null`). Catégories proposées : `PROGRAMS`, `FAQ`, `ADMISSION_RULES`, `OTHER`.

Les sources publiques officielles (PDF, FAQ importées en texte, programmes, règles d'admission) sont vérifiées avant import. Le worker RAG extrait et découpe les textes, calcule les embeddings puis les indexe dans pgvector. L'API renvoie `202` seulement après enregistrement durable du document et de la demande de traitement ; le client consulte ensuite `GET /knowledge/documents/{document_id}`. Seuls les documents actifs et indexés alimentent le chatbot. L'archivage les exclut immédiatement de la recherche. Une nouvelle version peut être importée puis l'ancienne archivée après indexation réussie.

## 5. Gestion commune des erreurs et conventions

| Code HTTP | Signification |
|---|---|
| `200` | Consultation ou modification réussie |
| `201` | Ressource créée |
| `202` | Traitement accepté, pas encore terminé |
| `204` | Succès sans corps de réponse |
| `401` | Authentification absente, expirée ou invalide |
| `403` | Rôle, permission ou consentement insuffisant |
| `404` | Ressource absente ou non accessible individuellement |
| `409` | Conflit : doublon, état incompatible ou traitement en cours |
| `413` / `415` | Fichier trop volumineux / type de contenu non accepté |
| `422` | Données invalides ou exigences de validation non satisfaites |
| `429` | Limite de requêtes dépassée |
| `500` / `503` | Erreur interne / service temporairement indisponible |

Les erreurs d'authentification, d'autorisation, de validation et les erreurs serveur s'appliquent transversalement selon la route. Format JSON commun proposé (gestionnaire d'erreurs FastAPI à configurer) :

```json
{
  "error": {
    "code": "DOCUMENT_REQUIRED",
    "message": "Une pièce obligatoire est manquante.",
    "details": [{"field": "documents", "reason": "TRANSCRIPT"}],
    "request_id": "req_124"
  }
}
```

Exemple : `422` lors de la soumission d'un dossier incomplet.

- JSON par défaut ; `multipart/form-data` pour les fichiers et l'audio ; contenu binaire pour le téléchargement.
- Identifiants UUID générés côté serveur ; dates ISO 8601 en UTC. Les listes sont paginées (`page=1&size=20`, maximum 100) et renvoient `items`, `page`, `size`, `total`.
- HTTPS, validation Pydantic, contrôle du propriétaire et de l'établissement côté serveur. Réponses privées non mises en cache (`Cache-Control: no-store`). Aucun mot de passe, chemin privé ou détail technique sensible dans les réponses.
- `Idempotency-Key` pour les créations de dossiers, soumissions, messages/audio, uploads et décisions afin d'éviter les doublons lors des relances. Une même clé avec un contenu différent retourne `409`. Les opérations sensibles sont journalisées.

## 6. Synthèse et limites

| Module | Nombre d'opérations |
|---|---:|
| Candidats : profils, consentements et dossiers | 13 |
| Conversations | 6 |
| Documents privés et officiels | 9 |
| **Total** | **28** |

FastAPI constitue le point d'entrée des API. LangGraph, Whisper, le LLM, pgvector, Redis et Celery restent des composants internes : aucune API publique dédiée n'est nécessaire. Le diagramme présente LangGraph, Whisper, l'ingestion RAG complète et les automatisations comme des évolutions prévues. Les routes, champs, permissions détaillées et statuts proposés sont à valider avec l'équipe et les établissements avant implémentation ; aucune exécution du backend n'a été vérifiée dans ce document.
