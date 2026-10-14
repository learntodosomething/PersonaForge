"""Normalized, source-agnostic message models.

Every importer (Messenger today, others later) converts raw exports into these
types so the rest of the pipeline never touches platform-specific JSON.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class MessageKind(str, Enum):
    TEXT = "text"      # has usable text content
    MEDIA = "media"    # photo / video / audio / file / sticker without text
    OTHER = "other"    # calls, system events, unsupported


class Message(BaseModel):
    sender: str | None = Field(None, description="Display name; None if missing in the export")
    timestamp: datetime = Field(..., description="UTC timestamp")
    text: str | None = None
    kind: MessageKind
    has_attachment: bool = False


class Conversation(BaseModel):
    title: str | None = None
    participants: list[str] = Field(default_factory=list)
    messages: list[Message] = Field(default_factory=list)  # chronological, oldest first


class ImportReport(BaseModel):
    """Counts only; never contains raw message text (see docs/PRIVACY.md)."""

    files_read: int = 0
    messages_total: int = 0
    messages_kept: int = 0
    skipped_invalid_timestamp: int = 0
    skipped_empty: int = 0
    duplicates_removed: int = 0
    missing_sender: int = 0
    encoding_repaired: bool = False
    warnings: list[str] = Field(default_factory=list)


class ParseResult(BaseModel):
    conversation: Conversation
    report: ImportReport


class SpeakerSummary(BaseModel):
    name: str
    message_count: int
    text_message_count: int


class SpeakerStats(BaseModel):
    name: str
    text_message_count: int
    median_chars: int
    p90_chars: int


class MonthActivity(BaseModel):
    month: str  # "YYYY-MM" (UTC)
    counts: dict[str, int]  # speaker name -> text messages in that month


class Overview(BaseModel):
    """Aggregates only; never contains message text."""

    first_message: datetime | None = None
    last_message: datetime | None = None
    span_days: int = 0
    active_months: int = 0
    months: list[MonthActivity] = Field(default_factory=list)  # continuous, gaps filled with zeros
    speakers: list[SpeakerStats] = Field(default_factory=list)
