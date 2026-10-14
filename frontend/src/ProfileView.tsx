import { useEffect, useState } from "react";
import { createProfile, saveProfile, type Counted, type Profile, type Trait } from "./api";

const pct = (x: number) => `${Math.round(x * 100)}%`;
const kindLabel = { observed: "megfigyelt", inferred: "következtetés", user: "saját" } as const;

function Chips({ title, items }: { title: string; items: Counted[] }) {
  if (!items.length) return null;
  return (
    <div className="chiprow">
      <h4>{title}</h4>
      <div className="chips">{items.map((c) => <span key={c.text} className="chip">{c.text} <b>{c.count}</b></span>)}</div>
    </div>
  );
}

export default function ProfileView({ importId, speaker }: { importId: string; speaker: string }) {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [traits, setTraits] = useState<Trait[]>([]);
  const [notes, setNotes] = useState("");
  const [state, setState] = useState<"loading" | "dirty" | "saving" | "saved">("loading");
  const [error, setError] = useState<string | null>(null);

  const apply = (p: Profile) => { setProfile(p); setTraits(p.traits); setNotes(p.notes); setState("saved"); };
  const generate = () => {
    setState("loading"); setError(null);
    createProfile(importId, speaker).then(apply).catch((e: Error) => setError(e.message));
  };
  useEffect(generate, [importId, speaker]); // eslint-disable-line react-hooks/exhaustive-deps

  const edit = (i: number, patch: Partial<Trait>) => {
    setTraits((ts) => ts.map((t, j) => (j === i ? { ...t, ...patch } : t)));
    setState("dirty");
  };
  const save = () => {
    setState("saving"); setError(null);
    saveProfile(importId, traits.filter((t) => t.text.trim()), notes).then(apply)
      .catch((e: Error) => { setError(e.message); setState("dirty"); });
  };

  if (error && !profile) return <section><p className="error" role="alert">{error}</p></section>;
  if (!profile) return <section><p className="hint">Profil készítése…</p></section>;
  const m = profile.metrics;
  const groups: [string, [string, string | number][]][] = [
    ["Hossz és ritmus", [["Medián hossz", `${m.chars_median} karakter`], ["90. percentilis", `${m.chars_p90} karakter`],
      ["Medián szószám", m.words_median], ["Rövid (legfeljebb 20 karakter)", pct(m.short_share)],
      ["Megszólalás", m.turns.toLocaleString("hu-HU")], ["Üzenet megszólalásonként", m.messages_per_turn_mean.toFixed(2)]]],
    ["Emoji", [["Emojis üzenetek", pct(m.emoji_message_share)], ["Emoji üzenetenként", m.emoji_per_message.toFixed(2)],
      ["Emojival végződő", pct(m.emoji_end_share)], ["Ismételt emoji", pct(m.repeated_emoji_share)]]],
    ["Írásmód", [["Kérdőjeles", pct(m.question_share)], ["Felkiáltójeles", pct(m.exclamation_share)],
      ["Három pontos", pct(m.ellipsis_share)], ["Írásjellel végződő", pct(m.terminal_punct_share)],
      ["Kisbetűvel kezdődő", pct(m.lowercase_start_share)], ["Nyújtott betűs", pct(m.stretched_message_share)],
      ["Csupa nagybetűs szót tartalmaz", pct(m.allcaps_share)]]],
  ];

  return (
    <section>
      <h2>Stílusprofil: {profile.speaker}</h2>
      <p className="hint">{m.message_count.toLocaleString("hu-HU")} szöveges üzenet alapján. A számok mérések, a "következtetés" sorok becslések.</p>
      {profile.warnings.map((w) => <p key={w} className="warn">{w}</p>)}
      {error && <p className="error" role="alert">{error}</p>}

      {groups.map(([title, rows]) => (
        <div key={title}>
          <h3>{title}</h3>
          <dl className="report">{rows.map(([k, v]) => <div key={k}><dt>{k}</dt><dd>{v}</dd></div>)}</dl>
        </div>
      ))}
      <h3>Szókincs</h3>
      <Chips title="Leggyakoribb emojik" items={m.top_emojis} />
      <Chips title="Leggyakoribb szavak" items={m.top_words} />
      <Chips title="Leggyakoribb szópárok" items={m.top_bigrams} />
      <Chips title="Szó szerint visszatérő üzenetek" items={m.repeated_messages} />

      <h3>Persona leírás</h3>
      <p className="hint">Ezt a leírást használja majd a chat. Írd át, kapcsold ki vagy törölje, amivel nem értesz egyet.</p>
      <ul className="traits">
        {traits.map((t, i) => (
          <li key={t.id} className={t.enabled ? "" : "off"}>
            <input type="checkbox" checked={t.enabled} aria-label="Használja a chat"
              onChange={(e) => edit(i, { enabled: e.target.checked })} />
            <div>
              <textarea rows={2} value={t.text} aria-label="Leírás" maxLength={500}
                onChange={(e) => edit(i, { text: e.target.value, kind: t.kind === "inferred" || t.kind === "observed" ? "user" : t.kind })} />
              <small><span className={`badge ${t.kind}`}>{kindLabel[t.kind]}</span> {t.evidence}</small>
            </div>
            <button className="link" onClick={() => { setTraits(traits.filter((_, j) => j !== i)); setState("dirty"); }}>Törlés</button>
          </li>
        ))}
      </ul>
      <button className="link" onClick={() => { setTraits([...traits, { id: `user-${Date.now()}`, text: "", kind: "user", evidence: "", enabled: true }]); setState("dirty"); }}>
        Új sor hozzáadása
      </button>

      <h3>Saját jegyzetek</h3>
      <textarea className="notes" rows={4} maxLength={4000} value={notes} placeholder="Bármi, amit a profil nem tud kiolvasni az üzenetekből."
        onChange={(e) => { setNotes(e.target.value); setState("dirty"); }} />
      <div className="actions">
        <button className="primary" onClick={save} disabled={state !== "dirty"}>
          {state === "saving" ? "Mentés…" : state === "saved" ? "Mentve" : "Változtatások mentése"}
        </button>
        <button className="danger" onClick={() => window.confirm("Az újragenerálás elveszi a szerkesztéseidet. Folytatod?") && generate()}>
          Újragenerálás
        </button>
      </div>
    </section>
  );
}
