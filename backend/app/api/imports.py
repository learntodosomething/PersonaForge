from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.importers.messenger import MessengerImportError, parse_messenger
from app.schemas.messages import ImportReport, Overview, SpeakerSummary
from app.services.overview import build_overview
from app.services.speakers import list_speakers
from app.store import store

router = APIRouter(prefix="/api/imports", tags=["imports"])


class ImportResponse(BaseModel):
    import_id: str
    title: str | None
    report: ImportReport
    speakers: list[SpeakerSummary]


@router.post("", response_model=ImportResponse, status_code=201)
async def create_import(
    files: list[UploadFile] = File(..., description="message_N.json files of ONE conversation"),
    confirm_authorized: bool = Form(False),
) -> ImportResponse:
    if not confirm_authorized:
        raise HTTPException(422, "You must confirm you are authorized to process this data.")
    payloads = [await f.read() for f in files]
    try:
        result = parse_messenger(payloads)
    except MessengerImportError as exc:
        raise HTTPException(400, str(exc)) from exc
    import_id = store.add(result.conversation)
    return ImportResponse(
        import_id=import_id,
        title=result.conversation.title,
        report=result.report,
        speakers=list_speakers(result.conversation),
    )


@router.get("/{import_id}/speakers", response_model=list[SpeakerSummary])
def get_speakers(import_id: str) -> list[SpeakerSummary]:
    conv = store.get(import_id)
    if conv is None:
        raise HTTPException(404, "Import not found")
    return list_speakers(conv)


@router.get("/{import_id}/overview", response_model=Overview)
def get_overview(import_id: str) -> Overview:
    conv = store.get(import_id)
    if conv is None:
        raise HTTPException(404, "Import not found")
    return build_overview(conv)


@router.delete("/{import_id}", status_code=204)
def delete_import(import_id: str) -> None:
    if not store.delete(import_id):
        raise HTTPException(404, "Import not found")
