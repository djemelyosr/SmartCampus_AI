"""Supervisor of the agentic layer (language -> memory -> intent -> planning -> tools -> reply).

run_agent() keeps its original signature, so the routes are unchanged. Steps are traced in meta["trace"].
Every tool is deterministic and sourced (Program catalogue / DocumentChunk). An optional LLM can later
rephrase the reply in `llm.polish()` (existing Derja model, no fine-tuning) without changing planning, tools or the human-in-the-loop rules.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents import llm, orientation, profile as prof, rag
from app.agents.language import detect_language, intents_in, tokens
from app.agents.replies import METHOD, PERIOD, QUICK, label, tr
from app.core.dates import tn_today
from app.models.models import Conversation, PreRegistration, Program, User
from app.services import session_memory as sm
from app.services.official_info import official_info

DECISION_TOKENS = {"admis", "admise", "accepte", "acceptee", "maqboul", "مقبول", "مقبولة"}
RESUMABLE = {"preinscription", "compare"}  # requests the agent interrupted by asking a question
MAX_FOLLOWUP_TOKENS = 8  # a bare answer is short; a long message is a new request
GUEST_SIGNUP = {  # a pre-registration needs an account: the visitor is invited to create one, nothing is stored
    "fr": "Pour faire une pré-inscription, il faut un compte candidat (gratuit). Créez-le via « Créer un compte » : vous pourrez ensuite la lancer ici en un message. En attendant, je peux vous renseigner sur les formations, les conditions et les frais.",
    "tn": "باش تعمل تسجيل أوّلي لازمك حساب مترشّح (ببلاش). اعمل حسابك من «إنشاء حساب» و بعدها نعمللك التسجيل هنا. وقتها نجّم نعاونك على الاختصاصات و الشروط و المصاريف.",
    "arabizi": "Bech ta3mel pré-inscription lazmek compte candidat (gratuit). A3mel compte men « Créer un compte » w baed na3mlek l'inscription houni. Fil wa9t hedha n9dar n3awnek fil formations, les conditions w les frais.",
}
NOTED = {"subjects": "matières", "interests": "centres d’intérêt", "goal": "objectif", "level": "niveau", "style": "préférence", "tracks": "parcours envisagés"}


def _lang(conv: Conversation, text: str) -> str:
    lang = detect_language(text)
    # very short neutral messages keep the language already used in the conversation
    if lang == "fr" and conv.language in ("tn", "arabizi") and len(tokens(text)) <= 2:
        lang = conv.language
    conv.language = lang
    return lang


def _ask(lang: str, profile: dict) -> tuple[str, str | None]:
    slot = prof.next_missing(profile)
    if slot:
        profile["asked"].append(slot)
        return tr(f"q_{slot}", lang), slot
    return "", None


def _programs(db: Session, ids: list[int]) -> list[Program]:
    return [p for p in (db.get(Program, i) for i in ids) if p]


def _named(db: Session, text: str, narrow: bool = True) -> list[Program]:
    """Formations mentioned in a message. With `narrow`, a clearly more specific match wins ("licence en informatique"
    is not every licence-level formation): at least 2 significant name words and strictly more than the next one."""
    named = rag.find_programs_named(db, text)
    if not narrow or len(named) < 2:
        return named
    words = {t for t in tokens(text) if len(t) > 2 and t not in rag.STOP}
    scored = sorted(((len(words & {t for t in tokens(p.name) if len(t) > 2}), i) for i, p in enumerate(named)), reverse=True)
    return [named[scored[0][1]]] if scored[0][0] >= 2 and scored[0][0] > scored[1][0] else named


def _resume(db: Session, user: User, text: str, intents: list[str], mem: dict) -> str | None:
    """A short bare answer ("la licence en informatique", "c'est fait") continues the request the agent interrupted."""
    pending = mem.get("pending") or {}
    intent = pending.get("intent")
    if intent not in RESUMABLE or intents or len(tokens(text)) > MAX_FOLLOWUP_TOKENS:
        return None
    if rag.find_programs_named(db, text):
        return intent
    if pending.get("program") and user is not None and user.profile and user.profile.consent_given:  # consent was the missing piece
        return intent
    return None


def _resolve_program(db: Session, text: str, profile: dict, mem: dict) -> Program | None:
    named = _named(db, text)
    if len(named) == 1:
        return named[0]
    if named:
        return None
    recent = _programs(db, mem["last_programs"])
    if len(recent) == 1:  # "this one" = the only formation just discussed
        return recent[0]
    chosen = profile.get("chosen_program")
    return db.get(Program, chosen) if chosen else None


def _info_programs(db: Session, text: str, profile: dict, mem: dict) -> list[Program]:
    """Formations an information question is about: named in the message, else just discussed, else the shortlist, else RAG."""
    progs = _named(db, text)[:2]
    if not progs:
        progs = _programs(db, mem["last_programs"])[:2]  # follow-up: "et les frais ?"
    if not progs and profile["shortlist"]:
        progs = _programs(db, profile["shortlist"][:2])
    if not progs:
        hits = rag.retrieve(db, text, limit=2)
        progs = _programs(db, [h["program_id"] for h in hits if h["program_id"]])
    return [p for p in progs if p.active][:2]


def _amount(value: float) -> str:
    s = f"{value:,.2f}".replace(",", " ")
    return s[:-3] if s.endswith(".00") else s


def _until(lang: str, d) -> str:
    return tr("valid_until", lang, date=d.strftime("%d/%m/%Y")) if d else ""


def _scope(item) -> str:
    return f" [{item.specialty.name}]" if item.specialty is not None else ""


def _condition_line(lang: str, c) -> str:
    desc = c.description.strip()
    return tr(
        "cond_line", lang, title=c.title + _scope(c),
        optional="" if c.required else tr("cond_optional", lang),
        threshold=tr("cond_threshold", lang, t=f"{c.threshold:g}") if c.threshold is not None else "",
        desc=f" : {desc[:200]}" if desc else "",
    ) + _until(lang, c.valid_until)


def _payment_line(lang: str, t) -> str:
    details = tr("pay_installments", lang, n=t.installments) if t.installments > 1 else ""
    if t.down_payment_percent is not None:
        details += tr("pay_down", lang, p=f"{t.down_payment_percent:g}")
    if t.due_date:
        details += tr("pay_due", lang, date=t.due_date.strftime("%d/%m/%Y"))
    if t.description.strip():
        details += f" — {t.description.strip()[:200]}"
    return tr("pay_line", lang, title=t.title + _scope(t), method=label(METHOD, t.method.value, lang), details=details + _until(lang, t.valid_until))


def _section(db: Session, lang: str, kind: str, p: Program, today) -> tuple[str, bool]:
    """One block of the answer about one formation. Returns (text, found).

    Fees, payment terms and admission conditions come ONLY from official items (published, active, valid on `today`): a
    draft, an archived or an expired tariff is never quoted. When nothing official exists the agent says so instead of
    guessing. (Admission conditions fall back to the formation's own summary text, which the academic heads maintain.)"""
    name, inst = p.name, p.institution.value
    if kind in ("frais", "paiement", "conditions"):
        info = official_info(db, p, on=today)
        if kind == "frais":
            rows = info["fees"]
            if not rows:
                return tr("fees_none", lang, name=name, inst=inst), False
            lines = [tr("fee_line", lang, label=f.label + _scope(f), amount=_amount(f.amount), currency=f.currency,
                        period=label(PERIOD, f.period.value, lang), valid=_until(lang, f.valid_until)) for f in rows]
            return tr("info_fees", lang, name=name, inst=inst, text="\n" + "\n".join(lines)), True
        if kind == "paiement":
            rows = info["payment_terms"]
            if not rows:
                return tr("payment_none", lang, name=name, inst=inst), False
            return tr("info_payment", lang, name=name, inst=inst, text="\n" + "\n".join(_payment_line(lang, t) for t in rows)), True
        if info["admission_conditions"]:
            return tr("info_conditions", lang, name=name, inst=inst, text="\n" + "\n".join(_condition_line(lang, c) for c in info["admission_conditions"])), True
    passages = rag.program_passages(p)
    field = {"conditions": "admission_requirements", "debouches": "careers", "duree": "duration"}[kind]
    return tr({"conditions": "info_conditions", "debouches": "info_debouches", "duree": "info_duree"}[kind], lang, name=name, inst=inst, text=passages[field]), True


def _answer_info(db: Session, lang: str, text: str, kinds: list[str], profile: dict, mem: dict, today) -> tuple[str, list[str], list[int], dict]:
    progs = _info_programs(db, text, profile, mem)
    if not progs:
        return "", [], [], {}
    blocks, complete, found_any = [], {}, False
    for kind in kinds:
        results = [_section(db, lang, kind, p, today) for p in progs]
        blocks.append("\n".join(t for t, _ in results))
        complete[kind] = all(ok for _, ok in results)
        found_any = found_any or any(ok for _, ok in results)
    reply = "\n\n".join(blocks)
    if found_any and {"frais", "paiement"} & set(kinds):
        reply += "\n\n" + tr("official_note", lang)
    return reply, [rag.source_label(p) for p in progs], [p.id for p in progs], {"as_of": today.isoformat(), "kinds": kinds, "complete": complete, "found": found_any}


def run_agent(db: Session, conv: Conversation, user: User | None, text: str) -> dict:
    state = dict(conv.state or {})
    profile = state.get("profile") or prof.empty()
    for k, v in prof.empty().items():
        profile.setdefault(k, v)
    lang = _lang(conv, text)
    if user is None:  # visitor without account: the working memory travels with the client, nothing is stored here
        raw = dict(state.get("memory") or {})
        if sm.guest_expired(raw):  # idle too long, too old or tampered: start again from nothing (slots included)
            raw, profile = {}, prof.empty()
        fresh = not raw  # before bound(), which fills the missing keys in place
        row, mem = None, sm.bound(raw)
    else:
        row, mem, fresh = sm.load(db, conv)  # temporary working memory: recent turns, last formations, pending question
    intents = intents_in(text)
    resumed = _resume(db, user, text, intents, mem)
    if resumed:
        intents = [resumed]
    changed = prof.extract(profile, text)
    sm.record_turn(mem, "user", text)
    trace = [f"language={lang}", f"intents={intents}", f"profile_update={sorted(changed)}",
             f"memory={'new' if fresh else 'reused'}" + (f", resumed={resumed}" if resumed else "")]
    meta: dict = {"agent": "supervisor", "language": lang, "intents": intents}
    reply, sources, replies, action = "", [], [], "fallback"
    focus: list[int] = []  # formations this answer is about -> what "it / this one" means next turn
    pending: dict | None = None  # question asked back to the candidate, to resume once answered

    if set(tokens(text)) & DECISION_TOKENS or "human" in intents:
        reply, action = tr("handoff", lang), "human_handoff"
        meta["handoff"] = True
    elif "preinscription" in intents and user is None:  # a pre-registration belongs to an account
        reply, action = GUEST_SIGNUP.get(lang, GUEST_SIGNUP["fr"]), "need_account"
    elif "preinscription" in intents:
        prog = _resolve_program(db, text, profile, mem)
        if prog is None:
            reply, action = tr("preinsc_which", lang), "ask_program"
            pending = {"intent": "preinscription"}
        else:
            profile["chosen_program"] = prog.id
            focus = [prog.id]
            existing = db.scalar(select(PreRegistration).where(PreRegistration.user_id == user.id, PreRegistration.program_id == prog.id))
            if existing:
                reply, action = tr("preinsc_exists", lang, name=prog.name), "preinscription_exists"
            elif not (user.profile and user.profile.consent_given):
                reply, action = tr("preinsc_consent", lang), "need_consent"
                pending = {"intent": "preinscription", "program": prog.id}
            else:
                pre = PreRegistration(user_id=user.id, program_id=prog.id, summary=f"Créée par l’assistant ({lang}).")
                db.add(pre)
                db.flush()
                meta["preinscription_id"] = pre.id
                reply, action = tr("preinsc_created", lang, name=prog.name, inst=prog.institution.value), "preinscription_created"
            sources = [rag.source_label(prog)]
    elif "rdv" in intents:
        reply, action = tr("rdv", lang), "explain_rdv"
    elif "qcm" in intents:
        reply, action = tr("qcm", lang), "explain_qcm"
    elif "compare" in intents:
        progs = rag.find_programs_named(db, text)
        if len(progs) < 2:  # "et la prépa ?" = compare with the formation just discussed, then with the shortlist
            progs += [p for p in _programs(db, mem["last_programs"]) if p not in progs]
        if len(progs) < 2 and profile["shortlist"]:
            progs = _programs(db, profile["shortlist"])
        progs = progs[:3]
        if len(progs) < 2:
            reply, action = tr("compare_need", lang), "ask_compare"
            pending = {"intent": "compare"}
        else:
            rows = orientation.compare(progs)
            reply = tr("compare_intro", lang) + "".join(
                tr("compare_line", lang, name=r["name"], inst=r["institution"], duration=r["duration"], careers=r["careers"], requirements=r["requirements"]) for r in rows
            )
            sources, action, focus = [r["source"] for r in rows], "compare", [p.id for p in progs]
    elif {"conditions", "frais", "paiement", "debouches", "duree"} & set(intents):
        kinds = [k for k in ("conditions", "frais", "paiement", "debouches", "duree") if k in intents][:3]
        reply, sources, focus, official = _answer_info(db, lang, text, kinds, profile, mem, tn_today())
        action = "rag_" + "_".join(kinds)
        meta["official"] = official  # which day the validity periods were checked, and which topics have official data
        if not reply:
            reply, action, meta["handoff"] = tr("no_source", lang), "no_source_handoff", True
        elif not official["found"]:  # the formation is known but nothing official is published on this topic
            reply += "\n" + tr("no_source", lang)
            action, meta["handoff"] = "no_source_handoff", True
    elif ("greeting" in intents or "thanks" in intents) and not changed:
        action = "greeting" if "greeting" in intents else "thanks"
        reply = tr(action, lang)
        replies = QUICK["greeting"][lang] if action == "greeting" else []
    else:
        question, slot = _ask(lang, profile)
        if prof.completeness(profile) >= 3 or (not question and orientation.profile_concepts(profile)):
            top = orientation.shortlist(db, profile)
            if top:
                profile["shortlist"] = [r["program_id"] for r in top]
                reply = tr("short_intro", lang, n=len(top)) + "".join(
                    tr("short_line", lang, name=r["name"], inst=r["institution"], score=r["score"], matched=", ".join(r["matched"])) for r in top
                ) + tr("short_outro", lang)
                sources, action, replies = [r["source"] for r in top], "shortlist", QUICK["shortlist"][lang]
                focus = [r["program_id"] for r in top]
                meta["shortlist"] = top
        if not reply and (changed or question):
            noted = ", ".join(NOTED[k] for k in changed if k in NOTED)
            reply = (tr("ack_ask", lang, noted=noted) if noted else "") + question
            action = f"ask_{slot}" if slot else "ack"
            if slot:
                pending = {"slot": slot}
        if not reply.strip():
            reply = tr("fallback", lang)

    trace.append(f"action={action}")
    meta.update({"action": action, "sources": sources, "trace": trace, "profile_completeness": prof.completeness(profile)})
    if replies:
        meta["replies"] = replies
    state["profile"] = profile
    conv.state = state
    if user is not None:
        prof.sync_to_db(db, user, profile)

    # Keep only what is useful for the next message: the formations just discussed and the open question.
    if focus:
        mem["last_programs"] = focus[: sm.MAX_PROGRAMS]
    mem["last_intent"] = intents[0] if intents else mem.get("last_intent")
    mem["last_action"], mem["pending"] = action, pending
    # Optional existing Derja LLM (no fine-tuning): rephrases the sourced reply, falls back to it when unfaithful.
    names = [s.split(" · ", 1)[-1] for s in sources]
    reply, meta["llm"] = llm.polish(reply, lang, action=action, history=mem["turns"], names=names)
    sm.record_turn(mem, "assistant", reply, action)
    if row is None:  # visitor: the bounded, stamped memory goes back to the client with the state
        state["memory"] = sm.guest_stamp(sm.bound(mem))
        conv.state = state
    else:
        sm.save(row, mem)
    left = max(0, int((sm.aware(row.expires_at) - sm.now()).total_seconds())) if row is not None else sm.guest_left(state["memory"])
    meta["memory"] = {"new": fresh, "resumed": resumed, "expires_in_seconds": left}
    return {"content": reply, "meta": meta}


class GuestConversation:
    """In-memory stand-in for Conversation: a visitor has no account, so nothing is written to the database."""

    id = None
    user_id = None

    def __init__(self, state: dict | None = None):
        self.state = dict(state or {})
        lang = self.state.get("language")
        self.language = lang if lang in ("fr", "tn", "arabizi") else None


def run_guest(db: Session, text: str, state: dict | None) -> tuple[dict, dict]:
    """Answer a visitor with the same agent (catalogue, official info, orientation) minus everything that needs an account.
    Returns (reply, new_state): the profile slots, the working memory and the language go back to the client."""
    conv = GuestConversation(state)
    reply = run_agent(db, conv, None, text)
    new_state = dict(conv.state)
    new_state["language"] = conv.language
    return reply, new_state
