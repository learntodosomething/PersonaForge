"""Aggregate statistics for the import overview. Counts only, no message text."""
from __future__ import annotations

from collections import defaultdict

from app.schemas.messages import (
    Conversation,
    MessageKind,
    MonthActivity,
    Overview,
    SpeakerStats,
)
from app.services.speakers import list_speakers


def _percentile(sorted_values: list[int], q: float) -> int:
    if not sorted_values:
        return 0
    return sorted_values[min(len(sorted_values) - 1, int(q * len(sorted_values)))]


def _month_range(first: tuple[int, int], last: tuple[int, int]) -> list[tuple[int, int]]:
    out, (y, m) = [], first
    while (y, m) <= last:
        out.append((y, m))
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def build_overview(conv: Conversation) -> Overview:
    texts = [m for m in conv.messages if m.kind is MessageKind.TEXT and m.sender and m.text]
    if not texts:
        return Overview(speakers=[SpeakerStats(name=s.name, text_message_count=0, median_chars=0, p90_chars=0)
                                  for s in list_speakers(conv)])

    per_month: dict[tuple[int, int], dict[str, int]] = defaultdict(lambda: defaultdict(int))
    lengths: dict[str, list[int]] = defaultdict(list)
    for m in texts:
        per_month[(m.timestamp.year, m.timestamp.month)][m.sender] += 1  # type: ignore[index]
        lengths[m.sender].append(len(m.text))  # type: ignore[arg-type]

    keys = sorted(per_month)
    names = [s.name for s in list_speakers(conv)]
    months = [
        MonthActivity(month=f"{y:04d}-{mo:02d}", counts={n: per_month[(y, mo)].get(n, 0) for n in names})
        for y, mo in _month_range(keys[0], keys[-1])
    ]
    stats = []
    for n in names:
        vals = sorted(lengths[n])
        stats.append(SpeakerStats(name=n, text_message_count=len(vals),
                                  median_chars=_percentile(vals, 0.5), p90_chars=_percentile(vals, 0.9)))
    first, last = texts[0].timestamp, texts[-1].timestamp
    return Overview(first_message=first, last_message=last, span_days=(last - first).days,
                    active_months=len(keys), months=months, speakers=stats)
