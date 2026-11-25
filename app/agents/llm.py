"""Optional LLM layer: an EXISTING Tunisian-Derja model, used as-is (no fine-tuning), behind an OpenAI-compatible API.

Role (see orchestrator): the deterministic agent plans, calls the tools (catalogue / RAG) and writes a sourced reply.
The LLM only *rephrases* that reply in natural Derja (Arabic script) or Arabizi, using the recent turns of the session
memory for context. It never decides, never adds facts, and never touches official wording (handoff, consent...).

Safety net: the rewrite is accepted only if it keeps every number and every formation name of the original, is written
in the right script and stays short. Otherwise (disabled, timeout, error, unfaithful) the deterministic reply is used.
Chosen model (open weights, Tunisian Arabic + Arabizi): ESPRIT-Group/ESPRIT-Derja-Qwen3-8B-v2 (base Qwen3-8B).
Alternatives: ESPRIT-Group/ESPRIT-Derja-8B-v1, linagora/Labess-7b-chat-16bit.
Cloud (Hugging Face): the ESPRIT derja model is called through a Hugging Face Inference Endpoint (OpenAI-compatible):
LLM_BASE_URL = endpoint URL ending in /v1, LLM_API_KEY = Hugging Face token (hf_...), LLM_MODEL = ESPRIT-Group/ESPRIT-Derja-Qwen3-8B-v2.
Any other OpenAI-compatible server also works: only LLM_BASE_URL changes.
"""

import json
import logging
import re
import urllib.request

from app.agents.language import norm
from app.core.config import settings

log = logging.getLogger("smartcampus.llm")

# Official / legal wording stays exactly as written by the team.
SKIP_ACTIONS = {"human_handoff", "no_source_handoff", "need_consent", "preinscription_created"}
DIALECT = {
    "tn": "le dialecte tunisien (derja) écrit en lettres arabes",
    "arabizi": "le dialecte tunisien (derja) en Arabizi : lettres latines et chiffres (3=ع, 7=ح, 9=ق, 5=خ, 2=ء)",
}
SYSTEM = (
    "Tu es le guide SmartCampus qui oriente de futurs étudiants vers les formations de l’IIT et de l’ISB. "
    "On te donne un message déjà validé. Réécris-le en {dialect}, de façon naturelle et chaleureuse. Règles strictes : "
    "ne rien ajouter ni retirer ; garde tels quels les noms de formations, chiffres, pourcentages, durées et sigles ; "
    "n’invente aucune condition, frais, date ou débouché ; ne décide jamais d’une admission ; garde les puces et les "
    "retours à la ligne ; réponds uniquement avec le message réécrit, sans commentaire."
)
_THINK = re.compile(r"<think>.*?</think>", re.S)
_ARABIC = re.compile(r"[\u0600-\u06FF]")


def enabled_for(lang: str, action: str) -> bool:
    langs = {x.strip() for x in settings.llm_languages.split(",") if x.strip()}
    return settings.llm_enabled and lang in langs and action not in SKIP_ACTIONS


def _post(messages: list[dict]) -> str:
    """One chat completion on the OpenAI-compatible endpoint (standard library only)."""
    body = {"model": settings.llm_model, "messages": messages, "temperature": settings.llm_temperature,
            "max_tokens": settings.llm_max_tokens, "chat_template_kwargs": {"enable_thinking": False}}
    headers = {"Content-Type": "application/json", "User-Agent": "SmartCampus/1.0"}  # some tunnels / WAFs reject the default urllib UA
    if settings.llm_api_key:
        headers["Authorization"] = f"Bearer {settings.llm_api_key}"
    req = urllib.request.Request(settings.llm_base_url.rstrip("/") + "/chat/completions", json.dumps(body).encode(), headers)
    with urllib.request.urlopen(req, timeout=settings.llm_timeout_seconds) as resp:  # noqa: S310 (configured endpoint)
        return json.load(resp)["choices"][0]["message"]["content"]


def faithful(original: str, rewritten: str, lang: str, names: list[str]) -> str | None:
    """None when the rewrite is acceptable, otherwise the reason it is rejected."""
    if not rewritten.strip():
        return "empty"
    if len(rewritten) > 2.5 * len(original) + 200:
        return "too_long"
    out = norm(rewritten)
    if any(n not in rewritten for n in re.findall(r"\d+", original)):
        return "numbers_changed"
    if any(norm(n) not in out for n in names):
        return "formation_name_changed"
    letters = [c for c in rewritten if c.isalpha()]
    arabic = sum(1 for c in letters if _ARABIC.match(c)) / max(1, len(letters))
    if (lang == "tn" and arabic < 0.25) or (lang == "arabizi" and arabic > 0.1):
        return "wrong_script"
    return None


def polish(text: str, lang: str, *, action: str, history: list[dict], names: list[str]) -> tuple[str, dict]:
    """Return (final reply, info). `info` is exposed in meta["llm"] for traceability and evaluation."""
    if not settings.llm_enabled:
        return text, {"used": False}
    if not enabled_for(lang, action):
        return text, {"used": False, "skipped": "language_or_action"}
    context = "\n".join(f"{'Candidat' if t['r'] == 'user' else 'Guide'} : {t['t']}" for t in history[-4:])
    messages = [
        {"role": "system", "content": SYSTEM.format(dialect=DIALECT[lang])},
        {"role": "user", "content": f"Contexte récent (ne pas répéter) :\n{context}\n\nMessage à réécrire :\n{text}"},
    ]
    try:
        out = _THINK.sub("", _post(messages)).strip()
    except Exception as exc:  # timeout, connection refused, bad payload: the deterministic reply is always available
        log.warning("LLM unavailable (%s): deterministic reply used", exc)
        return text, {"used": False, "fallback": "unavailable", "model": settings.llm_model}
    reason = faithful(text, out, lang, names)
    if reason:
        log.info("LLM rewrite rejected: %s", reason)
        return text, {"used": False, "fallback": reason, "model": settings.llm_model}
    return out, {"used": True, "model": settings.llm_model}
