import json
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.importers.messenger import parse_messenger
from app.main import app
from app.services.overview import build_overview
from app.store import store


def ms(y, m, d):
    return int(datetime(y, m, d, 12, tzinfo=timezone.utc).timestamp() * 1000)


def _conv():
    data = {"messages": [
        {"sender_name": "Ann", "timestamp_ms": ms(2023, 1, 5), "content": "abcd"},
        {"sender_name": "Ann", "timestamp_ms": ms(2023, 1, 6), "content": "abcdefgh"},
        {"sender_name": "Ben", "timestamp_ms": ms(2023, 1, 7), "content": "hi"},
        {"sender_name": "Ben", "timestamp_ms": ms(2023, 4, 1), "content": "hello there"},
        {"sender_name": "Ann", "timestamp_ms": ms(2023, 4, 2), "photos": [{"uri": "x"}]},
    ]}
    return parse_messenger([data]).conversation


def test_months_are_continuous_with_zero_gaps():
    ov = build_overview(_conv())
    assert [m.month for m in ov.months] == ["2023-01", "2023-02", "2023-03", "2023-04"]
    assert ov.months[0].counts == {"Ann": 2, "Ben": 1}
    assert ov.months[1].counts == {"Ann": 0, "Ben": 0}
    assert ov.months[3].counts == {"Ann": 0, "Ben": 1}  # photo is not a text message
    assert ov.active_months == 2


def test_range_and_speaker_stats():
    ov = build_overview(_conv())
    assert ov.first_message.date().isoformat() == "2023-01-05"
    assert ov.last_message.date().isoformat() == "2023-04-01"
    assert ov.span_days == 86
    ann = next(s for s in ov.speakers if s.name == "Ann")
    assert ann.text_message_count == 2 and ann.median_chars == 8 and ann.p90_chars == 8


def test_empty_conversation_has_no_dates():
    ov = build_overview(parse_messenger([{"messages": []}]).conversation)
    assert ov.first_message is None and ov.months == [] and ov.span_days == 0


def test_overview_endpoint_returns_aggregates_only():
    store.clear()
    client = TestClient(app)
    raw = json.dumps({"messages": [
        {"sender_name": "Ann", "timestamp_ms": ms(2023, 1, 5), "content": "SECRET-TEXT"}]}).encode()
    r = client.post("/api/imports", files=[("files", ("message_1.json", raw))],
                    data={"confirm_authorized": "true"})
    iid = r.json()["import_id"]
    ov = client.get(f"/api/imports/{iid}/overview")
    assert ov.status_code == 200 and "SECRET-TEXT" not in ov.text
    assert ov.json()["months"][0]["counts"] == {"Ann": 1}
    assert client.get("/api/imports/nope/overview").status_code == 404
