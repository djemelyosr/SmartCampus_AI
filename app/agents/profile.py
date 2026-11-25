"""Candidate profile extraction + conversational memory (stored in Conversation.state["profile"])."""

import re

from sqlalchemy.orm import Session

from app.agents.language import concepts_in, norm
from app.models.models import CandidateProfile, Conversation, User

SUBJECT_CONCEPTS = {"maths", "physique", "informatique"}
INTEREST_CONCEPTS = {"informatique", "ia_data", "gestion", "finance", "ingenierie"}
STYLE_CONCEPTS = {"pratique", "progressif"}
TRACK_CONCEPTS = {"prepa", "licence", "ingenierie"}
GOAL_WORDS = ("veux", "vise", "reve", "devenir", "objectif", "projet pro", "metier", "nheb", "n7eb", "nehb", "nokhdem", "نحب", "نخدم", "نولي")
_BAC = re.compile(r"\bbac(?:calaureat)?\s*(math\w*|info\w*|sciences?(?:\s*exp\w*)?|tech\w*|eco\w*|lettres|sport)", re.I)
_LEVEL_WORDS = {"lycee": "Lycée", "terminale": "Terminale", "bachelier": "Bachelier", "licence": None, "prepa": None}


def empty() -> dict:
    return {"subjects": [], "interests": [], "goal": [], "style": [], "level": None, "tracks": [], "asked": [], "chosen_program": None, "shortlist": []}


def _merge(lst: list, items) -> bool:
    new = [i for i in items if i not in lst]
    lst.extend(new)
    return bool(new)


def extract(profile: dict, text: str) -> dict:
    """Update `profile` in place from a user message. Returns what changed (for tracing)."""
    cs = set(concepts_in(text))
    t = norm(text)
    changed: dict = {}
    for key, pool in (("subjects", SUBJECT_CONCEPTS), ("interests", INTEREST_CONCEPTS), ("style", STYLE_CONCEPTS), ("tracks", TRACK_CONCEPTS)):
        if _merge(profile[key], sorted(cs & pool)):
            changed[key] = sorted(cs & pool)
    if any(w in t for w in GOAL_WORDS) and cs & (INTEREST_CONCEPTS | {"ingenierie"}):
        if _merge(profile["goal"], sorted(cs & (INTEREST_CONCEPTS | {"ingenierie"}))):
            changed["goal"] = sorted(cs & INTEREST_CONCEPTS)
    m = _BAC.search(text)
    if m:
        profile["level"] = f"Bac {m.group(1).lower()}"
        changed["level"] = profile["level"]
    else:
        for w, label in _LEVEL_WORDS.items():
            if label and w in t and not profile.get("level"):
                profile["level"] = label
                changed["level"] = label
    return changed


def completeness(profile: dict) -> int:
    """How many of the 4 slots (subjects, interests/goal, level, style) are known."""
    return sum(bool(x) for x in (profile["subjects"], profile["interests"] or profile["goal"], profile["level"], profile["style"]))


def next_missing(profile: dict) -> str | None:
    for slot, ok in (
        ("subjects", bool(profile["subjects"])),
        ("goal", bool(profile["interests"] or profile["goal"])),
        ("level", bool(profile["level"])),
        ("style", bool(profile["style"])),
    ):
        if not ok and slot not in profile["asked"]:
            return slot
    return None


def sync_to_db(db: Session, user: User, profile: dict) -> None:
    """Mirror the conversational profile into CandidateProfile (never touches consent)."""
    p = user.profile
    if p is None:
        p = CandidateProfile(user_id=user.id)
        db.add(p)
        user.profile = p
    if profile["level"]:
        p.school_level = profile["level"]
    p.favorite_subjects = sorted(set(p.favorite_subjects or []) | set(profile["subjects"]))
    p.interests = sorted(set(p.interests or []) | set(profile["interests"]))
    if profile["goal"]:
        p.career_goal = ", ".join(profile["goal"])
    cons = dict(p.constraints or {})
    if profile["style"]:
        cons["style"] = profile["style"]
    p.constraints = cons
