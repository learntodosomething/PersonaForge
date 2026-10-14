"""Speaker inspection and selection."""
from __future__ import annotations

from collections import Counter

from app.schemas.messages import Conversation, Message, MessageKind, SpeakerSummary


def list_speakers(conv: Conversation) -> list[SpeakerSummary]:
    total: Counter[str] = Counter()
    texts: Counter[str] = Counter()
    for m in conv.messages:
        if m.sender is None:
            continue
        total[m.sender] += 1
        if m.kind is MessageKind.TEXT:
            texts[m.sender] += 1
    names = list(dict.fromkeys([*conv.participants, *total]))
    summaries = [
        SpeakerSummary(name=n, message_count=total[n], text_message_count=texts[n]) for n in names
    ]
    return sorted(summaries, key=lambda s: s.text_message_count, reverse=True)


def speaker_text_messages(conv: Conversation, speaker: str) -> list[Message]:
    """Only the selected speaker's text messages: the sole input allowed for style profiling."""
    if speaker not in {s.name for s in list_speakers(conv)}:
        raise KeyError(f"Unknown speaker: {speaker!r}")
    return [m for m in conv.messages if m.sender == speaker and m.kind is MessageKind.TEXT]
