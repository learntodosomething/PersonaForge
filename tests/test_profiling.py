import json
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from app.importers.messenger import parse_messenger
from app.main import app
from app.schemas.profile import ProfileUpdate, Trait
from app.services.profiling import apply_update, build_profile, compute_metrics
from app.store import store

GAP = timedelta(minutes=10)
BASE = 1_700_000_000_000


def conv_from(msgs):
    data = {"messages": [{"sender_name": s, "timestamp_ms": BASE + sec * 1000, "content": t} for s, sec, t in msgs]}
    return parse_messenger([data]).conversation


def seq(sender, texts, start=0):
    return [(sender, start + i, t) for i, t in enumerate(texts)]


def test_emoji_metrics():
    conv = conv_from(seq("Ann", ["Szia ❤️❤️❤️", "ok 😝", "semmi", "nyújtott igeeeen"]))
    m = compute_metrics(conv, "Ann", GAP)
    assert m.message_count == 4
    assert m.emoji_message_share == 0.5 and m.emoji_per_message == 1.0
    assert m.repeated_emoji_share == 0.25 and m.emoji_end_share == 0.5
    assert m.top_emojis[0].text == "❤️" and m.top_emojis[0].count == 3


def test_stretched_letters_and_vocabulary_collapse():
    conv = conv_from(seq("Ann", ["igeeeen"] * 3 + ["igen"] * 3))
    m = compute_metrics(conv, "Ann", GAP)
    assert m.stretched_message_share == 0.5
    assert m.top_words[0].text == "igen" and m.top_words[0].count == 6


def test_punctuation_shares():
    conv = conv_from(seq("Ann", ["Kész?", "Nagyon jó!", "megyek...", "ok", "Szia."]))
    m = compute_metrics(conv, "Ann", GAP)
    assert (m.question_share, m.exclamation_share, m.ellipsis_share) == (0.2, 0.2, 0.2)
    assert m.terminal_punct_share == 0.8 and m.lowercase_start_share == 0.4


def test_turn_grouping_with_gap():
    conv = conv_from([("Ann", 0, "a"), ("Ann", 10, "b"), ("Ben", 20, "c"), ("Ann", 30, "d"), ("Ann", 730, "e")])
    m = compute_metrics(conv, "Ann", GAP)
    assert m.turns == 3 and m.messages_per_turn_mean == pytest.approx(1.33, abs=0.01)


def test_other_speakers_content_is_never_used():
    msgs = seq("Ann", [f"üzenet szám {i}" for i in range(10)]) + seq("Ben", ["xyzzy xyzzy 🔥🔥🔥"] * 20, start=100)
    m = compute_metrics(conv_from(msgs), "Ann", GAP)
    assert not any("xyzzy" in w.text for w in m.top_words + m.top_bigrams + m.repeated_messages)
    assert m.top_emojis == [] and m.emoji_message_share == 0


def test_traits_separate_observed_from_inferred():
    conv = conv_from(seq("Ann", ["Oooooh ❤️❤️❤️"] * 30))
    traits = {t.id: t for t in build_profile(conv, "Ann").traits}
    assert {"emoji", "emoji-repeat", "stretch", "recurring"} <= set(traits)
    assert traits["emoji"].kind == "observed" and traits["tone"].kind == "inferred"
    assert traits["tone"].evidence


def test_plain_speaker_gets_no_emoji_traits():
    conv = conv_from(seq("Ann", ["Megyek haza vacsorázni."] * 10))
    ids = {t.id for t in build_profile(conv, "Ann").traits}
    assert "emoji" not in ids and "tone" not in ids


def test_small_sample_warning_and_errors():
    conv = conv_from(seq("Ann", ["hello"] * 5))
    assert build_profile(conv, "Ann").warnings
    with pytest.raises(KeyError):
        build_profile(conv, "Mallory")
    only_photo = parse_messenger([{"messages": [
        {"sender_name": "Ann", "timestamp_ms": BASE, "photos": [{"uri": "x"}]},
        {"sender_name": "Ben", "timestamp_ms": BASE + 1, "content": "hi"}]}]).conversation
    with pytest.raises(ValueError):
        build_profile(only_photo, "Ann")


def test_apply_update_tracks_edits():
    profile = build_profile(conv_from(seq("Ann", ["Oooooh ❤️❤️❤️"] * 30)), "Ann")
    by_id = {t.id: t for t in profile.traits}
    edited = [
        by_id["emoji"].model_copy(update={"text": "Saját megfogalmazás", "enabled": False}),
        by_id["tone"],
        Trait(id="user-1", text="Új sor", kind="observed"),  # client cannot claim 'observed'
    ]
    out = apply_update(profile, ProfileUpdate(traits=edited, notes="jegyzet"))
    kinds = {t.id: t for t in out.traits}
    assert kinds["emoji"].kind == "user" and kinds["emoji"].enabled is False
    assert kinds["emoji"].evidence == by_id["emoji"].evidence
    assert kinds["tone"].kind == "inferred"
    assert kinds["user-1"].kind == "user" and out.notes == "jegyzet"
    assert out.metrics == profile.metrics


@pytest.fixture
def client():
    store.clear()
    return TestClient(app)


def _import(client):
    msgs = [{"sender_name": "Ann", "timestamp_ms": BASE + i * 1000, "content": "Oooooh ❤️❤️❤️"} for i in range(30)]
    msgs.append({"sender_name": "Ben", "timestamp_ms": BASE + 99_000, "content": "hi"})
    r = client.post("/api/imports", files=[("files", ("m.json", json.dumps({"messages": msgs}).encode()))],
                    data={"confirm_authorized": "true"})
    return r.json()["import_id"]


def test_profile_api_flow(client):
    iid = _import(client)
    base = f"/api/imports/{iid}/profile"
    assert client.get(base).status_code == 404
    assert client.post(base, json={"speaker": "Mallory"}).status_code == 404
    r = client.post(base, json={"speaker": "Ann"})
    assert r.status_code == 200 and r.json()["speaker"] == "Ann"
    traits = r.json()["traits"]
    traits[0]["text"] = "Átírt sor"
    put = client.put(base, json={"traits": traits, "notes": "x"})
    assert put.status_code == 200 and put.json()["traits"][0]["kind"] == "user"
    assert client.get(base).json()["notes"] == "x"
    dup = client.put(base, json={"traits": [traits[0], traits[0]], "notes": ""})
    assert dup.status_code == 422


def test_deleting_import_deletes_profile(client):
    iid = _import(client)
    client.post(f"/api/imports/{iid}/profile", json={"speaker": "Ann"})
    assert client.delete(f"/api/imports/{iid}").status_code == 204
    assert store.get_profile(iid) is None
