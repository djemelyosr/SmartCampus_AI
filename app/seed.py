"""Illustrative catalogue (same names as the frontend demo catalogue). Real content must come from IIT/ISB."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.models import Institution, Level, Program

PROGRAMS = [
    (Institution.IIT, Level.licence, "Licence en informatique", "Apprendre par la pratique et construire votre projet pas à pas.", ["Développement logiciel", "Projets numériques"]),
    (Institution.IIT, Level.prepa, "Cycle préparatoire", "Consolider les fondamentaux avant de se spécialiser.", ["Poursuite d’études"]),
    (Institution.IIT, Level.ingenierie, "Parcours en ingénierie", "Explorer une spécialisation selon votre parcours antérieur.", ["Conception de systèmes", "Projet technique"]),
    (Institution.ISB, Level.licence, "Parcours en gestion", "Relier les enjeux de l’entreprise et les usages du numérique.", ["Gestion", "Organisation"]),
    (Institution.ISB, Level.licence, "Parcours en finance", "Explorer l’analyse et les problématiques financières.", ["Analyse financière"]),
]


def seed_programs(db: Session) -> int:
    """Insert the illustrative programmes missing from the catalogue (idempotent). Returns how many were added."""
    have = set(db.scalars(select(Program.name)).all())
    added = 0
    for inst, level, name, desc, outs in PROGRAMS:
        if name not in have:
            db.add(Program(institution=inst, level=level, name=name, description=desc, career_outcomes=outs, admission_requirements="À confirmer auprès de l’établissement."))
            added += 1
    db.commit()
    return added
