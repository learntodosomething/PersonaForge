"""Rule-based style profiling.

Privacy rule: message *content* comes only from the selected speaker. Other participants'
messages are used solely as turn boundaries (who spoke when), never analysed.
"""
from __future__ import annotations

import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from statistics import median

from app.schemas.messages import Conversation, MessageKind
from app.schemas.profile import Counted, Profile, ProfileUpdate, StyleMetrics, Trait
from app.services.speakers import speaker_text_messages

EMOJI_CHARS = ("\U0001F300-\U0001FAFF\U0001F000-\U0001F2FF\u2600-\u27BF\u2B50\u2B55\u203C\u2049"
               "\u2B05-\u2B07\u2934\u2935\u3030\u303D\u3297\u3299")
EMOJI_RE = re.compile(f"[{EMOJI_CHARS}]\ufe0f?")
REPEAT_EMOJI_RE = re.compile(f"([{EMOJI_CHARS}])\\1{{2,}}")
INVISIBLE_RE = re.compile("[\ufe0f\u200d\U0001F3FB-\U0001F3FF]")
WORD_RE = re.compile(r"[^\W\d_]+(?:['’-][^\W\d_]+)*")
STRETCH_RE = re.compile(r"([^\W\d_])\1{2,}")
AFFECTION = set("❤🥰😍😘💕💖💗💓😻")
STOPWORDS = set("""a az egy és is de hogy nem én te ő mi ti ők ez azt ezt meg már még csak van volt ha mint na ne vagy
el fel le be ki rá át ide oda itt ott akkor mert majd persze nekem neked neki szerint úgy így olyan nagyon""".split())
MIN_MESSAGES_WARNING = 200


def _pct(sorted_values: list[int], q: float) -> int:
    return sorted_values[min(len(sorted_values) - 1, int(q * len(sorted_values)))] if sorted_values else 0


def _share(count: int, total: int) -> float:
    return round(count / total, 3) if total else 0.0


def _turn_sizes(conv: Conversation, speaker: str, gap: timedelta) -> list[int]:
    """Sizes of the speaker's turns. Other speakers' messages only mark boundaries."""
    sizes: list[int] = []
    cur, last_ts, cur_sender = 0, None, None
    for m in conv.messages:
        if m.sender is None:
            continue
        if m.sender != cur_sender or (last_ts is not None and m.timestamp - last_ts > gap):
            if cur_sender == speaker and cur > 0:
                sizes.append(cur)
            cur_sender, cur = m.sender, 0
        if m.sender == speaker and m.kind is MessageKind.TEXT:
            cur += 1
        last_ts = m.timestamp
    if cur_sender == speaker and cur > 0:
        sizes.append(cur)
    return sizes


def _top(counter: Counter[str], n: int, min_count: int) -> list[Counted]:
    return [Counted(text=t, count=c) for t, c in counter.most_common(n) if c >= min_count]


def compute_metrics(conv: Conversation, speaker: str, gap: timedelta) -> StyleMetrics:
    texts = [m.text for m in speaker_text_messages(conv, speaker) if m.text]
    if not texts:
        raise ValueError("The selected speaker has no text messages")
    n = len(texts)

    chars, words_per_msg = sorted(len(t) for t in texts), []
    emoji_msgs = emoji_total = emoji_end = repeated = stretched = 0
    q = ex = ell = term = low = low_den = caps = 0
    emojis: Counter[str] = Counter()
    words: Counter[str] = Counter()
    bigrams: Counter[str] = Counter()
    repeats: Counter[str] = Counter()

    for t in texts:
        found = EMOJI_RE.findall(t)
        clean = INVISIBLE_RE.sub("", t)
        if found:
            emoji_msgs += 1
            emoji_total += len(found)
            emojis.update(found)
            emoji_end += bool(EMOJI_RE.fullmatch(t.rstrip()[-2:]) or EMOJI_RE.fullmatch(t.rstrip()[-1:]))
        repeated += bool(REPEAT_EMOJI_RE.search(clean))

        raw_tokens = WORD_RE.findall(t)
        words_per_msg.append(len(raw_tokens))
        stretched += any(STRETCH_RE.search(w.lower()) for w in raw_tokens)
        caps += any(len(w) >= 3 and w.isupper() for w in raw_tokens)
        toks = [re.sub(r"(.)\1{2,}", r"\1", w.lower()) for w in raw_tokens]
        words.update(w for w in toks if len(w) >= 2 and w not in STOPWORDS)
        bigrams.update(f"{a} {b}" for a, b in zip(toks, toks[1:])
                       if not (a in STOPWORDS and b in STOPWORDS) and len(a) > 1 and len(b) > 1)

        q += "?" in t
        ex += "!" in t
        ell += "…" in t or "..." in t
        term += t.rstrip()[-1] in ".!?…"
        first = next((c for c in t if c.isalpha()), None)
        if first:
            low_den += 1
            low += first.islower()
        repeats[" ".join(t.lower().split())] += 1

    sizes = sorted(_turn_sizes(conv, speaker, gap)) or [1]
    return StyleMetrics(
        message_count=n, chars_median=int(median(chars)), chars_p90=_pct(chars, 0.9),
        words_median=int(median(words_per_msg)), short_share=_share(sum(c <= 20 for c in chars), n),
        turns=len(sizes), messages_per_turn_mean=round(sum(sizes) / len(sizes), 2),
        messages_per_turn_p90=_pct(sizes, 0.9),
        emoji_message_share=_share(emoji_msgs, n), emoji_per_message=round(emoji_total / n, 2),
        emoji_end_share=_share(emoji_end, n), repeated_emoji_share=_share(repeated, n),
        top_emojis=_top(emojis, 8, 2), stretched_message_share=_share(stretched, n),
        question_share=_share(q, n), exclamation_share=_share(ex, n), ellipsis_share=_share(ell, n),
        terminal_punct_share=_share(term, n), lowercase_start_share=_share(low, low_den),
        allcaps_share=_share(caps, n),
        top_words=_top(words, 20, 3), top_bigrams=_top(bigrams, 15, 5),
        repeated_messages=_top(Counter({k: v for k, v in repeats.items() if len(k) >= 3}), 10, 5),
    )


def _p(x: float) -> str:
    return f"{round(x * 100)}%"


def build_traits(m: StyleMetrics) -> list[Trait]:
    basis = f"{m.message_count} üzenet alapján"
    out: list[Trait] = []

    def add(id_: str, text: str, kind: str, evidence: str = basis) -> None:
        out.append(Trait(id=id_, text=text, kind=kind, evidence=evidence))  # type: ignore[arg-type]

    if m.chars_median <= 40:
        add("length", f"Rövid üzeneteket ír: a medián {m.chars_median} karakter, az üzenetek {_p(m.short_share)}-a legfeljebb 20 karakteres.", "observed")
    elif m.chars_median >= 100:
        add("length", f"Hosszabb, kifejtős üzeneteket ír (medián {m.chars_median} karakter).", "observed")
    else:
        add("length", f"Közepes hosszúságú üzeneteket ír (medián {m.chars_median} karakter).", "observed")
    if m.messages_per_turn_mean >= 1.5:
        add("rhythm", f"Gyakran több üzenetre bontja a mondandóját (átlag {m.messages_per_turn_mean:.1f} üzenet megszólalásonként).", "observed")
    if m.emoji_message_share >= 0.25:
        top = " ".join(e.text for e in m.top_emojis[:3])
        add("emoji", f"Gyakran használ emojit: az üzenetek {_p(m.emoji_message_share)}-ában" + (f", leggyakoribb: {top}." if top else "."), "observed")
    if m.repeated_emoji_share >= 0.1:
        add("emoji-repeat", f"Gyakran ismétel egy emojit egymás után (az üzenetek {_p(m.repeated_emoji_share)}-ában).", "observed")
    if m.stretched_message_share >= 0.05:
        add("stretch", f"Gyakran nyújt meg szavakat ismételt betűkkel (az üzenetek {_p(m.stretched_message_share)}-ában).", "observed")
    if m.lowercase_start_share >= 0.5:
        add("lowercase", f"Az üzeneteket többnyire kisbetűvel kezdi ({_p(m.lowercase_start_share)}).", "observed")
    if m.terminal_punct_share <= 0.3:
        add("no-terminal", f"Az üzenetek ritkán végződnek írásjellel ({_p(m.terminal_punct_share)}).", "observed")
    if m.question_share >= 0.15:
        add("questions", f"Sok kérdést tesz fel (az üzenetek {_p(m.question_share)}-ában van kérdőjel).", "observed")
    if m.repeated_messages:
        add("recurring", "Visszatérő, szó szerint ismétlődő üzenetei: " + ", ".join(r.text for r in m.repeated_messages[:5]) + ".", "observed")
    if m.emoji_message_share >= 0.25 and any(e.text[0] in AFFECTION for e in m.top_emojis[:3]):
        add("tone", "Hangneme valószínűleg meleg és érzelmes.", "inferred", "a leggyakoribb emojik között szív vagy hasonló szerepel; ez csak becslés")
    if m.lowercase_start_share >= 0.5 and m.chars_median <= 40 and m.terminal_punct_share <= 0.5:
        add("informal", "Stílusa valószínűleg informális, a beszélt nyelvhez közeli.", "inferred", "rövid, kisbetűs kezdésű, írásjel nélküli üzenetek; ez csak becslés")
    return out


def build_profile(conv: Conversation, speaker: str, turn_gap: timedelta = timedelta(minutes=10)) -> Profile:
    metrics = compute_metrics(conv, speaker, turn_gap)
    warnings = []
    if metrics.message_count < MIN_MESSAGES_WARNING:
        warnings.append(f"Kevés üzenet ({metrics.message_count}): a profil megbízhatatlan lehet.")
    return Profile(speaker=speaker, generated_at=datetime.now(timezone.utc),
                   based_on_messages=metrics.message_count, metrics=metrics,
                   traits=build_traits(metrics), warnings=warnings)


def apply_update(profile: Profile, update: ProfileUpdate) -> Profile:
    """Merge user edits. Metrics stay server-computed; an edited observed/inferred line becomes 'user'."""
    old = {t.id: t for t in profile.traits}
    merged: list[Trait] = []
    for t in update.traits:
        prev = old.get(t.id)
        text = t.text.strip()
        if prev and prev.kind != "user":
            kind = prev.kind if text == prev.text else "user"
            evidence = prev.evidence
        else:
            kind, evidence = "user", (prev.evidence if prev else "")
        merged.append(Trait(id=t.id, text=text, kind=kind, evidence=evidence, enabled=t.enabled))
    return profile.model_copy(update={"traits": merged, "notes": update.notes})
