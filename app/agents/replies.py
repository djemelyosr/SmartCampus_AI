"""Reply templates in French (fr), Tunisian in Arabic script (tn) and Arabizi (arabizi)."""

T: dict[str, dict[str, str]] = {
    "greeting": {
        "fr": "Bonjour ! Je suis votre guide SmartCampus. Parlez-moi de vos matières préférées, de vos envies et de vos hésitations : je vous aide à explorer les formations de l’IIT et de l’ISB.",
        "tn": "أهلا بيك! أنا دليلك في SmartCampus. قلي على المواد اللي تحبها وشنوة تحب تعمل في المستقبل، وأنا نعاونك تكتشف التكوينات متاع IIT و ISB.",
        "arabizi": "Ahla bik ! Ena el guide mta3ek fi SmartCampus. 9olli 3al mawed elli t7ebhom w chnowa t7eb ta3mel fil mosta9bal, w na3awnek tektachef el formations mta3 IIT w ISB.",
    },
    "ack_ask": {
        "fr": "Merci, j’ai noté : {noted}. ",
        "tn": "يعطيك الصحة، سجلت: {noted}. ",
        "arabizi": "Yaatik essa7a, sajalt : {noted}. ",
    },
    "q_subjects": {
        "fr": "Quelles matières préférez-vous (maths, physique, informatique…) ?",
        "tn": "شنوة المواد اللي تحبها أكثر (رياضيات، فيزياء، إعلامية…)؟",
        "arabizi": "Chnowa el mawed elli t7ebhom akther (maths, physique, info…) ?",
    },
    "q_goal": {
        "fr": "Quel domaine ou métier vous attire pour plus tard ?",
        "tn": "شنوة الميدان ولا الخدمة اللي تحب تخدمها في المستقبل؟",
        "arabizi": "Chnowa el domaine walla el khedma elli t7eb tokhdemha fil mosta9bal ?",
    },
    "q_level": {
        "fr": "Quel est votre niveau actuel (type de bac, année) ?",
        "tn": "في أي مستوى أنت توا (شعبة الباكالوريا، السنة)؟",
        "arabizi": "Fi anehi mostawa enti tawa (bac chnoua, el 3am) ?",
    },
    "q_style": {
        "fr": "Préférez-vous une voie pratique et progressive, ou plus théorique ?",
        "tn": "تفضل مسار تطبيقي وتدريجي ولا نظري أكثر؟",
        "arabizi": "T7eb parcours pratique w graduel walla théorique akther ?",
    },
    "short_intro": {
        "fr": "D’après votre profil, voici {n} piste(s) à explorer (sans vous imposer de choix) :\n",
        "tn": "حسب الملف متاعك، هاذم {n} اختيارات تنجم تشوفهم (من غير ما نفرض عليك حاجة):\n",
        "arabizi": "Hasb el profil mta3ek, hethom {n} options tnajem tchoufhom (men ghir ma nfard 3lik chay) :\n",
    },
    "short_line": {
        "fr": "• {name} ({inst}) — compatibilité {score} % · points communs : {matched}\n",
        "tn": "• {name} ({inst}) — توافق {score}% · نقاط مشتركة: {matched}\n",
        "arabizi": "• {name} ({inst}) — compatibilité {score} % · nou9at moshtaraka : {matched}\n",
    },
    "short_outro": {
        "fr": "\nVoulez-vous que je compare ces parcours, détaille les conditions d’accès ou lance la préinscription ?",
        "tn": "\nتحب نقارنلك بيناتهم، نفسرلك شروط القبول ولا نبدا التسجيل المبدئي؟",
        "arabizi": "\nT7eb n9arenlek binethom, nfassarlek chrout el 9bol walla nebda el préinscription ?",
    },
    "compare_intro": {
        "fr": "Comparaison (sources officielles IIT/ISB) :\n",
        "tn": "المقارنة (من المصادر الرسمية IIT/ISB):\n",
        "arabizi": "El mouqarana (men el masader errasmiya IIT/ISB) :\n",
    },
    "compare_line": {
        "fr": "• {name} ({inst}) — durée : {duration} · débouchés : {careers} · accès : {requirements}\n",
        "tn": "• {name} ({inst}) — المدة: {duration} · الآفاق: {careers} · الشروط: {requirements}\n",
        "arabizi": "• {name} ({inst}) — modda : {duration} · débouchés : {careers} · chrouta : {requirements}\n",
    },
    "compare_need": {
        "fr": "Quels parcours voulez-vous comparer (par exemple Prépa et Licence) ?",
        "tn": "شنوة هي المسارات اللي تحب نقارنلك بيناتهم (مثلا Prépa و Licence)؟",
        "arabizi": "Anehom el parcours elli t7eb n9arenlek binethom (par exemple Prépa w Licence) ?",
    },
    "info_conditions": {"fr": "Conditions d’accès — {name} ({inst}) : {text}", "tn": "شروط القبول — {name} ({inst}): {text}", "arabizi": "Chrouta el 9bol — {name} ({inst}) : {text}"},
    "info_debouches": {"fr": "Débouchés — {name} ({inst}) : {text}", "tn": "الآفاق المهنية — {name} ({inst}): {text}", "arabizi": "Débouchés — {name} ({inst}) : {text}"},
    "info_duree": {"fr": "Durée — {name} ({inst}) : {text}", "tn": "المدة — {name} ({inst}): {text}", "arabizi": "Modda — {name} ({inst}) : {text}"},
    "info_general": {"fr": "{name} ({inst}) : {text}", "tn": "{name} ({inst}): {text}", "arabizi": "{name} ({inst}) : {text}"},
    "no_source": {
        "fr": "Je n’ai pas d’information officielle validée sur ce point, et je préfère ne rien inventer (conditions, frais…). Je peux transmettre votre question à un conseiller de l’IIT/ISB.",
        "tn": "ما عنديش معلومة رسمية مؤكدة على النقطة هاذي، وما نحبش نخترع (شروط، معاليم…). نجم نبعث سؤالك لمستشار في IIT/ISB.",
        "arabizi": "Ma 3andich ma3louma rasmiya mou2akeda 3al no9ta hethi, w ma n7ebch nekhtare3 (chrouta, ma3alim…). Nnajem nab3eth so2alek l conseiller mta3 IIT/ISB.",
    },
    "preinsc_created": {
        "fr": "C’est fait : votre préinscription à « {name} » ({inst}) est créée en brouillon. Complétez-la depuis la rubrique Préinscription de votre espace ; le QCM ciblé et le rendez-vous suivront. La décision d’admission reste prise par l’équipe.",
        "tn": "تمّ: الترشح المبدئي متاعك لـ «{name}» ({inst}) تسجّل كمسودة. كمّلو من خانة Préinscription في فضاءك؛ بعدها يجيك الـ QCM والموعد. قرار القبول النهائي ياخذوه الفريق.",
        "arabizi": "Tamma : el préinscription mta3ek l « {name} » ({inst}) tsajjlet brouillon. Kammelha men rubrique Préinscription fi espace mta3ek ; baed yjik el QCM w el maw3ed. Qarar el 9bol ya5dhou el équipe.",
    },
    "preinsc_exists": {
        "fr": "Vous avez déjà une préinscription pour « {name} ». Retrouvez-la dans votre espace pour la compléter.",
        "tn": "عندك ترشح مبدئي لـ «{name}» من قبل. لقاه في فضاءك باش تكمله.",
        "arabizi": "3andek déjà préinscription l « {name} ». Lawwej 3liha fi espace mta3ek bech tkammelha.",
    },
    "preinsc_consent": {
        "fr": "Pour créer la préinscription, j’ai besoin de votre consentement au traitement de vos données : cochez-le dans votre profil, puis redemandez-moi.",
        "tn": "باش نعمل الترشح المبدئي نحتاج موافقتك على معالجة المعطيات متاعك: علّمها في البروفيل متاعك وبعد عاود قولي.",
        "arabizi": "Bech na3mel el préinscription na7tej mouwafa9tek 3al ma3lomet: 3allemha fil profil mta3ek w ba3d 3awed 9olli.",
    },
    "preinsc_which": {
        "fr": "Quel parcours souhaitez-vous choisir pour la préinscription ? Dites-moi son nom.",
        "tn": "شنوة هو المسار اللي تحب تترشح ليه؟ قلي إسمو.",
        "arabizi": "Anehou el parcours elli t7eb tetrashah lih ? 9olli ismou.",
    },
    "rdv": {
        "fr": "Une fois la préinscription et le QCM terminés, vous pouvez réserver un créneau d’entretien dans la rubrique Rendez-vous de votre espace. Je vous enverrai un rappel.",
        "tn": "بعد ما تكمل الترشح المبدئي والـ QCM، تنجم تحجز موعد المقابلة من خانة Rendez-vous في فضاءك. وأنا نبعثلك تذكير.",
        "arabizi": "Baed ma tkammel el préinscription w el QCM, tnajem te7jez maw3ed el entretien men rubrique Rendez-vous fi espace mta3ek. W ena nab3athlek rappel.",
    },
    "qcm": {
        "fr": "Après votre préinscription, un QCM ciblé selon le parcours et votre profil est généré dans votre espace. Il aide le responsable d’entretien à préparer l’échange.",
        "tn": "بعد الترشح المبدئي يتولّد QCM على قدّ المسار والملف متاعك في فضاءك. يعاون مسؤول المقابلة يحضّر.",
        "arabizi": "Baed el préinscription, yetwalled QCM 3ala 9add el parcours w el profil mta3ek fi espace mta3ek. Y3awen el responsable entretien yhadher.",
    },
    "handoff": {
        "fr": "Je transmets votre demande à un conseiller humain de l’équipe admissions IIT/ISB, qui vous répondra. Les décisions officielles (admission, équivalences, frais) ne sont jamais prises par l’IA.",
        "tn": "نبعث طلبك لمستشار من فريق القبول IIT/ISB باش يرد عليك. القرارات الرسمية (القبول، المعادلات، المعاليم) ما تاخذهاش الذكاء الاصطناعي.",
        "arabizi": "Nab3eth talabek l conseiller men équipe admissions IIT/ISB bech yrod 3lik. El qararat errasmiya (9bol, mo3adalet, ma3alim) ma ya5dhouhech l IA.",
    },
    "thanks": {"fr": "Avec plaisir ! Autre chose à explorer ?", "tn": "بالرحبى! عندك حاجة أخرى؟", "arabizi": "Bel ra7ba ! 3andek chay o5ra ?"},
    "info_fees": {
        "fr": "Frais de scolarité — {name} ({inst}) :\n{text}",
        "tn": "معاليم الدراسة — {name} ({inst}):\n{text}",
        "arabizi": "Ma3alim el dirassa — {name} ({inst}) :\n{text}",
    },
    "info_payment": {
        "fr": "Modalités de paiement — {name} ({inst}) :\n{text}",
        "tn": "طرق الدفع — {name} ({inst}):\n{text}",
        "arabizi": "Toro9 el khlass — {name} ({inst}) :\n{text}",
    },
    "fees_none": {
        "fr": "Aucun tarif officiel valide n’est publié pour « {name} » ({inst}) pour le moment.",
        "tn": "ما فما حتى معاليم رسمية صالحة منشورة لـ «{name}» ({inst}) توّا.",
        "arabizi": "Ma famma 7atta ma3alim rasmiya salha manchoura l « {name} » ({inst}) tawa.",
    },
    "payment_none": {
        "fr": "Aucune modalité de paiement officielle valide n’est publiée pour « {name} » ({inst}) pour le moment.",
        "tn": "ما فما حتى طريقة دفع رسمية صالحة منشورة لـ «{name}» ({inst}) توّا.",
        "arabizi": "Ma famma 7atta tari9a dfa3 rasmiya salha manchoura l « {name} » ({inst}) tawa.",
    },
    "fee_line": {
        "fr": "• {label} : {amount} {currency} ({period}){valid}",
        "tn": "• {label}: {amount} {currency} ({period}){valid}",
        "arabizi": "• {label} : {amount} {currency} ({period}){valid}",
    },
    "pay_line": {
        "fr": "• {title} ({method}){details}",
        "tn": "• {title} ({method}){details}",
        "arabizi": "• {title} ({method}){details}",
    },
    "cond_line": {
        "fr": "• {title}{optional}{threshold}{desc}",
        "tn": "• {title}{optional}{threshold}{desc}",
        "arabizi": "• {title}{optional}{threshold}{desc}",
    },
    "valid_until": {"fr": " — valable jusqu’au {date}", "tn": " — صالح حتى {date}", "arabizi": " — salah hatta {date}"},
    "pay_installments": {"fr": ", en {n} versements", "tn": "، على {n} أقساط", "arabizi": ", 3ala {n} a9sat"},
    "pay_down": {"fr": ", dont {p} % à l’inscription", "tn": "، منها {p}% عند التسجيل", "arabizi": ", menhom {p} % wa9t el inscription"},
    "pay_due": {"fr": ", avant le {date}", "tn": "، قبل {date}", "arabizi": ", 9bal {date}"},
    "cond_optional": {"fr": " (facultatif)", "tn": " (اختياري)", "arabizi": " (ikhtiyari)"},
    "cond_threshold": {"fr": " — seuil : {t}", "tn": " — الحد الأدنى: {t}", "arabizi": " — seuil : {t}"},
    "official_note": {
        "fr": "Informations officielles en vigueur à ce jour ; un conseiller IIT/ISB peut confirmer tout point.",
        "tn": "معلومات رسمية سارية اليوم؛ مستشار من IIT/ISB ينجم يأكدلك أي نقطة.",
        "arabizi": "Ma3lomet rasmiya sariya lyoum ; conseiller men IIT/ISB ynajem y2akedlek ay no9ta.",
    },
    "fallback": {
        "fr": "Je veux bien vous aider. Parlez-moi de vos matières préférées, de votre projet ou posez une question sur un parcours (conditions, durée, débouchés).",
        "tn": "يعطيك الصحة، نعاونك. قلي على المواد اللي تحبها ولا مشروعك، ولا اسأل على أي مسار (الشروط، المدة، الآفاق).",
        "arabizi": "Na3awnek bkol far7a. 9olli 3al mawed elli t7ebhom walla el projet mta3ek, walla es2el 3la ay parcours (chrouta, modda, débouchés).",
    },
}

QUICK: dict[str, dict[str, list[str]]] = {
    "shortlist": {
        "fr": ["Comparer ces parcours", "Conditions d’accès", "Lancer la préinscription"],
        "tn": ["قارن بين المسارات", "شروط القبول", "ابدا الترشح المبدئي"],
        "arabizi": ["9arenli el parcours", "Chrouta el 9bol", "Nebda el préinscription"],
    },
    "greeting": {
        "fr": ["J’hésite entre Prépa et Licence", "Je veux comparer les formations"],
        "tn": ["مختار بين Prépa و Licence", "نحب نقارن بين التكوينات"],
        "arabizi": ["Na7ar bin Prépa w Licence", "N7eb n9aren el formations"],
    },
}


def tr(key: str, lang: str, **kw) -> str:
    d = T[key]
    return d.get(lang, d["fr"]).format(**kw) if kw else d.get(lang, d["fr"])


PERIOD: dict[str, dict[str, str]] = {
    "annual": {"fr": "par an", "tn": "في العام", "arabizi": "fil 3am"},
    "semester": {"fr": "par semestre", "tn": "في السداسي", "arabizi": "fil semestre"},
    "one_time": {"fr": "une seule fois", "tn": "مرة وحدة", "arabizi": "mara wa7da"},
}
METHOD: dict[str, dict[str, str]] = {
    "bank_transfer": {"fr": "virement bancaire", "tn": "تحويل بنكي", "arabizi": "virement bancaire"},
    "cash": {"fr": "espèces", "tn": "نقدا", "arabizi": "cash"},
    "cheque": {"fr": "chèque", "tn": "شيك", "arabizi": "chèque"},
    "card": {"fr": "carte bancaire", "tn": "بطاقة بنكية", "arabizi": "carte bancaire"},
    "online": {"fr": "paiement en ligne", "tn": "دفع إلكتروني", "arabizi": "paiement en ligne"},
    "other": {"fr": "autre mode", "tn": "طريقة أخرى", "arabizi": "tari9a o5ra"},
}


def label(table: dict[str, dict[str, str]], key: str, lang: str) -> str:
    d = table.get(key, {})
    return d.get(lang) or d.get("fr") or key
