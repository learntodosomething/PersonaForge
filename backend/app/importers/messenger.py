"""Facebook / Messenger JSON export parser.

Two export flavours are understood and can be mixed in one import:

* "Download your information" (facebook.com/dyi): ``sender_name`` / ``timestamp_ms`` /
  ``content``, newest message first, UTF-8-as-Latin-1 mojibake.
* Messenger "secure storage" download of end-to-end encrypted chats: ``senderName`` /
  ``timestamp`` / ``text`` / ``media``, ``participants`` as plain strings, proper UTF-8.

Messages that appear in more than one file (e.g. around the E2EE cut-over) are
de-duplicated.

Independent from the web framework so it can be tested without the API.

Known quirk: Meta exports encode UTF-8 bytes as Latin-1 escapes, so
"á" arrives as "Ã¡". We detect and repair this per string, falling back to
the original text when the repair is not valid UTF-8.
"""
from __future__ import annotations

import json
from collections.abc import Iterable
from datetime import datetime, timezone
from typing import Any

from app.schemas.messages import (
    Conversation,
    ImportReport,
    Message,
    MessageKind,
    ParseResult,
)

MAX_FILE_BYTES = 250 * 1024 * 1024  # per file; guards against accidental huge uploads
ATTACHMENT_KEYS = ("photos", "videos", "audio_files", "files", "gifs", "sticker")
SYSTEM_TYPES = {"call", "subscribe", "unsubscribe", "system"}  # compared lower-case


class MessengerImportError(ValueError):
    """Raised for input that cannot be parsed at all. Message never contains raw content."""


def repair_mojibake(value: str) -> tuple[str, bool]:
    """Return (text, repaired). Safe on already-correct text."""
    if not value or value.isascii():
        return value, False
    try:
        fixed = value.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return value, False
    return fixed, fixed != value


def _load(raw: bytes | str | dict[str, Any]) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, bytes):
        if len(raw) > MAX_FILE_BYTES:
            raise MessengerImportError(f"File exceeds {MAX_FILE_BYTES // (1024 * 1024)} MB limit")
        try:
            raw = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise MessengerImportError("File is not valid UTF-8 JSON") from exc
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise MessengerImportError(f"Malformed JSON (line {exc.lineno}, column {exc.colno})") from exc
    if not isinstance(data, dict):
        raise MessengerImportError("Top-level JSON value must be an object")
    return data


def _to_utc(ts_ms: Any) -> datetime | None:
    if isinstance(ts_ms, bool) or not isinstance(ts_ms, (int, float)):
        return None
    try:
        return datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
    except (OverflowError, OSError, ValueError):
        return None


def _first(item: dict[str, Any], *keys: str) -> Any:
    """Value of the first key present in ``item`` (supports both export flavours)."""
    for key in keys:
        if key in item:
            return item[key]
    return None


def parse_messenger(files: Iterable[bytes | str | dict[str, Any]]) -> ParseResult:
    """Parse one or more message_N.json payloads of the SAME conversation."""
    report = ImportReport()
    title: str | None = None
    participants: dict[str, None] = {}  # ordered set
    messages: list[Message] = []
    seen: set[tuple[str | None, int, str | None, MessageKind]] = set()

    def clean(value: str) -> str:
        fixed_text, fixed = repair_mojibake(value.strip())
        report.encoding_repaired |= fixed
        return fixed_text

    for raw in files:
        data = _load(raw)
        report.files_read += 1

        if "messages" not in data or not isinstance(data["messages"], list):
            raise MessengerImportError("Missing 'messages' array: not a Messenger export file")

        raw_title = _first(data, "title", "threadName")
        if title is None and isinstance(raw_title, str):
            title = clean(raw_title)

        for p in data.get("participants") or []:
            name = p.get("name") if isinstance(p, dict) else p  # dict or plain string
            if isinstance(name, str) and name.strip():
                participants.setdefault(clean(name))

        for item in data["messages"]:
            report.messages_total += 1
            if not isinstance(item, dict):
                report.skipped_empty += 1
                continue

            ts = _to_utc(_first(item, "timestamp_ms", "timestamp"))
            if ts is None:
                report.skipped_invalid_timestamp += 1
                continue

            sender = _first(item, "sender_name", "senderName")
            if isinstance(sender, str) and sender.strip():
                sender = clean(sender)
                participants.setdefault(sender)
            else:
                sender = None
                report.missing_sender += 1

            if item.get("isUnsent") is True:  # retracted message: nothing usable left
                report.skipped_empty += 1
                continue

            content = _first(item, "content", "text")
            text = clean(content) if isinstance(content, str) and content.strip() else None

            has_attachment = any(item.get(k) for k in (*ATTACHMENT_KEYS, "media"))
            msg_type = item.get("type")
            is_system = (
                (isinstance(msg_type, str) and msg_type.lower() in SYSTEM_TYPES)
                or item.get("call_duration") is not None
            )

            if text and not is_system:
                kind = MessageKind.TEXT
            elif has_attachment:
                kind, text = MessageKind.MEDIA, None
            elif is_system:
                kind, text = MessageKind.OTHER, None
            else:
                report.skipped_empty += 1
                continue

            fingerprint = (sender, int(ts.timestamp() * 1000), text, kind)
            if fingerprint in seen:
                report.duplicates_removed += 1
                continue
            seen.add(fingerprint)

            messages.append(
                Message(sender=sender, timestamp=ts, text=text, kind=kind, has_attachment=has_attachment)
            )

    messages.sort(key=lambda m: m.timestamp)  # files and exports differ in order; sort once
    report.messages_kept = len(messages)
    if not messages:
        report.warnings.append("No usable messages were found in the export.")

    return ParseResult(
        conversation=Conversation(title=title, participants=list(participants), messages=messages),
        report=report,
    )
