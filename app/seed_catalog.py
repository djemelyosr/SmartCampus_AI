"""Demonstration catalogue: specialties, teaching programmes (programmes pedagogiques), subjects, admission conditions
and fees (tarifs) of the five illustrative formations created by `seed.seed_programs`.

FICTIONAL DATA for testing the platform. Real content (subjects, conditions, tuition) must be entered or confirmed by
the IIT / ISB academic heads through the catalogue manager. Idempotent: existing items are never duplicated or overwritten."""

from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.catalog import (
    AdmissionCondition, ConditionKind as K, Curriculum, Fee, FeePeriod as P, PaymentMethod as M, PaymentTerm, PublicationStatus, Specialty, Subject,
)
from app.models.models import Program

YEAR = "2026-2027"
# The demonstration data is published (visible to candidates and the agent) from the start of the year; no end date, so the
# demo never silently expires. Real items entered by the academic heads start as drafts and need an explicit publication.
VALID_FROM = date(2026, 1, 1)
DOSSIER = "Copie de la CIN, relevé de notes du baccalauréat, photo d'identité et lettre de motivation."
TUITION = "Montant indicatif de démonstration, payable en tranches. À confirmer auprès de l'établissement."
REGISTRATION = "Payés une seule fois, lors de la confirmation de l'inscription."

# subject = (code, name, semester, credits, coefficient, hours)
# curriculum = (name, specialty or None, description, [subjects])
# condition = (specialty or None, kind, title, description, required, threshold)
# fee = (specialty or None, label, amount in TND, period, description)
CATALOG = [
    {
        "program": "Licence en informatique", "duration": 3,
        "admission": "Baccalauréat scientifique ou technique, dossier académique et entretien. Détail des conditions ci-dessous (données de démonstration).",
        "specialties": [
            ("Développement logiciel", "Conception d'applications web et mobiles, qualité logicielle et travail en équipe projet."),
            ("Réseaux et systèmes", "Administration des systèmes, réseaux, virtualisation et bases de la cybersécurité."),
            ("Data et intelligence artificielle", "Analyse de données, apprentissage automatique et premiers projets d'IA."),
        ],
        "curricula": [
            ("Tronc commun – 1re année", None, "Bases de la programmation, des mathématiques et des systèmes, communes aux trois spécialités.", [
                ("INF101", "Algorithmique et programmation 1", 1, 5, 3, 56), ("MAT101", "Mathématiques pour l'informatique", 1, 4, 2.5, 42),
                ("ARC101", "Architecture des ordinateurs", 1, 3, 2, 35), ("ANG101", "Anglais technique 1", 1, 2, 1, 28),
                ("INF102", "Programmation orientée objet", 2, 5, 3, 56), ("BDD101", "Bases de données relationnelles", 2, 4, 2.5, 42),
                ("WEB101", "Introduction au développement web", 2, 3, 2, 35), ("COM101", "Communication et techniques d'expression", 2, 2, 1, 28),
            ]),
            ("Développement logiciel – 2e et 3e années", "Développement logiciel", "Parcours orienté applications et génie logiciel.", [
                ("DEV201", "Développement web avancé", 3, 5, 3, 56), ("DEV202", "Génie logiciel et UML", 3, 4, 2.5, 42),
                ("DEV203", "Développement mobile", 4, 4, 2.5, 42), ("DEV301", "Architecture logicielle et API", 5, 5, 3, 56),
                ("DEV302", "Tests, qualité et DevOps", 5, 3, 2, 35), ("DEV303", "Projet de fin d'études", 6, 12, 4, 120),
            ]),
            ("Réseaux et systèmes – 2e et 3e années", "Réseaux et systèmes", "Parcours orienté infrastructures et administration.", [
                ("RES201", "Réseaux informatiques", 3, 5, 3, 56), ("SYS201", "Administration Linux", 3, 4, 2.5, 42),
                ("RES202", "Routage et commutation", 4, 4, 2.5, 42), ("SEC201", "Fondamentaux de la cybersécurité", 4, 4, 2.5, 42),
                ("RES301", "Virtualisation et cloud", 5, 5, 3, 56), ("RES303", "Projet de fin d'études", 6, 12, 4, 120),
            ]),
            ("Data et IA – 2e et 3e années", "Data et intelligence artificielle", "Parcours orienté données et apprentissage automatique.", [
                ("DAT201", "Probabilités et statistiques", 3, 5, 3, 56), ("DAT202", "Python pour la data science", 3, 4, 2.5, 42),
                ("DAT203", "Entrepôts de données et SQL avancé", 4, 4, 2.5, 42), ("IAA301", "Apprentissage automatique", 5, 5, 3, 56),
                ("IAA302", "Visualisation de données", 5, 3, 2, 35), ("DAT303", "Projet de fin d'études", 6, 12, 4, 120),
            ]),
        ],
        "conditions": [
            (None, K.diploma, "Baccalauréat", "Baccalauréat mathématiques, sciences expérimentales, sciences techniques ou informatique.", True, None),
            (None, K.average, "Moyenne générale au baccalauréat", "Moyenne minimale indicative pour l'étude du dossier.", True, 11),
            (None, K.document, "Dossier de candidature", DOSSIER, True, None),
            (None, K.exam, "Test de positionnement", "Test court en mathématiques et logique avant l'entretien.", False, None),
            (None, K.language, "Français", "Capacité à suivre les cours en français ; l'anglais technique s'apprend pendant le cursus.", False, None),
            ("Data et intelligence artificielle", K.average, "Moyenne conseillée en mathématiques", "Recommandée pour suivre la spécialité à l'aise.", False, 12),
        ],
        "fees": [
            (None, "Frais d'inscription", 350, P.one_time, REGISTRATION),
            (None, "Scolarité annuelle", 7200, P.annual, TUITION),
            ("Réseaux et systèmes", "Matériel de laboratoire réseau", 300, P.annual, "Accès aux équipements et aux travaux pratiques."),
            ("Data et intelligence artificielle", "Laboratoire et licences logicielles", 400, P.annual, "Plateforme de calcul et outils de data science."),
        ],
    },
    {
        "program": "Cycle préparatoire", "duration": 2,
        "admission": "Baccalauréat scientifique ou technique, dossier académique et entretien de motivation (données de démonstration).",
        "specialties": [],
        "curricula": [
            ("Cycle préparatoire – 1re année", None, "Consolidation des fondamentaux en mathématiques, physique et informatique.", [
                ("MAT111", "Analyse 1", 1, 5, 3, 56), ("MAT112", "Algèbre linéaire", 1, 4, 2.5, 42), ("PHY111", "Physique générale", 1, 4, 2.5, 42),
                ("INF111", "Algorithmique et programmation", 1, 4, 2.5, 42), ("ANG111", "Anglais", 1, 2, 1, 28),
                ("MAT121", "Analyse 2", 2, 5, 3, 56), ("MAT122", "Probabilités", 2, 3, 2, 35), ("PHY121", "Électricité", 2, 4, 2.5, 42),
                ("INF121", "Programmation structurée", 2, 4, 2.5, 42),
            ]),
            ("Cycle préparatoire – 2e année", None, "Approfondissement scientifique et préparation à l'entrée en cycle ingénieur.", [
                ("MAT211", "Analyse 3", 3, 5, 3, 56), ("MAT212", "Algèbre bilinéaire", 3, 4, 2.5, 42), ("PHY211", "Mécanique", 3, 4, 2.5, 42),
                ("INF211", "Structures de données", 3, 4, 2.5, 42), ("MAT221", "Équations différentielles", 4, 4, 2.5, 42),
                ("PHY221", "Thermodynamique", 4, 3, 2, 35), ("INF221", "Bases de données", 4, 4, 2.5, 42), ("PRJ221", "Projet scientifique", 4, 6, 3, 60),
            ]),
        ],
        "conditions": [
            (None, K.diploma, "Baccalauréat", "Baccalauréat mathématiques, sciences expérimentales ou sciences techniques.", True, None),
            (None, K.average, "Moyenne générale au baccalauréat", "Moyenne minimale indicative pour l'étude du dossier.", True, 12),
            (None, K.document, "Dossier de candidature", DOSSIER, True, None),
            (None, K.exam, "Entretien de motivation", "Échange avec le responsable entretien sur le projet de l'étudiant.", True, None),
        ],
        "fees": [
            (None, "Frais d'inscription", 350, P.one_time, REGISTRATION),
            (None, "Scolarité annuelle", 6800, P.annual, TUITION),
        ],
    },
    {
        "program": "Parcours en ingénierie", "duration": 3,
        "admission": "Licence en informatique ou deux années de cycle préparatoire validées, dossier et entretien technique (données de démonstration).",
        "specialties": [
            ("Génie logiciel", "Conception, construction et industrialisation de systèmes logiciels complexes."),
            ("Cybersécurité", "Protection des systèmes, tests d'intrusion, gouvernance et gestion des risques."),
            ("Intelligence artificielle", "Apprentissage profond, ingénierie des données et IA générative."),
        ],
        "curricula": [
            ("Tronc commun ingénieur – 1re année", None, "Socle d'ingénierie commun aux trois spécialités.", [
                ("ING101", "Architecture des systèmes d'information", 1, 5, 3, 56), ("ING102", "Algorithmique avancée", 1, 5, 3, 56),
                ("ING103", "Mathématiques appliquées", 1, 4, 2.5, 42), ("ING104", "Anglais professionnel", 1, 2, 1, 28),
                ("ING201", "Gestion de projet agile", 2, 4, 2.5, 42), ("ING202", "Systèmes d'exploitation et réseaux", 2, 4, 2.5, 42),
                ("ING203", "Management et entrepreneuriat", 2, 3, 2, 35),
            ]),
            ("Génie logiciel – 2e et 3e années", "Génie logiciel", "Spécialisation génie logiciel.", [
                ("GLO301", "Conception et architecture logicielle", 3, 5, 3, 56), ("GLO302", "Microservices et cloud-native", 3, 5, 3, 56),
                ("GLO401", "DevOps et intégration continue", 4, 4, 2.5, 42), ("GLO402", "Qualité et sécurité du logiciel", 4, 4, 2.5, 42),
                ("GLO601", "Projet de fin d'études", 6, 20, 5, 400),
            ]),
            ("Cybersécurité – 2e et 3e années", "Cybersécurité", "Spécialisation cybersécurité.", [
                ("SEC301", "Cryptographie appliquée", 3, 5, 3, 56), ("SEC302", "Sécurité des réseaux", 3, 5, 3, 56),
                ("SEC401", "Tests d'intrusion", 4, 4, 2.5, 42), ("SEC402", "Gouvernance, risques et conformité", 4, 4, 2.5, 42),
                ("SEC601", "Projet de fin d'études", 6, 20, 5, 400),
            ]),
            ("Intelligence artificielle – 2e et 3e années", "Intelligence artificielle", "Spécialisation intelligence artificielle.", [
                ("IAI301", "Apprentissage statistique", 3, 5, 3, 56), ("IAI302", "Ingénierie des données", 3, 5, 3, 56),
                ("IAI401", "Apprentissage profond", 4, 4, 2.5, 42), ("IAI402", "IA générative et RAG", 4, 4, 2.5, 42),
                ("IAI601", "Projet de fin d'études", 6, 20, 5, 400),
            ]),
        ],
        "conditions": [
            (None, K.diploma, "Diplôme d'accès", "Licence en informatique ou validation de deux années de cycle préparatoire.", True, None),
            (None, K.average, "Moyenne du cursus précédent", "Moyenne minimale indicative pour l'étude du dossier.", True, 12),
            (None, K.document, "Dossier de candidature", "Relevés de notes, CV, lettre de motivation et copie de la CIN.", True, None),
            (None, K.exam, "Entretien technique", "Entretien avec le responsable entretien sur les acquis et le projet professionnel.", True, None),
            (None, K.language, "Anglais", "Niveau B1 minimum conseillé pour suivre les enseignements et la documentation technique.", False, None),
            ("Cybersécurité", K.exam, "Test de logique et de réseaux", "Évaluation des bases en réseaux avant l'admission dans la spécialité.", False, None),
        ],
        "fees": [
            (None, "Frais d'inscription", 350, P.one_time, REGISTRATION),
            (None, "Scolarité annuelle", 9500, P.annual, TUITION),
            ("Cybersécurité", "Certifications et plateforme de pratique", 600, P.one_time, "Préparation à une certification et accès aux plateformes d'entraînement."),
        ],
    },
    {
        "program": "Parcours en gestion", "duration": 3,
        "admission": "Baccalauréat (économie et gestion, sciences, lettres ou équivalent), dossier et entretien de motivation (données de démonstration).",
        "specialties": [
            ("Management et entrepreneuriat", "Pilotage d'organisations, création d'entreprise et gestion de projets."),
            ("Marketing digital", "Stratégie de marque, communication en ligne et analyse de données marketing."),
            ("Ressources humaines", "Gestion du personnel, droit du travail, recrutement et développement des compétences."),
        ],
        "curricula": [
            ("Tronc commun – 1re année", None, "Fondamentaux de la gestion communs aux trois spécialités.", [
                ("GES101", "Introduction à la gestion", 1, 4, 2.5, 42), ("ECO101", "Microéconomie", 1, 4, 2.5, 42), ("CPT101", "Comptabilité générale", 1, 5, 3, 56),
                ("MAT151", "Mathématiques et statistiques appliquées", 1, 3, 2, 35), ("ANG151", "Anglais des affaires", 1, 2, 1, 28),
                ("GES102", "Droit des affaires", 2, 4, 2.5, 42), ("MKT101", "Principes du marketing", 2, 4, 2.5, 42), ("INF151", "Outils numériques pour la gestion", 2, 3, 2, 35),
            ]),
            ("Management et entrepreneuriat – 2e et 3e années", "Management et entrepreneuriat", "Parcours management et création d'activité.", [
                ("MGT201", "Stratégie d'entreprise", 3, 5, 3, 56), ("MGT202", "Création d'entreprise et business plan", 3, 4, 2.5, 42),
                ("MGT301", "Management de projet", 5, 4, 2.5, 42), ("MGT302", "Gestion de la production et logistique", 5, 4, 2.5, 42),
                ("MGT303", "Stage et mémoire", 6, 12, 4, 120),
            ]),
            ("Marketing digital – 2e et 3e années", "Marketing digital", "Parcours marketing et communication numérique.", [
                ("MKT201", "Comportement du consommateur", 3, 5, 3, 56), ("MKT202", "Marketing digital et réseaux sociaux", 3, 4, 2.5, 42),
                ("MKT301", "Analyse de données marketing", 5, 4, 2.5, 42), ("MKT302", "Communication et gestion de marque", 5, 4, 2.5, 42),
                ("MKT303", "Stage et mémoire", 6, 12, 4, 120),
            ]),
            ("Ressources humaines – 2e et 3e années", "Ressources humaines", "Parcours gestion des ressources humaines.", [
                ("RHU201", "Droit du travail", 3, 5, 3, 56), ("RHU202", "Gestion des ressources humaines", 3, 4, 2.5, 42),
                ("RHU301", "Recrutement et développement des compétences", 5, 4, 2.5, 42), ("RHU302", "Paie et administration du personnel", 5, 4, 2.5, 42),
                ("RHU303", "Stage et mémoire", 6, 12, 4, 120),
            ]),
        ],
        "conditions": [
            (None, K.diploma, "Baccalauréat", "Baccalauréat économie et gestion, sciences, lettres ou diplôme équivalent.", True, None),
            (None, K.average, "Moyenne générale au baccalauréat", "Moyenne minimale indicative pour l'étude du dossier.", True, 10.5),
            (None, K.document, "Dossier de candidature", DOSSIER, True, None),
            (None, K.exam, "Entretien de motivation", "Échange avec le responsable entretien sur le projet de l'étudiant.", True, None),
        ],
        "fees": [
            (None, "Frais d'inscription", 300, P.one_time, REGISTRATION),
            (None, "Scolarité annuelle", 5800, P.annual, TUITION),
            ("Marketing digital", "Licences d'outils marketing", 250, P.annual, "Accès aux outils d'analyse et de gestion de campagnes."),
        ],
    },
    {
        "program": "Parcours en finance", "duration": 3,
        "admission": "Baccalauréat, dossier académique et test de mathématiques (données de démonstration).",
        "specialties": [
            ("Finance d'entreprise", "Diagnostic financier, budgets, trésorerie et évaluation d'entreprise."),
            ("Banque et marchés financiers", "Techniques bancaires, marchés, gestion de portefeuille et des risques."),
            ("Comptabilité et audit", "Comptabilité approfondie, fiscalité, audit et contrôle de gestion."),
        ],
        "curricula": [
            ("Tronc commun – 1re année", None, "Fondamentaux de la finance communs aux trois spécialités.", [
                ("FIN101", "Introduction à la finance", 1, 4, 2.5, 42), ("CPT111", "Comptabilité financière", 1, 5, 3, 56), ("ECO111", "Macroéconomie", 1, 4, 2.5, 42),
                ("MAT161", "Mathématiques financières", 1, 4, 2.5, 42), ("ANG161", "Anglais financier", 1, 2, 1, 28),
                ("DRT111", "Droit commercial et fiscalité", 2, 4, 2.5, 42), ("STA111", "Statistiques pour la finance", 2, 4, 2.5, 42), ("XLS111", "Tableur et outils de modélisation", 2, 3, 2, 35),
            ]),
            ("Finance d'entreprise – 2e et 3e années", "Finance d'entreprise", "Parcours finance d'entreprise.", [
                ("FDE201", "Diagnostic financier", 3, 5, 3, 56), ("FDE202", "Gestion budgétaire", 3, 4, 2.5, 42),
                ("FDE301", "Évaluation d'entreprise", 5, 5, 3, 56), ("FDE302", "Gestion de trésorerie", 5, 4, 2.5, 42),
                ("FDE303", "Stage et mémoire", 6, 12, 4, 120),
            ]),
            ("Banque et marchés financiers – 2e et 3e années", "Banque et marchés financiers", "Parcours banque et marchés.", [
                ("BMF201", "Techniques bancaires", 3, 5, 3, 56), ("BMF202", "Marchés financiers", 3, 4, 2.5, 42),
                ("BMF301", "Gestion de portefeuille", 5, 5, 3, 56), ("BMF302", "Gestion des risques bancaires", 5, 4, 2.5, 42),
                ("BMF303", "Stage et mémoire", 6, 12, 4, 120),
            ]),
            ("Comptabilité et audit – 2e et 3e années", "Comptabilité et audit", "Parcours comptabilité, audit et contrôle de gestion.", [
                ("CAU201", "Comptabilité approfondie", 3, 5, 3, 56), ("CAU202", "Fiscalité des entreprises", 3, 4, 2.5, 42),
                ("CAU301", "Audit financier", 5, 5, 3, 56), ("CAU302", "Contrôle de gestion", 5, 4, 2.5, 42),
                ("CAU303", "Stage et mémoire", 6, 12, 4, 120),
            ]),
        ],
        "conditions": [
            (None, K.diploma, "Baccalauréat", "Baccalauréat économie et gestion, mathématiques, sciences ou diplôme équivalent.", True, None),
            (None, K.average, "Moyenne générale au baccalauréat", "Moyenne minimale indicative pour l'étude du dossier.", True, 11),
            (None, K.document, "Dossier de candidature", DOSSIER, True, None),
            (None, K.exam, "Test de mathématiques", "Test court sur les bases de calcul et de raisonnement quantitatif.", False, None),
        ],
        "fees": [
            (None, "Frais d'inscription", 300, P.one_time, REGISTRATION),
            (None, "Scolarité annuelle", 6200, P.annual, TUITION),
            ("Banque et marchés financiers", "Accès aux simulateurs de marché", 200, P.annual, "Salle de marché virtuelle et données de cotation pédagogiques."),
        ],
    },
]


# payment term = (method, title, description, installments, down payment %)  -- FICTIONAL, formation-wide
_TRANSFER = (M.bank_transfer, "Virement bancaire en 3 tranches", "Scolarité annuelle payable en trois versements, le premier lors de l'inscription.", 3, 40.0)
_COUNTER = (M.cash, "Paiement au guichet", "Espèces ou chèque auprès du service de la scolarité, en un seul versement.", 1, None)
PAYMENTS = {name: [_TRANSFER, _COUNTER] for name in (
    "Licence en informatique", "Cycle préparatoire", "Parcours en ingénierie", "Parcours en gestion", "Parcours en finance")}


def seed_catalog(db: Session) -> dict[str, int]:
    """Insert the demonstration catalogue (idempotent). Returns how many items of each kind were added."""
    added = dict(specialties=0, curricula=0, subjects=0, conditions=0, fees=0, payment_terms=0)
    published = dict(status=PublicationStatus.published, valid_from=VALID_FROM, academic_year=YEAR, published_at=datetime.now(timezone.utc))
    for block in CATALOG:
        program = db.scalar(select(Program).where(Program.name == block["program"]))
        if program is None:  # formation removed or renamed by a manager: nothing to attach to
            continue
        if program.duration_years is None:
            program.duration_years = block["duration"]
        if not program.admission_requirements.strip() or program.admission_requirements.startswith("À confirmer"):
            program.admission_requirements = block["admission"]

        specs: dict[str, Specialty] = {}
        for name, desc in block["specialties"]:
            spec = db.scalar(select(Specialty).where(Specialty.program_id == program.id, Specialty.name == name))
            if spec is None:
                spec = Specialty(program_id=program.id, name=name, description=desc)
                db.add(spec)
                db.flush()
                added["specialties"] += 1
            specs[name] = spec
        sid = lambda name: specs[name].id if name else None  # noqa: E731

        for name, spec_name, desc, subjects in block["curricula"]:
            cur = db.scalar(select(Curriculum).where(Curriculum.program_id == program.id, Curriculum.name == name))
            if cur is None:
                cur = Curriculum(program_id=program.id, specialty_id=sid(spec_name), name=name, academic_year=YEAR, description=desc)
                db.add(cur)
                db.flush()
                added["curricula"] += 1
            have = set(db.scalars(select(Subject.code).where(Subject.curriculum_id == cur.id)).all())
            for code, sname, semester, credits, coef, hours in subjects:
                if code not in have:
                    db.add(Subject(curriculum_id=cur.id, code=code, name=sname, semester=semester, credits=credits, coefficient=coef, hours=hours))
                    added["subjects"] += 1

        for spec_name, kind, title, desc, required, threshold in block["conditions"]:
            exists = db.scalar(select(AdmissionCondition.id).where(
                AdmissionCondition.program_id == program.id, AdmissionCondition.specialty_id == sid(spec_name), AdmissionCondition.title == title))
            if exists is None:
                db.add(AdmissionCondition(program_id=program.id, specialty_id=sid(spec_name), kind=kind, title=title, description=desc, required=required, threshold=threshold, **published))
                added["conditions"] += 1

        for spec_name, label, amount, period, desc in block["fees"]:
            exists = db.scalar(select(Fee.id).where(Fee.program_id == program.id, Fee.specialty_id == sid(spec_name), Fee.label == label))
            if exists is None:
                db.add(Fee(program_id=program.id, specialty_id=sid(spec_name), label=label, amount=amount, currency="TND", period=period, description=desc, **published))
                added["fees"] += 1

        for method, title, desc, installments, down in PAYMENTS.get(program.name, []):
            exists = db.scalar(select(PaymentTerm.id).where(PaymentTerm.program_id == program.id, PaymentTerm.specialty_id.is_(None), PaymentTerm.title == title))
            if exists is None:
                db.add(PaymentTerm(program_id=program.id, method=method, title=title, description=desc, installments=installments, down_payment_percent=down, **published))
                added["payment_terms"] += 1
    db.commit()
    return added
