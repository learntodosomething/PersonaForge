import { useEffect, useState, type DragEvent } from "react";
import ProfileView from "./ProfileView";
import { deleteImport, fetchOverview, uploadExport, type ImportResult, type Overview } from "./api";

const nf = new Intl.NumberFormat("hu-HU");
const steps = ["Feltöltés", "Ellenőrzés", "Beszélő"];
const day = (iso: string | null) => (iso ? new Date(iso).toLocaleDateString("hu-HU") : "–");
const span = (days: number) => (days >= 365 ? `${(days / 365).toFixed(1).replace(".", ",")} év` : `${days} nap`);

export default function App() {
  const [files, setFiles] = useState<File[]>([]);
  const [confirmed, setConfirmed] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ImportResult | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [over, setOver] = useState(false);
  const [showProfile, setShowProfile] = useState(false);
  const [overview, setOverview] = useState<Overview | null>(null);

  useEffect(() => {
    if (!result) { setOverview(null); return; }
    fetchOverview(result.import_id).then(setOverview).catch((e: Error) => setError(e.message));
  }, [result]);

  const step = !result ? 0 : selected ? 2 : 1;
  const addFiles = (list: FileList | null) =>
    list && setFiles(Array.from(list).filter((f) => f.name.endsWith(".json")));
  const onDrop = (e: DragEvent) => { e.preventDefault(); setOver(false); addFiles(e.dataTransfer.files); };

  async function submit() {
    setBusy(true); setError(null);
    try { setResult(await uploadExport(files, confirmed)); }
    catch (e) { setError((e as Error).message); }
    finally { setBusy(false); }
  }
  async function remove() {
    if (!result) return;
    try { await deleteImport(result.import_id); } catch (e) { setError((e as Error).message); return; }
    setResult(null); setSelected(null); setShowProfile(false); setFiles([]); setConfirmed(false);
  }

  const totalText = result?.speakers.reduce((n, s) => n + s.text_message_count, 0) ?? 0;
  const size = files.reduce((n, f) => n + f.size, 0);

  return (
    <main>
      <header>
        <h1>PersonaForge</h1>
        <p>Messenger-export betöltése és ellenőrzése. Minden adat a gépeden marad, a szerver csak memóriában tartja.</p>
        <ol className="steps" aria-label="Lépések">
          {steps.map((s, i) => (
            <li key={s} className={i === step ? "on" : i < step ? "done" : ""} aria-current={i === step ? "step" : undefined}>
              <span>{i + 1}</span>{s}
            </li>
          ))}
        </ol>
      </header>

      {error && <p className="error" role="alert">{error}</p>}

      {!result && (
        <section>
          <label className={`drop ${over ? "over" : ""}`}
            onDragOver={(e) => { e.preventDefault(); setOver(true); }}
            onDragLeave={() => setOver(false)} onDrop={onDrop}>
            <input type="file" accept=".json,application/json" multiple onChange={(e) => addFiles(e.target.files)} />
            {files.length === 0
              ? <>Húzd ide a <b>message_*.json</b> fájlokat, vagy kattints a választáshoz</>
              : <><b>{files.length} fájl</b> kiválasztva ({(size / 1048576).toFixed(1)} MB). Kattints a cseréhez.</>}
          </label>
          <label className="check">
            <input type="checkbox" checked={confirmed} onChange={(e) => setConfirmed(e.target.checked)} />
            Megerősítem, hogy jogosult vagyok feldolgozni ezeket a beszélgetéseket, és a többi résztvevő magánszférájára is tekintettel vagyok.
          </label>
          <button className="primary" disabled={!files.length || !confirmed || busy} onClick={submit}>
            {busy ? "Feldolgozás…" : "Import indítása"}
          </button>
        </section>
      )}

      {result && (
        <>
          <section>
            <h2>{result.title ?? "Beszélgetés"}</h2>
            <dl className="report">
              <div><dt>Beolvasott fájl</dt><dd>{result.report.files_read}</dd></div>
              <div><dt>Üzenet összesen</dt><dd>{nf.format(result.report.messages_total)}</dd></div>
              <div><dt>Megtartott</dt><dd>{nf.format(result.report.messages_kept)}</dd></div>
              <div><dt>Eldobott (üres vagy visszavont)</dt><dd>{nf.format(result.report.skipped_empty)}</dd></div>
              <div><dt>Hibás időbélyeg</dt><dd>{result.report.skipped_invalid_timestamp}</dd></div>
              <div><dt>Hiányzó feladó</dt><dd>{result.report.missing_sender}</dd></div>
              <div><dt>Ékezetek javítva</dt><dd>{result.report.encoding_repaired ? "igen" : "nem"}</dd></div>
            </dl>
            {result.report.warnings.map((w) => <p key={w} className="warn">{w}</p>)}
          </section>

          {overview && overview.months.length > 0 && <Timeline ov={overview} names={result.speakers.map((s) => s.name)} />}

          <section>
            <h2>Kit modellezzünk?</h2>
            <p className="hint">A sáv a szöveges üzenetek arányát mutatja. Csak a kiválasztott beszélő üzenetei kerülnek majd a stílusprofilba.</p>
            <div className="split" aria-hidden="true">
              {result.speakers.map((s, i) => (
                <i key={s.name} className={`c${i % 4} ${selected === s.name ? "sel" : ""}`}
                  style={{ flexGrow: s.text_message_count || 0.01 }} />
              ))}
            </div>
            <div role="radiogroup" aria-label="Beszélő" className="speakers">
              {result.speakers.map((s, i) => (
                <button key={s.name} role="radio" aria-checked={selected === s.name}
                  className={`speaker ${selected === s.name ? "sel" : ""}`} onClick={() => { setSelected(s.name); setShowProfile(false); }}>
                  <span className={`dot c${i % 4}`} />
                  <span className="name">{s.name}
                    {overview && <small>medián {overview.speakers.find((o) => o.name === s.name)?.median_chars ?? 0} karakter / üzenet</small>}
                  </span>
                  <span className="num">{nf.format(s.text_message_count)} szöveges<small> / {nf.format(s.message_count)} összes</small></span>
                  <span className="pct">{totalText ? Math.round((s.text_message_count / totalText) * 100) : 0}%</span>
                </button>
              ))}
            </div>
            <div className="actions">
              <button className="primary" disabled={!selected} onClick={() => setShowProfile(true)}>Stílusprofil készítése</button>
              <button className="danger" onClick={remove}>Import törlése</button>
            </div>
          </section>
          {showProfile && selected && <ProfileView key={selected} importId={result.import_id} speaker={selected} />}
        </>
      )}
    </main>
  );
}

function Timeline({ ov, names }: { ov: Overview; names: string[] }) {
  const max = Math.max(...ov.months.map((m) => Object.values(m.counts).reduce((a, b) => a + b, 0)), 1);
  const busiest = ov.months.reduce((a, b) => {
    const t = (m: typeof a) => Object.values(m.counts).reduce((x, y) => x + y, 0);
    return t(b) > t(a) ? b : a;
  });
  return (
    <section>
      <h2>Idővonal</h2>
      <p className="hint">
        {day(ov.first_message)} – {day(ov.last_message)} ({span(ov.span_days)}, ebből {ov.active_months} hónapban volt üzenet).
        A legaktívabb hónap: {busiest.month}.
      </p>
      <div className="timeline" role="img" aria-label={`Havi szöveges üzenetek ${ov.months[0].month} és ${ov.months[ov.months.length - 1].month} között`}>
        {ov.months.map((m) => (
          <div key={m.month} className="col"
            title={`${m.month}: ${names.map((n) => `${n} ${m.counts[n] ?? 0}`).join(", ")}`}>
            {names.map((n, i) => <i key={n} className={`c${i % 4}`} style={{ height: `${((m.counts[n] ?? 0) / max) * 100}%` }} />)}
          </div>
        ))}
      </div>
      <div className="axis"><span>{ov.months[0].month}</span><span>{ov.months[ov.months.length - 1].month}</span></div>
    </section>
  );
}
