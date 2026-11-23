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


def public_questions() -> list[dict]:
    """Questions as sent to the candidate: never include the correct answer."""
    return [{k: v for k, v in q.items() if k != "correct"} for q in BANK]


def score(answers: dict[int, int]) -> dict:
    by_section = []
    for s in SECTIONS:
        idx = [i for i, q in enumerate(BANK) if q["section"] == s]
        good = sum(1 for i in idx if answers.get(i) == BANK[i]["correct"])
        by_section.append({"section": s, "good": good, "total": len(idx), "pct": round(100 * good / len(idx)), "advice": ADVICE[s]})
    good = sum(s["good"] for s in by_section)
    total = len(BANK)
    pct = round(100 * good / total)
    if pct >= 70:
        summary = "Des bases à mobiliser pendant l’entretien, et quelques notions à approfondir ensemble."
    elif pct >= 40:
        summary = "Des acquis à consolider : l’entretien permettra d’identifier les sujets à travailler ensemble."
    else:
        summary = "Un point de départ : le conseiller vous aidera à construire un parcours de remise à niveau."
    return {"good": good, "total": total, "pct": pct, "by_section": by_section, "summary": summary}
