# Backend

Planned Python + FastAPI service.

Suggested modules once implementation begins:

- `app/main.py` — FastAPI application entry point
- `app/api/` — HTTP routes
- `app/schemas/` — validated request and response models
- `app/importers/messenger.py` — Messenger JSON parser
- `app/services/profiling.py` — style analysis
- `app/services/retrieval.py` — conversation retrieval
- `app/services/chat.py` — persona chat orchestration
- `tests/` — unit and integration tests

Keep parsing and data-cleaning logic testable without starting the API server.
