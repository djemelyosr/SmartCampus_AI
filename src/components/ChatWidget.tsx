import { useEffect, useRef, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import conversationIcon from "../assets/conversation.svg";
import sparkles from "../assets/sparkles.svg";
import paperclip from "../assets/paperclip.svg";
import mic from "../assets/mic.svg";
import arrowUp from "../assets/arrow-up.svg";
import { api, ApiError } from "../lib/api";
import { useAuth } from "../lib/auth";
import { useI18n } from "../lib/i18n";

type Lang = "Français" | "Tounsi" | "Arabizi";
interface Turn {
  from: "me" | "bot";
  text: string;
  time: string;
  expl?: { title: string; bullets: string[] };
  sources?: string[];
  question?: string;
  replies?: string[];
}

const now = () => new Date().toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });

const WELCOME: Turn = {
  from: "bot",
  time: now(),
  text: "Bonjour ! Je suis votre guide SmartCampus. Parlez-moi de vos matières préférées, de vos envies et de vos hésitations : je vous aide à explorer les formations de l’IIT et de l’ISB.",
  replies: ["J’hésite entre Prépa et Licence", "Je veux comparer les formations"],
};

export default function ChatWidget() {
  const { user } = useAuth();
  const { t: tr } = useI18n();
  const [speakingIdx, setSpeakingIdx] = useState<number | null>(null);
  const speechOk = typeof window !== "undefined" && "speechSynthesis" in window;
  const [open, setOpen] = useState(false);
  const [lang, setLang] = useState<Lang>("Français");
  const [turns, setTurns] = useState<Turn[]>([WELCOME]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [recording, setRecording] = useState(false);
  const [convId, setConvId] = useState<number | null>(null);
  const endRef = useRef<HTMLDivElement>(null);
  const recRef = useRef<MediaRecorder | null>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const srRef = useRef<any>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [turns, open]);

  // Stop any reading when the chat is closed or the widget unmounts.
  useEffect(() => {
    if (!open && speechOk) { window.speechSynthesis.cancel(); setSpeakingIdx(null); }
  }, [open, speechOk]);
  useEffect(() => () => { if (speechOk) window.speechSynthesis.cancel(); }, [speechOk]);

  /** Read a bot reply aloud (browser text-to-speech). Click again to stop. */
  function listen(i: number, text: string) {
    if (!speechOk) return;
    const synth = window.speechSynthesis;
    if (speakingIdx === i) { synth.cancel(); setSpeakingIdx(null); return; }
    synth.cancel();
    const clean = text.replace(/[*#_`>]/g, " ").replace(/\s+/g, " ").trim();
    if (!clean) return;
    const u = new SpeechSynthesisUtterance(clean);
    const arabic = /[\u0600-\u06FF]/.test(clean);
    const hasTn = arabic && window.speechSynthesis.getVoices().some((v) => v.lang.toLowerCase() === "ar-tn");
    u.lang = arabic ? (hasTn ? "ar-TN" : "ar-SA") : "fr-FR";
    const voice = synth.getVoices().find((v) => v.lang.toLowerCase().startsWith(u.lang.slice(0, 2)));
    if (voice) u.voice = voice;
    const done = () => setSpeakingIdx((c) => (c === i ? null : c));
    u.onend = done;
    u.onerror = done;
    setSpeakingIdx(i);
    synth.speak(u);
  }

  async function send(content: string, modality = "text") {
    content = content.trim();
    if (!content || busy) return;
    setText("");
    setTurns((t) => [...t, { from: "me", text: content, time: now() }]);
    if (!user) {
      setTurns((t) => [...t, { from: "bot", time: now(), text: "Pour poursuivre et sauvegarder vos échanges, connectez-vous ou créez un compte candidat. Vous pouvez continuer à explorer le catalogue sans compte." }]);
      return;
    }
    setBusy(true);
    try {
      let id = convId;
      if (id === null) {
        id = (await api.startConversation()).id;
        setConvId(id);
      }
      const reply = await api.sendMessage(id, content, modality);
      const meta = (reply.meta ?? {}) as { sources?: unknown; replies?: unknown; handoff?: unknown };
      const strs = (v: unknown): string[] | undefined => (Array.isArray(v) && v.length ? v.filter((x): x is string => typeof x === "string") : undefined);
      const turn: Turn = { from: "bot", time: now(), text: reply.content, sources: strs(meta.sources), replies: strs(meta.replies) };
      if (meta.handoff) turn.expl = { title: "Un conseiller humain prend le relais", bullets: ["Votre demande est transmise à l’équipe habilitée.", "Aucune décision d’admission n’est prise par l’assistant."] };
      setTurns((t) => [...t, turn]);
      // After a voice message, answer aloud too (index of the bot turn = current length + 1).
      if (modality === "audio") listen(turns.length + 1, reply.content);
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Le serveur est injoignable.";
      setTurns((t) => [...t, { from: "bot", time: now(), text: `Erreur : ${msg}` }]);
    } finally {
      setBusy(false);
    }
  }

  async function toggleMic() {
    // Preferred path: in-browser speech recognition -> transcript is sent as an "audio" message.
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (SR) {
      if (recording) { srRef.current?.stop(); return; }
      const rec = new SR();
      rec.lang = lang === "Tounsi" ? "ar-TN" : "fr-FR"; // Arabizi is spoken, then transcribed as French/Latin
      rec.interimResults = false;
      rec.maxAlternatives = 1;
      let heard = "";
      rec.onresult = (e: { results: ArrayLike<ArrayLike<{ transcript: string }>> }) => {
        heard = Array.from(e.results).map((r) => r[0]?.transcript ?? "").join(" ").trim();
      };
      rec.onerror = () => {
        setRecording(false);
        setTurns((t) => [...t, { from: "bot", time: now(), text: "Je n’ai pas pu comprendre le message vocal. Vous pouvez réessayer ou écrire votre message." }]);
      };
      rec.onend = () => {
        setRecording(false);
        if (heard) void send(heard, "audio");
      };
      srRef.current = rec;
      setRecording(true);
      rec.start();
      return;
    }
    if (recording) { recRef.current?.stop(); return; }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const rec = new MediaRecorder(stream);
      rec.onstop = () => {
        stream.getTracks().forEach((t) => t.stop());
        setRecording(false);
        // Whisper transcription not wired yet on the backend.
        setTurns((t) => [...t, { from: "bot", time: now(), text: "Message vocal reçu. La transcription audio sera disponible prochainement." }]);
      };
      rec.start();
      recRef.current = rec;
      setRecording(true);
    } catch {
      setTurns((t) => [...t, { from: "bot", time: now(), text: "Le micro n’est pas accessible. Vous pouvez écrire votre message." }]);
    }
  }

  if (!open) {
    return (
      <div className="fab-wrap">
        <span className="fab-label">Une question ?</span>
        <button className="fab" aria-label="Ouvrir la conversation" onClick={() => setOpen(true)}>
          <img src={conversationIcon} alt="" />
        </button>
      </div>
    );
  }

  return (
    <>
      <button className="scrim" aria-label="Fermer la conversation" onClick={() => setOpen(false)} />
      <section className="cw" role="dialog" aria-label="Fenêtre de conversation SmartCampus">
        <div className="cw-head">
          <div>
            <b>Votre guide SmartCampus</b>
            <span>{user ? `Connecté · ${user.full_name || user.email}` : "Mode visiteur · Sans compte"}</span>
          </div>
          <button className="cw-x" aria-label="Fermer la conversation" onClick={() => setOpen(false)}>×</button>
        </div>
        <div className="cw-lang">
          <span>Parlez comme vous aimez</span>
          <div className="seg">
            {(["Français", "Tounsi", "Arabizi"] as Lang[]).map((l) => (
              <button key={l} className={l === lang ? "on" : ""} onClick={() => setLang(l)}>{l}</button>
            ))}
          </div>
        </div>
        <div className="cw-msgs">
          <div className="cw-time">AUJOURD’HUI · {turns[0].time}</div>
          {turns.map((t, i) =>
            t.from === "me" ? (
              <div className="cw-me" key={i}>
                <span>{t.text}</span>
                <small>Vous · {t.time}</small>
              </div>
            ) : (
              <div className="cw-bot" key={i}>
                <div className="who">
                  <img src={sparkles} alt="" />SmartCampus AI
                  {speechOk && (
                    <button
                      type="button"
                      className={`cw-listen ${speakingIdx === i ? "on" : ""}`}
                      aria-pressed={speakingIdx === i}
                      aria-label={speakingIdx === i ? tr("Arrêter la lecture") : tr("Écouter la réponse")}
                      title={speakingIdx === i ? tr("Arrêter la lecture") : tr("Écouter la réponse")}
                      onClick={() => listen(i, t.text)}
                    >
                      <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
                        {speakingIdx === i ? (
                          <rect x="6" y="6" width="12" height="12" rx="2" fill="currentColor" />
                        ) : (
                          <g fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M4 9.5v5h3.5L12 18.5v-13L7.5 9.5H4z" fill="currentColor" />
                            <path d="M15.5 9a4 4 0 010 6M18 6.5a7.5 7.5 0 010 11" />
                          </g>
                        )}
                      </svg>
                      <span>{speakingIdx === i ? tr("Arrêter") : tr("Écouter")}</span>
                    </button>
                  )}
                </div>
                <span style={{ whiteSpace: "pre-wrap" }}>{t.text}</span>
                {t.expl && (
                  <div className="expl">
                    <b>{t.expl.title}</b>
                    {t.expl.bullets.map((b) => <span key={b}>• {b}</span>)}
                  </div>
                )}
                {t.sources && <div className="rowg">{t.sources.map((s) => <span className="chip2" key={s}>{s}</span>)}</div>}
                {t.question && <b>{t.question}</b>}
                {t.replies && i === turns.length - 1 && (
                  <div className="reps">{t.replies.map((r) => <button key={r} onClick={() => send(r)}>{r}</button>)}</div>
                )}
              </div>
            ),
          )}
          {!user && (
            <span className="small">
              <Link to="/connexion" style={{ color: "var(--blue)" }} onClick={() => setOpen(false)}>Se connecter</Link>
              {" · "}
              <Link to="/inscription" style={{ color: "var(--blue)" }} onClick={() => setOpen(false)}>Créer un compte</Link>
            </span>
          )}
          <div ref={endRef} />
        </div>
        <form className="cw-comp" onSubmit={(e: FormEvent) => { e.preventDefault(); send(text); }}>
          <div className="cw-in">
            <button type="button" className="ico" aria-label="Joindre un fichier"><img src={paperclip} alt="" /></button>
            <input value={text} onChange={(e) => setText(e.target.value)} placeholder="Écrivez votre message…" aria-label="Message" />
            <button type="button" className={`ico ${recording ? "rec" : ""}`} aria-label="Message vocal" onClick={toggleMic}><img src={mic} alt="" /></button>
            <button className="send" aria-label="Envoyer" disabled={busy || !text.trim()}><img src={arrowUp} alt="" /></button>
          </div>
          <small>Texte ou audio · Micro à votre demande. Échange temporaire tant qu’il n’est pas sauvegardé dans un compte.</small>
        </form>
      </section>
    </>
  );
}
