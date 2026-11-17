"""Entry point to the agentic layer.

Placeholder: replace with the LangGraph supervisor (language detection, profile
extraction, RAG, orientation, QCM, scheduling, human-in-the-loop). The API layer
only depends on run_agent(), so the graph can be swapped in without touching routes.
"""

from sqlalchemy.orm import Session

from app.models.models import Conversation, User


def run_agent(db: Session, conv: Conversation, user: User, text: str) -> dict:
    return {
        "content": "Agent not implemented yet.",
        "meta": {"echo": text, "agent": "stub"},
    }
