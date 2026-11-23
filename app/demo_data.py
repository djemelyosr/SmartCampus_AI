"""Demonstration data for local development: one account per role, candidates at different steps of the journey,
and a catalogue with specialties, subjects and published official information.

Fictitious people and figures. Every account uses DEMO_PASSWORD (see GUIDE_DEMARRAGE.md). Idempotent: does nothing
if the demo administrator already exists. Never enable it on a real deployment.
"""

from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.models import (
    AdmissionCondition,
    Appointment,
    CandidateProfile,
    Conversation,
    Curriculum,
    Fee,
    Message,
    PaymentTerm,
    PreRegistration,
    PreRegStatus,
    Program,
    PublicationStatus,
    Qcm,
    Role,
    Specialty,
    Subject,
    User,
)
from app.seed import seed_programs
from app.services import qcm as qcm_service

DEMO_PASSWORD = "SmartCampus-Demo-2026"
DOMAIN = "demo.smartcampus.tn"
TUNIS = timezone(timedelta(hours=1))

TEAM = [
    ("admin", "Amira Mansour", Role.admin),
    ("iit.academique", "Nadia Khelifi", Role.iit_head),
    ("isb.academique", "Karim Ben Salah", Role.isb_head),
    ("entretien", "Sami Gharbi", Role.interviewer),
    ("direction", "Youssef Dridi", Role.direction),
]


def demo_accounts() -> list[tuple[str, str, Role]]:
    """(email, name, role) of every demo account, team first."""
    team = [(f"{k}@{DOMAIN}", n, r) for k, n, r in TEAM]
    cands = [(f"{k}@{DOMAIN}", c["name"], Role.candidate) for k, c in CANDIDATES.items()]
    return team + cands


# key -> profile, chosen programme, how far they went
CANDIDATES = {
    "fatma.kchaou": {
        "name": "Fatma Kchaou", "program": "Licence en informatique", "stage": "interview",
        "profile": {"school_level": "Terminale", "favorite_subjects": ["Mathématiques", "Informatique"], "career_goal": "Devenir ingénieure logicielle",
                    "constraints": {"bac": "Mathématiques", "city": "Sfax", "mobilite": "Sfax en priorité", "moyenne": "15,20 / 20"}},
        "chat": [("J’aime les maths et l’informatique, j’hésite entre Prépa et Licence.", "Votre envie de pratiquer progressivement peut orienter vers la Licence en informatique ; la Prépa reste une piste pour approfondir les bases.", {"sources": ["Catalogue des parcours IIT"]})],
    },
    "aziz.trabelsi": {
        "name": "Aziz Trabelsi", "program": "Cycle préparatoire", "stage": "qcm",
        "profile": {"school_level": "Terminale", "favorite_subjects": ["Physique", "Mathématiques"], "career_goal": "Intégrer une école d’ingénieurs", "constraints": {"bac": "Sciences expérimentales", "city": "Sousse"}},
        "chat": [("Nheb n9ra prépa w ba3d ingénierie", "La Prépa IIT prépare aux cycles d’ingénieur ; les passerelles dépendent de vos résultats.", {"sources": ["Catalogue des parcours IIT"]})],
    },
    "mariem.kammoun": {
        "name": "Mariem Kammoun", "program": "Parcours en gestion", "stage": "submitted",
        "profile": {"school_level": "Bac obtenu", "favorite_subjects": ["Économie"], "career_goal": "Travailler en management", "constraints": {"bac": "Économie et gestion", "city": "Tunis", "budget": "À discuter"}},
        "chat": [("Quels sont les frais de la licence en gestion ?", "Je transmets votre question à un conseiller ISB pour confirmer les frais en vigueur.", {"handoff": True})],
    },
    "sarra.ayadi": {
        "name": "Sarra Ayadi", "program": "Parcours en ingénierie", "stage": "submitted",
        "profile": {"school_level": "Licence", "favorite_subjects": ["Électronique"], "career_goal": "Systèmes embarqués", "constraints": {"city": "Sfax"}},
        "chat": [],
    },
    "hedi.feki": {
        "name": "Hedi Feki", "program": "Licence en informatique", "stage": "enrolled",
        "profile": {"school_level": "Terminale", "favorite_subjects": ["Informatique"], "career_goal": "Data scientist", "constraints": {"city": "Monastir"}},
        "chat": [("Est-ce qu’il y a des projets en data ?", "La Licence comporte des projets ; les spécialités data sont à confirmer avec l’IIT.", {"sources": ["Catalogue des parcours IIT"]})],
    },
}


def _next_weekday(start: date, n: int) -> date:
    d = start + timedelta(days=n)
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d


def _catalogue(db: Session, progs: dict[str, Program]) -> None:
    today = datetime.now(TUNIS).date()
    year = f"{today.year}-{today.year + 1}"
    lic, ges, prepa = progs["Licence en informatique"], progs["Parcours en gestion"], progs["Cycle préparatoire"]
    lic.duration_years, ges.duration_years, prepa.duration_years = 3, 3, 2

    gl = Specialty(program_id=lic.id, name="Génie logiciel", description="Conception et développement d’applications.")
    ds = Specialty(program_id=lic.id, name="Science des données", description="Données, statistiques et apprentissage automatique.")
    db.add_all([gl, ds])
    db.flush()
    c1 = Curriculum(program_id=lic.id, specialty_id=None, name="Tronc commun L1", academic_year=year, description="Première année commune.")
    c2 = Curriculum(program_id=lic.id, specialty_id=gl.id, name="Génie logiciel L2-L3", academic_year=year)
    c3 = Curriculum(program_id=ges.id, name="Licence gestion L1", academic_year=year)
    db.add_all([c1, c2, c3])
    db.flush()
    db.add_all([
        Subject(curriculum_id=c1.id, code="INF101", name="Algorithmique et programmation", semester=1, credits=6, coefficient=3, hours=63),
        Subject(curriculum_id=c1.id, code="MAT101", name="Analyse 1", semester=1, credits=5, coefficient=2.5, hours=52),
        Subject(curriculum_id=c1.id, code="INF102", name="Architecture des ordinateurs", semester=2, credits=4, coefficient=2, hours=42),
        Subject(curriculum_id=c2.id, code="GL201", name="Programmation orientée objet", semester=3, credits=6, coefficient=3, hours=63),
        Subject(curriculum_id=c2.id, code="GL301", name="Projet de génie logiciel", semester=5, credits=8, coefficient=4, hours=84),
        Subject(curriculum_id=c3.id, code="GES101", name="Principes de gestion", semester=1, credits=5, coefficient=2.5, hours=48),
        Subject(curriculum_id=c3.id, code="ECO101", name="Microéconomie", semester=1, credits=5, coefficient=2.5, hours=48),
    ])

    pub = dict(status=PublicationStatus.published, published_at=datetime.now(timezone.utc), valid_from=today - timedelta(days=30),
               valid_until=today + timedelta(days=300), academic_year=year)
    fee_lic = Fee(program_id=lic.id, label="Frais de scolarité", amount=6500, currency="TND", period="annual", description="Montant fictif de démonstration.", **pub)
    fee_ges = Fee(program_id=ges.id, label="Frais de scolarité", amount=5800, currency="TND", period="annual", description="Montant fictif de démonstration.", **pub)
    db.add_all([fee_lic, fee_ges])
    db.flush()
    db.add_all([
        Fee(program_id=lic.id, label="Frais d’inscription", amount=300, currency="TND", period="one_time", status=PublicationStatus.draft),
        PaymentTerm(program_id=lic.id, fee_id=fee_lic.id, method="bank_transfer", title="Paiement en trois versements", installments=3, down_payment_percent=40, **pub),
        PaymentTerm(program_id=ges.id, fee_id=fee_ges.id, method="bank_transfer", title="Paiement annuel", installments=1, **pub),
        AdmissionCondition(program_id=lic.id, kind="diploma", title="Baccalauréat", description="Sections mathématiques, sciences ou informatique.", required=True, **pub),
        AdmissionCondition(program_id=lic.id, kind="average", title="Moyenne au baccalauréat", threshold=12, required=True, **pub),
        AdmissionCondition(program_id=ges.id, kind="diploma", title="Baccalauréat", description="Toutes sections.", required=True, **pub),
        AdmissionCondition(program_id=prepa.id, kind="exam", title="Entretien de motivation", required=True, status=PublicationStatus.draft),
    ])


def seed_demo(db: Session) -> bool:
    """Insert the demo data once. Returns False if it was already there."""
    if db.scalar(select(User.id).where(User.email == f"admin@{DOMAIN}")):
        return False
    seed_programs(db)
    progs = {p.name: p for p in db.scalars(select(Program)).all()}
    _catalogue(db, progs)
    pw = hash_password(DEMO_PASSWORD)

    for key, name, role in TEAM:
        db.add(User(email=f"{key}@{DOMAIN}", full_name=name, role=role, hashed_password=pw))

    today = datetime.now(TUNIS).date()
    now = datetime.now(timezone.utc)
    interviewer = None
    db.flush()
    interviewer = db.scalar(select(User).where(User.email == f"entretien@{DOMAIN}"))
    for i, (key, c) in enumerate(CANDIDATES.items()):
        u = User(email=f"{key}@{DOMAIN}", full_name=c["name"], role=Role.candidate, hashed_password=pw)
        u.profile = CandidateProfile(consent_given=True, **c["profile"])
        db.add(u)
        db.flush()

        if c["chat"]:
            conv = Conversation(user_id=u.id, language="fr")
            db.add(conv)
            db.flush()
            for question, answer, meta in c["chat"]:
                db.add(Message(conversation_id=conv.id, role="user", content=question))
                db.add(Message(conversation_id=conv.id, role="assistant", content=answer, meta=meta))

        stage = c["stage"]
        status = {"submitted": PreRegStatus.submitted, "qcm": PreRegStatus.qcm_pending, "interview": PreRegStatus.interview_scheduled, "enrolled": PreRegStatus.enrolled}[stage]
        pre = PreRegistration(user_id=u.id, program_id=progs[c["program"]].id, status=status)
        db.add(pre)
        db.flush()
        if stage in ("qcm", "interview", "enrolled"):
            answers = {i_: q["correct"] if (i_ + i) % 4 else (q["correct"] + 1) % 4 for i_, q in enumerate(qcm_service.BANK)}
            res = qcm_service.score(answers)
            db.add(Qcm(pre_registration_id=pre.id, questions=qcm_service.public_questions(), answers={str(k): v for k, v in answers.items()},
                       score=res["good"], summary=res["summary"], finished_at=now - timedelta(days=1)))
        if stage in ("interview", "enrolled"):
            day = _next_weekday(today, 2) if stage == "interview" else today - timedelta(days=7)
            at = datetime.combine(day, time(10, 0), tzinfo=TUNIS).astimezone(timezone.utc)
            db.add(Appointment(pre_registration_id=pre.id, interviewer_id=interviewer.id if interviewer else None, scheduled_at=at,
                               status="confirmed" if stage == "interview" else "done"))
    db.commit()
    return True
