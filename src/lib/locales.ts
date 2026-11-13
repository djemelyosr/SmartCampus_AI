import type { Lang } from "./i18n";

type Tr = { en: string; ar: string };

/**
 * Translations keyed by the French source text. `t("texte français")` returns the text unchanged in French,
 * and the translation below in English / Arabic (falls back to French when a key is missing).
 * To translate another screen: wrap its strings with `t(...)` and add the entries here.
 */
export const DICT: Record<string, Tr> = {
  // Navigation
  "Découvrir les formations": { en: "Discover the programmes", ar: "اكتشف التكوينات" },
  "Besoin d’aide ?": { en: "Need help?", ar: "هل تحتاج إلى مساعدة؟" },
  "Se connecter": { en: "Sign in", ar: "تسجيل الدخول" },
  "Déconnexion": { en: "Sign out", ar: "تسجيل الخروج" },
  "Se déconnecter": { en: "Sign out", ar: "تسجيل الخروج" },
  "Mon profil": { en: "My profile", ar: "ملفي الشخصي" },
  "Notifications": { en: "Notifications", ar: "الإشعارات" },
  "Ajouter aux favoris": { en: "Add to favourites", ar: "أضف إلى المفضلة" },
  "Retirer des favoris": { en: "Remove from favourites", ar: "إزالة من المفضلة" },
  "Mes favoris": { en: "My favourites", ar: "مفضلتي" },
  "Écouter la réponse": { en: "Listen to the answer", ar: "استمع إلى الإجابة" },
  "Arrêter la lecture": { en: "Stop reading", ar: "إيقاف القراءة" },
  "Écouter": { en: "Listen", ar: "استماع" },
  "Arrêter": { en: "Stop", ar: "إيقاف" },
  "Langue": { en: "Language", ar: "اللغة" },
  "MON PARCOURS": { en: "MY JOURNEY", ar: "مساري" },
  "MON ORIENTATION": { en: "MY GUIDANCE", ar: "توجيهي" },
  "MES FORMATIONS": { en: "MY PROGRAMMES", ar: "تكويناتي" },
  "MA CANDIDATURE": { en: "MY APPLICATION", ar: "ترشحي" },
  "MES RENDEZ-VOUS": { en: "MY APPOINTMENTS", ar: "مواعيدي" },
  "DOSSIERS CANDIDATS": { en: "APPLICANT FILES", ar: "ملفات المترشحين" },
  "ENTRETIENS": { en: "INTERVIEWS", ar: "المقابلات" },
  "PILOTAGE": { en: "DASHBOARD", ar: "القيادة والمتابعة" },
  "ADMINISTRATION": { en: "ADMINISTRATION", ar: "الإدارة" },
  "Espace candidat": { en: "Applicant area", ar: "فضاء المترشح" },
  "Responsable académique": { en: "Academic head", ar: "المسؤول الأكاديمي" },
  "Responsable entretien": { en: "Interview manager", ar: "مسؤول المقابلات" },
  "Direction": { en: "Management", ar: "الإدارة العليا" },
  "Administrateur": { en: "Administrator", ar: "المشرف" },

  // Home
  "ORIENTATION IIT & ISB · ACCÈS LIBRE": { en: "IIT & ISB GUIDANCE · OPEN ACCESS", ar: "التوجيه IIT وISB · وصول حر" },
  "Votre avenir commence": { en: "Your future starts", ar: "مستقبلك يبدأ" },
  "par une conversation.": { en: "with a conversation.", ar: "بمحادثة." },
  "Un doute entre Licence, Prépa, Ingénierie ou les formations ISB ? Échangez avec SmartCampus et explorez des pistes adaptées à votre projet.": {
    en: "Unsure between a Bachelor's, Prep, Engineering or the ISB programmes? Chat with SmartCampus and explore options that fit your plans.",
    ar: "هل أنت متردد بين الإجازة أو السنة التحضيرية أو الهندسة أو تكوينات ISB؟ تحدّث مع SmartCampus واكتشف مسارات تناسب مشروعك.",
  },
  "Aucune inscription pour discuter ou comparer les formations.": { en: "No sign-up needed to chat or compare programmes.", ar: "لا حاجة للتسجيل للتحدث أو مقارنة التكوينات." },
  "Français, dialecte tunisien ou Arabizi · Texte et audio.": { en: "French, Tunisian dialect or Arabizi · Text and audio.", ar: "الفرنسية أو الدارجة التونسية أو العربيزي · نص وصوت." },
  "J’ai déjà un compte": { en: "I already have an account", ar: "لدي حساب بالفعل" },
  "Un guide à vos côtés": { en: "A guide by your side", ar: "مرشد إلى جانبك" },
  "FRANÇAIS · TOUNSI · ARABIZI": { en: "FRENCH · TOUNSI · ARABIZI", ar: "فرنسية · تونسي · عربيزي" },
  "Une question sur votre orientation ?": { en: "A question about your guidance?", ar: "سؤال حول توجيهك؟" },
  "Cliquez sur l’icône de conversation en bas à droite. Le guide s’ouvre ici, sans quitter l’accueil.": {
    en: "Click the chat icon at the bottom right. The guide opens here, without leaving the home page.",
    ar: "اضغط على أيقونة المحادثة في أسفل الصفحة. يفتح المرشد هنا دون مغادرة الصفحة الرئيسية.",
  },
  "Accès libre, sans compte · Échangez par texte ou audio à votre rythme.": { en: "Open access, no account · Chat by text or audio at your own pace.", ar: "وصول حر دون حساب · تحدّث كتابة أو صوتًا حسب وتيرتك." },
  "Échanger": { en: "Chat", ar: "تحدّث" },
  "Chatbot libre, texte ou audio.": { en: "Free chatbot, text or audio.", ar: "روبوت محادثة حر، نص أو صوت." },
  "S’orienter": { en: "Find your path", ar: "اختر مسارك" },
  "Comparer les pistes et les formations.": { en: "Compare options and programmes.", ar: "قارن بين المسارات والتكوينات." },
  "Se préinscrire": { en: "Pre-register", ar: "التسجيل المسبق" },
  "Créer un compte et transmettre le dossier.": { en: "Create an account and submit your file.", ar: "أنشئ حسابًا وأرسل ملفك." },
  "Passer le QCM": { en: "Take the quiz", ar: "اجتياز الاختبار" },
  "Préparer l’entretien avec un bilan ciblé.": { en: "Prepare for the interview with a targeted assessment.", ar: "حضّر للمقابلة بتقييم موجّه." },
  "Rencontrer et suivre": { en: "Meet and follow up", ar: "المقابلة والمتابعة" },
  "Réserver, échanger et suivre la décision.": { en: "Book, talk and follow the decision.", ar: "احجز وتواصل وتابع القرار." },
  "Un parcours simple, dans le bon ordre": { en: "A simple journey, in the right order", ar: "مسار بسيط وبالترتيب الصحيح" },
  "Un compte seulement pour aller plus loin": { en: "An account only to go further", ar: "حساب فقط للمضي أبعد" },
  "Sauvegardez vos échanges, retrouvez vos choix et suivez votre candidature. La création du compte ne vaut pas préinscription.": {
    en: "Save your conversations, find your choices again and follow your application. Creating an account is not a pre-registration.",
    ar: "احفظ محادثاتك واسترجع اختياراتك وتابع ترشحك. إنشاء الحساب لا يعني التسجيل المسبق.",
  },
  "Créer mon compte candidat": { en: "Create my applicant account", ar: "إنشاء حساب المترشح" },
  "L’IA vous guide. Vous gardez le choix.": { en: "AI guides you. You keep the choice.", ar: "الذكاء الاصطناعي يرشدك. والقرار قرارك." },
  "Un conseiller peut prendre le relais. L’orientation et le QCM sont des aides : seule l’équipe habilitée de l’établissement décide de l’admission.": {
    en: "An advisor can take over. Guidance and the quiz are aids: only the institution's authorised team decides on admission.",
    ar: "يمكن لمستشار أن يتولى المتابعة. التوجيه والاختبار مجرد مساعدة: الفريق المخوّل بالمؤسسة وحده يقرر القبول.",
  },
  "Contacter les admissions": { en: "Contact admissions", ar: "الاتصال بمصلحة القبول" },
  "Maquette de démonstration · Formations, conditions d’accès et sources à confirmer auprès de l’IIT / ISB. Accès équipe réservé aux comptes habilités.": {
    en: "Demo mock-up · Programmes, admission requirements and sources to be confirmed with IIT / ISB. Team access reserved for authorised accounts.",
    ar: "نموذج تجريبي · يجب التأكد من التكوينات وشروط القبول والمصادر لدى IIT / ISB. الدخول الخاص بالفريق مخصص للحسابات المخوّلة.",
  },
};

export const LANGS: { code: Lang; label: string; dir: "ltr" | "rtl" }[] = [
  { code: "fr", label: "Français", dir: "ltr" },
  { code: "en", label: "English", dir: "ltr" },
  { code: "ar", label: "العربية", dir: "rtl" },
];
