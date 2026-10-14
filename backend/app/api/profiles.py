from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.profile import Profile, ProfileRequest, ProfileUpdate
from app.services.profiling import apply_update, build_profile
from app.store import store

router = APIRouter(prefix="/api/imports/{import_id}/profile", tags=["profile"])


def _stored(import_id: str) -> Profile:
    profile = store.get_profile(import_id)
    if profile is None:
        raise HTTPException(404, "Profile not found")
    return profile


@router.post("", response_model=Profile)
def create_profile(import_id: str, req: ProfileRequest) -> Profile:
    conv = store.get(import_id)
    if conv is None:
        raise HTTPException(404, "Import not found")
    try:
        profile = build_profile(conv, req.speaker)
    except KeyError as exc:
        raise HTTPException(404, "Speaker not found") from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    store.set_profile(import_id, profile)
    return profile


@router.get("", response_model=Profile)
def get_profile(import_id: str) -> Profile:
    return _stored(import_id)


@router.put("", response_model=Profile)
def update_profile(import_id: str, update: ProfileUpdate) -> Profile:
    profile = _stored(import_id)
    ids = [t.id for t in update.traits]
    if len(set(ids)) != len(ids):
        raise HTTPException(422, "Trait ids must be unique")
    merged = apply_update(profile, update)
    store.set_profile(import_id, merged)
    return merged
