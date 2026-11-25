"""Retrieval over the official IIT/ISB corpus (Program catalogue + DocumentChunk when the table exists).

Keyword/concept scoring (no external service needed). pgvector similarity can be added in `retrieve()`
by embedding the query and ordering DocumentChunk by cosine distance; the return shape stays the same.
"""

from sqlalchemy import inspect, select
from sqlalchemy.orm import Session

from app.agents.language import concepts_in, tokens
from app.models.models import DocumentChunk, Program

STOP = {"le", "la", "les", "de", "des", "du", "un", "une", "et", "en", "pour", "je", "tu", "est", "ce", "que", "qui", "quoi", "dans", "sur", "au", "aux", "a", "d", "l", "el", "w", "fi", "mta3"}
FIELDS = ("description", "admission_requirements", "duration", "careers")


def program_tags(p: Program) -> set[str]:
    txt = f"{p.name} {p.description} {' '.join(p.career_outcomes or [])}"
    tags = set(concepts_in(txt))
    tags.add(p.level.value)
    if p.level.value == "prepa":
        tags |= {"maths", "physique", "progressif"}
    if p.level.value == "ingenierie":
        tags |= {"ingenierie", "maths"}
    if p.institution.value == "IIT":
        tags |= {"informatique"} if p.level.value in ("licence", "ingenierie") else set()
    return tags


def program_passages(p: Program) -> dict[str, str]:
    outs = ", ".join(p.career_outcomes or []) or "Non renseigné"
    dur = f"{p.duration_years} an(s)" if p.duration_years else "Durée à confirmer auprès de l’établissement"
    return {
        "description": p.description or "",
        "admission_requirements": p.admission_requirements or "À confirmer auprès de l’établissement.",
        "duration": dur,
        "careers": outs,
    }


def source_label(p: Program) -> str:
    return f"{p.institution.value} · {p.name}"


def retrieve(db: Session, query: str, limit: int = 3) -> list[dict]:
    """Return [{source, program_id, name, text, score}] best first. Empty list = no sourced answer (never invent)."""
    q = {t for t in tokens(query) if t not in STOP and len(t) > 2} | set(concepts_in(query))
    out: list[dict] = []
    for p in db.scalars(select(Program).where(Program.active.is_(True))).all():
        hay = set(tokens(f"{p.name} {p.description} {' '.join(p.career_outcomes or [])}")) | program_tags(p)
        score = len(q & hay) + (3 if any(t in set(tokens(p.name)) for t in q) else 0)
        if score:
            out.append({"source": source_label(p), "program_id": p.id, "name": p.name, "text": p.description, "score": score})
    if inspect(db.get_bind()).has_table(DocumentChunk.__tablename__):
        for c in db.scalars(select(DocumentChunk).limit(500)).all():
            hits = len(q & set(tokens(c.content)))
            if hits:
                out.append({"source": c.source, "program_id": c.program_id, "name": c.source, "text": c.content[:400], "score": hits})
    out.sort(key=lambda r: r["score"], reverse=True)
    return out[:limit]


def find_programs_named(db: Session, text: str) -> list[Program]:
    """Programmes explicitly mentioned (by name, level, domain) in a message, for comparisons."""
    cs = set(concepts_in(text)) | {t for t in tokens(text) if len(t) > 2}
    res = []
    for p in db.scalars(select(Program).where(Program.active.is_(True))).all():
        tags = program_tags(p) | set(tokens(p.name))
        # a programme is "named" when a domain/level concept or one of its name words appears
        if cs & (tags - {"informatique"} if len(cs) > 1 else tags):
            res.append(p)
    return res
