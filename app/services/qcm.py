"""Targeted QCM: question bank, public view (no answers) and scoring.

Placeholder bank mirroring the frontend demo. The agentic layer is expected to generate
the questions per programme/profile; the API contract (questions without `correct`,
answers as {index: choice}) stays the same.
"""

SECTIONS = ["Logique & algorithmique", "Mathématiques", "Culture numérique"]

BANK: list[dict] = [
    {"section": SECTIONS[0], "text": "Quelle structure répète une action tant qu’une condition est vraie ?", "options": ["Une affectation", "Une boucle", "Un commentaire", "Une constante"], "correct": 1},
    {"section": SECTIONS[0], "text": "Que vaut « x » à la fin de ces instructions ?", "code": ["x ← 3", "x ← x × 2", "x ← x − 1"], "options": ["3", "5", "6", "7"], "correct": 1},
    {"section": SECTIONS[0], "text": "Quel est le rôle d’une condition « si … alors … sinon » ?", "options": ["Répéter un bloc", "Choisir entre deux chemins", "Déclarer une variable", "Arrêter le programme"], "correct": 1},
    {"section": SECTIONS[0], "text": "Combien de fois s’exécute cette boucle ?", "code": ["pour i allant de 2 à 6", "    afficher(i)", "fin pour"], "options": ["4", "5", "6", "7"], "correct": 1},
    {"section": SECTIONS[0], "text": "Que vaut la variable « total » à la fin de cet algorithme ?", "code": ["total ← 0", "pour i allant de 1 à 4", "    total ← total + i", "fin pour"], "options": ["4", "6", "10", "16"], "correct": 2},
    {"section": SECTIONS[1], "text": "Quelle est la valeur de 2³ + 3² ?", "options": ["12", "15", "17", "21"], "correct": 2},
    {"section": SECTIONS[1], "text": "La solution de 2x + 5 = 17 est :", "options": ["x = 5", "x = 6", "x = 11", "x = 12"], "correct": 1},
    {"section": SECTIONS[1], "text": "Quelle fraction est équivalente à 3/4 ?", "options": ["6/8", "9/16", "4/3", "3/8"], "correct": 0},
    {"section": SECTIONS[1], "text": "Quelle est la dérivée de f(x) = x² ?", "options": ["x", "2x", "x²", "2"], "correct": 1},
    {"section": SECTIONS[2], "text": "Que signifie le sigle « RAM » ?", "options": ["Mémoire vive", "Réseau d’accès mobile", "Registre d’adresses", "Routeur actif"], "correct": 0},
    {"section": SECTIONS[2], "text": "Quel est le meilleur réflexe pour un mot de passe ?", "options": ["Le réutiliser partout", "Le choisir long et unique", "Utiliser sa date de naissance", "Le partager avec un ami"], "correct": 1},
    {"section": SECTIONS[2], "text": "Que fait un navigateur web ?", "options": ["Il compile des programmes", "Il affiche des pages web", "Il répare le disque dur", "Il crée des mots de passe"], "correct": 1},
]

ADVICE = {
    SECTIONS[0]: "Bon raisonnement sur les étapes d’un algorithme. À revoir : les conditions et les cas limites.",
    SECTIONS[1]: "Des acquis à consolider en résolution de problèmes. Prenez le temps d’expliciter chaque étape.",
    SECTIONS[2]: "Des repères utiles. Approfondissez les notions de données et de sécurité numérique.",
}

# --- ISB bank (gestion / finance) --------------------------------------------------------------------------------------
ISB_SECTIONS = ["Calcul & raisonnement", "Culture économique & gestion", "Culture numérique"]

BANK_ISB: list[dict] = [
    {"section": ISB_SECTIONS[0], "text": "Un article à 80 DT bénéficie de 25 % de remise. Quel est le prix final ?", "options": ["55 DT", "60 DT", "65 DT", "20 DT"], "correct": 1},
    {"section": ISB_SECTIONS[0], "text": "Quelle est la valeur de 15 % de 200 ?", "options": ["15", "20", "30", "45"], "correct": 2},
    {"section": ISB_SECTIONS[0], "text": "Si 3 stylos coûtent 4,5 DT, combien coûtent 5 stylos ?", "options": ["6,5 DT", "7 DT", "7,5 DT", "9 DT"], "correct": 2},
    {"section": ISB_SECTIONS[0], "text": "La moyenne de 10, 12 et 14 est :", "options": ["11", "12", "13", "36"], "correct": 1},
    {"section": ISB_SECTIONS[1], "text": "Que mesure le chiffre d’affaires d’une entreprise ?", "options": ["Ses bénéfices", "Le total de ses ventes", "Ses dettes", "Son nombre d’employés"], "correct": 1},
    {"section": ISB_SECTIONS[1], "text": "À quoi sert principalement un budget ?", "options": ["Prévoir et suivre recettes et dépenses", "Recruter du personnel", "Fabriquer un produit", "Choisir un logo"], "correct": 0},
    {"section": ISB_SECTIONS[1], "text": "Que désigne l’inflation ?", "options": ["Une baisse générale des prix", "Une hausse générale et durable des prix", "Une hausse des salaires uniquement", "Une baisse du chômage"], "correct": 1},
    {"section": ISB_SECTIONS[1], "text": "Qu’est-ce qu’un intérêt ?", "options": ["Le prix payé pour emprunter de l’argent", "Une taxe sur les ventes", "Un salaire mensuel", "Un stock de marchandises"], "correct": 0},
    {"section": ISB_SECTIONS[2], "text": "À quoi sert un tableur ?", "options": ["Calculer et organiser des données", "Retoucher des photos", "Compiler du code", "Naviguer sur le web"], "correct": 0},
    {"section": ISB_SECTIONS[2], "text": "Quel est le meilleur réflexe pour un mot de passe ?", "options": ["Le réutiliser partout", "Le choisir long et unique", "Utiliser sa date de naissance", "Le partager avec un ami"], "correct": 1},
    {"section": ISB_SECTIONS[2], "text": "Qu’est-ce qu’un message d’hameçonnage (phishing) ?", "options": ["Un message qui cherche à voler des informations", "Une lettre d’information", "Une sauvegarde automatique", "Une mise à jour système"], "correct": 0},
    {"section": ISB_SECTIONS[2], "text": "Que fait un navigateur web ?", "options": ["Il compile des programmes", "Il affiche des pages web", "Il répare le disque dur", "Il crée des mots de passe"], "correct": 1},
]

# Harder replacements used for the preparatory / engineering tracks (same sections, same count).
ADVANCED_MATHS = [
    {"section": SECTIONS[1], "text": "Quelle est la limite de 1/x quand x tend vers +∞ ?", "options": ["0", "1", "+∞", "−∞"], "correct": 0},
    {"section": SECTIONS[1], "text": "On lance deux fois une pièce équilibrée. Quelle est la probabilité d’obtenir deux fois « face » ?", "options": ["1/2", "1/4", "1/3", "3/4"], "correct": 1},
]
DATA_QUESTION = {"section": SECTIONS[2], "text": "Quel type d’apprentissage automatique utilise des données étiquetées ?", "options": ["Apprentissage supervisé", "Compression de données", "Chiffrement", "Défragmentation"], "correct": 0}

GENERIC_ADVICE = "Notion à aborder pendant l’entretien pour identifier les besoins d’accompagnement."


def generate(institution: str | None, level: str | None, interests: list[str] | None = None, subjects: list[str] | None = None) -> list[dict]:
    """Targeted QCM (questions WITH the answer key, to be stored server-side).

    ISB programmes get the management/finance bank. IIT licence keeps the base bank. IIT prepa / engineering swap two
    basic maths questions for harder ones, and a candidate interested in AI/data gets one data question.
    """
    interests, subjects = interests or [], subjects or []
    if institution == "ISB":
        return [dict(q) for q in BANK_ISB]
    qs = [dict(q) for q in BANK]
    if level in ("prepa", "ingenierie"):
        qs[7], qs[8] = dict(ADVANCED_MATHS[0]), dict(ADVANCED_MATHS[1])
    if "ia_data" in interests:
        qs[11] = dict(DATA_QUESTION)
    return qs


def public_questions(questions: list[dict] | None = None) -> list[dict]:
    """Questions as sent to the candidate: never include the correct answer."""
    return [{k: v for k, v in q.items() if k != "correct"} for q in (questions or BANK)]


def has_key(questions: list[dict] | None) -> bool:
    return bool(questions) and all("correct" in q for q in questions)


def score(answers: dict[int, int], questions: list[dict] | None = None) -> dict:
    questions = questions if has_key(questions) else BANK
    sections = list(dict.fromkeys(q["section"] for q in questions))
    by_section = []
    for s in sections:
        idx = [i for i, q in enumerate(questions) if q["section"] == s]
        good = sum(1 for i in idx if answers.get(i) == questions[i]["correct"])
        by_section.append({"section": s, "good": good, "total": len(idx), "pct": round(100 * good / len(idx)), "advice": ADVICE.get(s, GENERIC_ADVICE)})
    good = sum(s["good"] for s in by_section)
    total = len(questions)
    pct = round(100 * good / total)
    if pct >= 70:
        summary = "Des bases à mobiliser pendant l’entretien, et quelques notions à approfondir ensemble."
    elif pct >= 40:
        summary = "Des acquis à consolider : l’entretien permettra d’identifier les sujets à travailler ensemble."
    else:
        summary = "Un point de départ : le conseiller vous aidera à construire un parcours de remise à niveau."
    return {"good": good, "total": total, "pct": pct, "by_section": by_section, "summary": summary}


def interview_points(result: dict | None, profile, program_name: str | None) -> list[str]:
    """Talking points for the interviewer, from the QCM result and the candidate profile."""
    pts: list[str] = []
    if result:
        for s in result["by_section"]:
            if s["pct"] < 60:
                pts.append(f"Revenir sur « {s['section']} » ({s['good']}/{s['total']}).")
    else:
        pts.append("Le QCM n’est pas encore terminé : évaluer les acquis à l’oral.")
    goal = getattr(profile, "career_goal", None)
    if goal:
        pts.append(f"Explorer le projet professionnel : {goal}.")
    style = (getattr(profile, "constraints", None) or {}).get("style")
    if style:
        pts.append("Discuter de la préférence d’apprentissage : " + ", ".join(style) + ".")
    if program_name:
        pts.append(f"Vérifier les prérequis et la motivation pour « {program_name} ».")
    pts.append("Confirmer la disponibilité du relevé de notes, la mobilité et le budget.")
    return pts
