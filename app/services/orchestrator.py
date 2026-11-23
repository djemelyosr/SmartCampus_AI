"""Entry point to the agentic layer.

Placeholder: replace with the LangGraph supervisor (language detection, profile extraction, RAG,
orientation, QCM, scheduling, human-in-the-loop). The API layer only depends on run_agent(), so the graph
can be swapped in without touching the routes. `user` is None for visitors chatting without an account.

Reply contract (read by the frontend chat): {"content": str, "meta": {"sources"?: [str], "replies"?: [str],
"handoff"?: bool, ...}}.
"""

from sqlalchemy.orm import Session

from app.models.models import Conversation, User


def run_agent(db: Session, conv: Conversation, user: User | None, text: str) -> dict:
    who = "visitor" if user is None else user.role.value
    return {
        "content": (
            "Merci pour votre message. L’assistant d’orientation n’est pas encore branché sur ce serveur : "
            "vous pouvez dès maintenant explorer et comparer les formations IIT et ISB."
        ),
        "meta": {"agent": "stub", "audience": who, "replies": ["Voir les formations", "Comparer Licence et Prépa"]},
    }
