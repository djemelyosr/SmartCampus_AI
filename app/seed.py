"""Illustrative catalogue (same names as the frontend demo catalogue). Real content must come from IIT/ISB."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.models.models import Institution, Level, Program, Role, User

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


TEAM = [
    (Role.admin, "admin@smartcampus.tn", "Administrateur"),
    (Role.iit_head, "iit@smartcampus.tn", "Responsable académique IIT"),
    (Role.isb_head, "isb@smartcampus.tn", "Responsable académique ISB"),
    (Role.interviewer, "entretien@smartcampus.tn", "Responsable entretien"),
    (Role.direction, "direction@smartcampus.tn", "Direction"),
]


def seed_team_accounts(db: Session) -> int:
    """Create the team accounts (one per role) when SEED_TEAM_PASSWORD is set. Idempotent; no default password."""
    if not settings.seed_team_password:
        return 0
    have = set(db.scalars(select(User.email)).all())
    added = 0
    for role, email, name in TEAM:
        if email in have:
            user = db.scalar(select(User).where(User.email == email))
            if user is not None and "?" in user.full_name:  # repair a name stored with a lost accent
                user.full_name = name
        else:
            db.add(User(email=email, full_name=name, role=role, hashed_password=hash_password(settings.seed_team_password)))
            added += 1
    db.commit()
    return added
