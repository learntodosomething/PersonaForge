const BASE: string = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

export type Report = {
  files_read: number; messages_total: number; messages_kept: number;
  skipped_invalid_timestamp: number; skipped_empty: number; missing_sender: number;
  encoding_repaired: boolean; warnings: string[];
};
export type Speaker = { name: string; message_count: number; text_message_count: number };
export type ImportResult = { import_id: string; title: string | null; report: Report; speakers: Speaker[] };

async function request(path: string, init: RequestInit): Promise<Response> {
  let res: Response;
  try {
    res = await fetch(`${BASE}${path}`, init);
  } catch {
    throw new Error("A szerver nem érhető el. Indítsd el a backendet: uvicorn app.main:app --reload");
  }
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(typeof body?.detail === "string" ? body.detail : `Hiba (${res.status})`);
  }
  return res;
}

export async function uploadExport(files: File[], confirmAuthorized: boolean): Promise<ImportResult> {
  const body = new FormData();
  files.forEach((f) => body.append("files", f));
  body.append("confirm_authorized", String(confirmAuthorized));
  return (await request("/api/imports", { method: "POST", body })).json();
}

export async function deleteImport(id: string): Promise<void> {
  await request(`/api/imports/${id}`, { method: "DELETE" });
}

export type SpeakerStats = { name: string; text_message_count: number; median_chars: number; p90_chars: number };
export type Overview = {
  first_message: string | null; last_message: string | null; span_days: number; active_months: number;
  months: { month: string; counts: Record<string, number> }[];
  speakers: SpeakerStats[];
};

export async function fetchOverview(id: string): Promise<Overview> {
  return (await request(`/api/imports/${id}/overview`, {})).json();
}

export type Counted = { text: string; count: number };
export type Trait = { id: string; text: string; kind: "observed" | "inferred" | "user"; evidence: string; enabled: boolean };
export type Metrics = {
  message_count: number; chars_median: number; chars_p90: number; words_median: number; short_share: number;
  turns: number; messages_per_turn_mean: number; messages_per_turn_p90: number;
  emoji_message_share: number; emoji_per_message: number; emoji_end_share: number; repeated_emoji_share: number;
  top_emojis: Counted[]; stretched_message_share: number; question_share: number; exclamation_share: number;
  ellipsis_share: number; terminal_punct_share: number; lowercase_start_share: number; allcaps_share: number;
  top_words: Counted[]; top_bigrams: Counted[]; repeated_messages: Counted[];
};
export type Profile = {
  speaker: string; generated_at: string; based_on_messages: number; metrics: Metrics;
  traits: Trait[]; notes: string; warnings: string[];
};

const json = { "Content-Type": "application/json" };

export async function createProfile(id: string, speaker: string): Promise<Profile> {
  const body = JSON.stringify({ speaker });
  return (await request(`/api/imports/${id}/profile`, { method: "POST", headers: json, body })).json();
}

export async function saveProfile(id: string, traits: Trait[], notes: string): Promise<Profile> {
  const body = JSON.stringify({ traits, notes });
  return (await request(`/api/imports/${id}/profile`, { method: "PUT", headers: json, body })).json();
}
