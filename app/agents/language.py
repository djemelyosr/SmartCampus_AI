"""Language detection (fr | tn | arabizi), accent-free normalisation and concept lexicon.

tn      = Tunisian / Arabic written in Arabic script
arabizi = Tunisian written in Latin letters with digits (3, 7, 9, 5, 2...)
fr      = French (default). Code-switching: the dominant script/lexicon wins.
"""

import re
import unicodedata

_ARABIC = re.compile(r"[\u0600-\u06FF]")
_ARABIZI_DIGITS = re.compile(r"\b\w*[a-z][23579][a-z]\w*\b|\b[23579][a-z]{2,}\b|\b[a-z]{2,}[23579]\b", re.I)
_ARABIZI_WORDS = {
    "nheb", "n7eb", "nehb", "7ab", "barcha", "behi", "bahi", "chnowa", "chnoua", "chnia", "mouch", "mich", "3lech", "3leh",
    "kifech", "kifah", "famma", "fama", "ya3ni", "yaani", "bech", "tawa", "fhemt", "brabi", "yesser", "yasser", "sahbi",
    "3andi", "3andek", "9rit", "9ra", "nkamel", "nokhdem", "khedma", "5edma", "ena", "enti", "winou", "wakteh", "9adech",
    "bsh", "mazelt", "mazal", "ken", "kif", "taw", "lyom", "ghodwa", "mta3", "mte3", "el", "bel", "fil", "lel", "nzid",
    "ntsajel", "nsajel", "nse77", "n9ra", "nji", "ma3andi", "nchoufou", "chouf", "ahki", "9olli", "9oulli",
}


def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def norm(text: str) -> str:
    """Lowercase, accent-free, apostrophes removed (keeps Arabic letters and digits)."""
    t = strip_accents(text.lower()).replace("’", "'").replace("'", "")
    t = re.sub(r"[\u064B-\u065F\u0640]", "", t)  # Arabic diacritics / tatweel
    return t


def tokens(text: str) -> list[str]:
    return re.findall(r"[\w\u0600-\u06FF]+", norm(text))


def detect_language(text: str) -> str:
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return "fr"
    arabic_ratio = sum(1 for c in letters if _ARABIC.match(c)) / len(letters)
    if arabic_ratio >= 0.4:
        return "tn"
    toks = set(tokens(text))
    hits = len(toks & _ARABIZI_WORDS) + len(_ARABIZI_DIGITS.findall(norm(text)))
    if hits >= 1 and (hits >= 2 or len(toks) <= 6):
        return "arabizi"
    if arabic_ratio > 0.15:
        return "tn"
    return "fr"


# Canonical concept -> trigger words (French, Arabizi, Arabic script). Matching is done on norm()ed tokens/substrings.
CONCEPTS: dict[str, tuple[str, ...]] = {
    "maths": ("math", "maths", "mathematiques", "ryadhiyet", "riyadhiyat", "ryadhiyat", "رياضيات", "رياضة"),
    "informatique": ("informatique", "info ", "programmation", "coding", "code", "ordinateur", "ordi", "developpement", "logiciel", "software", "informatik", "iformatik", "إعلامية", "اعلامية", "برمجة", "كمبيوتر"),
    "ia_data": ("intelligence artificielle", " ia ", "data", "donnees", "machine learning", "ذكاء", "بيانات"),
    "physique": ("physique", "fizik", "physic", "فيزياء"),
    "gestion": ("gestion", "management", "business", "entreprise", "marketing", "tasarouf", "tasarof", "تصرف", "تجارة", "مؤسسة"),
    "finance": ("finance", "banque", "bourse", "comptabilite", "audit", "مالية", "بنك", "محاسبة"),
    "ingenierie": ("ingenieur", "ingenierie", "engineering", "mohandes", "muhandis", "مهندس", "هندسة"),
    "prepa": ("prepa", "preparatoire", "concours", "tahdhiriya", "تحضيرية"),
    "licence": ("licence", "lmd", "license", "ليسانس"),
    "pratique": ("pratique", "projet", "projets", "concret", "terrain", "stage", "tatbiqi", "تطبيقي", "مشروع"),
    "progressif": ("progressif", "progressive", "pas a pas", "step by step", "tadrij", "تدريجي", "doucement"),
}

INTENTS: dict[str, tuple[str, ...]] = {
    "human": ("conseiller", "humain", "parler a quelqu", "responsable", "insan", "إنسان", "مستشار"),
    "preinscription": ("preinscri", "pre-inscri", "inscrire", "inscription", "candidature", "nsajel", "ntsajel", "nsajjel", "نسجل", "تسجيل", "ترشح"),
    "rdv": ("rendez-vous", "rendez vous", "rdv", "entretien", "maw3ed", "maw3id", "موعد", "مقابلة"),
    "qcm": ("qcm", "quiz", "questionnaire", "test de", "اختبار"),
    "compare": ("compar", "difference", "different", "versus", " vs ", "ou bien", "farq", "fark", "9arenli", "قارن", "فرق", "الفرق"),
    "conditions": ("condition", "admission", "prerequis", "pre-requis", "dossier", "moyenne", "chrouta", "shorout", "شروط", "قبول"),
    "debouches": ("debouche", "metier", "carriere", "emploi", "travail", "salaire", "khedma", "5edma", "khidma", "خدمة", "شغل", "وظيفة"),
    "duree": ("duree", "combien d'annee", "combien dannee", "annees", "9adech", "9addech", "كم سنة", "مدة"),
    "frais": (" frais", "tarif", "scolarite", " cout", " prix", "ma3alim", "m3alim", "mesrouf", "msarif", "masarif", "flous", "floss", "floos", "معاليم", "مصاريف", "فلوس", "تكلفة", "سعر", "معلوم"),
    "paiement": ("paiement", "payement", "payer", "tranche", "virement", "cheque", "echelonn", "mensualite", "versement", "n5alles", "nkhalles", "5alles", "khalles", "نخلص", "الدفع", "دفع", "تقسيط", "نقسط"),
    "greeting": ("bonjour", "salut", "bonsoir", "hello", "hi ", "salam", "aslema", "aslama", "3aslema", "عسلامة", "مرحبا", "السلام", "صباح الخير"),
    "thanks": ("merci", "thanks", "barakallah", "yaatik", "ya3tik", "عيشك", "يعطيك", "شكرا"),
}


def concepts_in(text: str) -> list[str]:
    t = " " + norm(text) + " "
    return [c for c, words in CONCEPTS.items() if any(norm(w) in t for w in words)]


STRONG_PREINSCRIPTION = ("preinscri", "pre-inscri", "inscrire", "candidature", "nsajel", "ntsajel", "nsajjel", "نسجل", "ترشح")
STRONG_DUREE = ("duree", "annees", "كم سنة", "مدة")


def intents_in(text: str) -> list[str]:
    t = " " + norm(text) + " "
    found = [i for i, words in INTENTS.items() if any(norm(w) in t for w in words)]
    if {"frais", "paiement"} & set(found):
        # "frais d'inscription" is a question about money, not a request to register; "9adech" ("how much") is not a duration
        if "preinscription" in found and not any(norm(w) in t for w in STRONG_PREINSCRIPTION):
            found.remove("preinscription")
        if "duree" in found and not any(norm(w) in t for w in STRONG_DUREE):
            found.remove("duree")
        # "conditions de paiement" are payment terms, not admission conditions
        if "conditions" in found and "paiement" in found and re.search(r"conditions? (?:de|du|d|des) ?(?:paiement|payement|reglement)|conditions? financier", t):
            found.remove("conditions")
    return found
