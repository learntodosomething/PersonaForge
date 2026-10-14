# Backend

Python + FastAPI service. **Phase 1 (foundation) is implemented:** normalized schemas,
Messenger JSON parser, speaker selection, and the first import API.

## Run

```bash
cd backend
python -m venv .venv            # Windows: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"
uvicorn app.main:app --reload   # http://127.0.0.1:8000/docs
pytest                          # runs ../tests
```

## Layout

- `app/main.py` — FastAPI application entry point
- `app/api/imports.py` — `POST /api/imports`, `GET /api/imports/{id}/speakers`, `DELETE /api/imports/{id}`
- `app/schemas/messages.py` — validated, source-agnostic message models
- `app/importers/messenger.py` — Messenger JSON parser (repairs Meta's Latin-1/UTF-8 mojibake)
- `app/services/speakers.py` — speaker listing and selection (only the selected speaker's text is used for profiling)
- `app/store.py` — in-memory import store (nothing written to disk; deletable)
- Planned: `services/profiling.py`, `services/retrieval.py`, `services/chat.py`

Parsing and cleaning logic is testable without starting the API server.
Import reports contain counts only, never raw message text.
