"""Orientation: compatibility scoring, justified shortlist (2-3 programmes), comparison. Never imposes a choice."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.rag import program_tags, source_label
from app.models.models import Program

LABELS = {
    "maths": "maths", "physique": "physique", "informatique": "informatique", "ia_data": "IA / data", "gestion": "gestion",
    "finance": "finance", "ingenierie": "ingénierie", "prepa": "voie préparatoire", "licence": "licence",
    "pratique": "approche pratique", "progressif": "progression par étapes",
}


def profile_concepts(profile: dict) -> dict[str, float]:
    w: dict[str, float] = {}
    for key, weight in (("goal", 3.0), ("interests", 2.0), ("subjects", 1.5), ("style", 1.0), ("tracks", 1.5)):
        for c in profile.get(key, []):
            w[c] = max(w.get(c, 0), weight)
    return w


def score_program(p: Program, wants: dict[str, float]) -> tuple[int, list[str]]:
    tags = program_tags(p)
    if p.level.value == "licence":
        tags |= {"pratique"}  # the licence is the hands-on track in the catalogue
    matched = [c for c in wants if c in tags]
    total = sum(wants.values()) or 1.0
    pct = round(100 * sum(wants[c] for c in matched) / total)
    return pct, matched


def shortlist(db: Session, profile: dict, k: int = 3) -> list[dict]:
    wants = profile_concepts(profile)
    if not wants:
        return []
    rows = []
    for p in db.scalars(select(Program).where(Program.active.is_(True))).all():
        pct, matched = score_program(p, wants)
        if pct > 0:
            rows.append({
                "program_id": p.id, "name": p.name, "institution": p.institution.value, "level": p.level.value,
                "score": pct, "matched": [LABELS.get(m, m) for m in matched], "source": source_label(p),
                "requirements": p.admission_requirements or "À confirmer auprès de l’établissement.",
            })
    rows.sort(key=lambda r: r["score"], reverse=True)
    return rows[:k]


def compare(programs: list[Program]) -> list[dict]:
    return [{
        "program_id": p.id, "name": p.name, "institution": p.institution.value, "level": p.level.value,
        "duration": f"{p.duration_years} an(s)" if p.duration_years else "à confirmer",
        "careers": ", ".join(p.career_outcomes or []) or "non renseigné",
        "requirements": p.admission_requirements or "À confirmer auprès de l’établissement.",
        "source": source_label(p),
    } for p in programs]
