"""Style profile models. Metrics are observed numbers; traits mix observed, inferred and user-written lines."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class Counted(BaseModel):
    text: str
    count: int


class StyleMetrics(BaseModel):
    message_count: int
    chars_median: int
    chars_p90: int
    words_median: int
    short_share: float              # messages with <= 20 characters
    turns: int
    messages_per_turn_mean: float
    messages_per_turn_p90: int
    emoji_message_share: float
    emoji_per_message: float
    emoji_end_share: float
    repeated_emoji_share: float     # same emoji 3+ times in a row
    top_emojis: list[Counted]
    stretched_message_share: float  # a letter repeated 3+ times ("sooooo")
    question_share: float
    exclamation_share: float
    ellipsis_share: float
    terminal_punct_share: float
    lowercase_start_share: float
    allcaps_share: float
    top_words: list[Counted]
    top_bigrams: list[Counted]
    repeated_messages: list[Counted]


class Trait(BaseModel):
    id: str = Field(min_length=1, max_length=64)
    text: str = Field(min_length=1, max_length=500)
    kind: Literal["observed", "inferred", "user"]
    evidence: str = Field("", max_length=300)
    enabled: bool = True


class Profile(BaseModel):
    speaker: str
    generated_at: datetime
    based_on_messages: int
    metrics: StyleMetrics
    traits: list[Trait]
    notes: str = ""
    warnings: list[str] = Field(default_factory=list)


class ProfileRequest(BaseModel):
    speaker: str = Field(min_length=1)


class ProfileUpdate(BaseModel):
    traits: list[Trait] = Field(max_length=50)
    notes: str = Field("", max_length=4000)
