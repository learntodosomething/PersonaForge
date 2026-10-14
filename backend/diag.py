import sys, glob, json, re
from collections import Counter
from app.importers.messenger import parse_messenger

folder = sys.argv[1]
paths = sorted(glob.glob(f"{folder}/message_*.json"))
raws = [json.load(open(p, encoding="utf-8")) for p in paths]
result = parse_messenger(raws)
conv = result.conversation

# 1) Milyen rekordokat dobott el a parser? (csak mezőnevek, tartalom nélkül)
media = ("photos", "videos", "audio_files", "files", "gifs", "sticker")
skipped = Counter()
types = Counter()
for d in raws:
    for m in d["messages"]:
        if not isinstance(m, dict):
            continue
        types[m.get("type")] += 1
        if (not str(m.get("content") or "").strip() and not any(m.get(k) for k in media)
                and m.get("call_duration") is None
                and m.get("type") not in ("Call", "Subscribe", "Unsubscribe")):
            skipped[tuple(sorted(k for k in m if k not in ("sender_name", "timestamp_ms")))] += 1
print("Üzenettípusok:", dict(types))
print("Eldobott rekordok mezői:")
for keys, n in skipped.most_common(5):
    print(f"  {n:5d}  {keys}")

# 2) Gyakran ismétlődő hosszabb szövegek (név és számok kicserélve)
names = [re.escape(n) for n in conv.participants]
name_re = re.compile("|".join(names)) if names else None
norm = Counter()
for m in conv.messages:
    if m.text and len(m.text) >= 12:
        t = name_re.sub("<NÉV>", m.text) if name_re else m.text
        norm[re.sub(r"\d+", "#", t)] += 1
print("\nTöbbször ismétlődő, 12+ karakteres szövegek (rendszerüzenet-gyanús):")
for t, n in norm.most_common(15):
    if n >= 5:
        print(f"  {n:5d}  {t[:90]}")