"""In-memory store. Nothing is written to disk by default (local-first, deletable)."""
from __future__ import annotations

import uuid

from app.schemas.messages import Conversation
from app.schemas.profile import Profile


class ImportStore:
    def __init__(self) -> None:
        self._items: dict[str, Conversation] = {}
        self._profiles: dict[str, Profile] = {}

    def add(self, conv: Conversation) -> str:
        import_id = uuid.uuid4().hex
        self._items[import_id] = conv
        return import_id

    def get(self, import_id: str) -> Conversation | None:
        return self._items.get(import_id)

    def set_profile(self, import_id: str, profile: Profile) -> None:
        self._profiles[import_id] = profile

    def get_profile(self, import_id: str) -> Profile | None:
        return self._profiles.get(import_id)

    def delete(self, import_id: str) -> bool:
        """Deletes the import and every derived profile."""
        self._profiles.pop(import_id, None)
        return self._items.pop(import_id, None) is not None

    def clear(self) -> None:
        self._items.clear()
        self._profiles.clear()


store = ImportStore()
