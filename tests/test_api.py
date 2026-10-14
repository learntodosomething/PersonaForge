import json

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.store import store


@pytest.fixture
def client():
    store.clear()
    return TestClient(app)


def _upload(client, payload: bytes, confirm: bool = True):
    return client.post(
        "/api/imports",
        files=[("files", ("message_1.json", payload, "application/json"))],
        data={"confirm_authorized": str(confirm).lower()},
    )


def test_health(client):
    assert client.get("/health").json()["status"] == "ok"


def test_import_requires_authorization_confirmation(client, basic_export):
    r = _upload(client, json.dumps(basic_export).encode(), confirm=False)
    assert r.status_code == 422


def test_import_select_and_delete_flow(client, basic_export):
    r = _upload(client, json.dumps(basic_export).encode())
    assert r.status_code == 201
    body = r.json()
    assert {s["name"] for s in body["speakers"]} == {"Alice Example", "Bob Example"}
    assert "Szia" not in r.text  # response carries counts, never raw messages

    import_id = body["import_id"]
    assert client.get(f"/api/imports/{import_id}/speakers").status_code == 200
    assert client.delete(f"/api/imports/{import_id}").status_code == 204
    assert client.get(f"/api/imports/{import_id}/speakers").status_code == 404
    assert client.delete(f"/api/imports/{import_id}").status_code == 404


def test_malformed_upload_returns_400(client):
    assert _upload(client, b"{not json").status_code == 400
