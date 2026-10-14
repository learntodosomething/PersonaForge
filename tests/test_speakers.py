import pytest

from app.importers.messenger import parse_messenger
from app.services.speakers import list_speakers, speaker_text_messages


def test_speaker_summary_counts(basic_export):
    conv = parse_messenger([basic_export]).conversation
    summary = {s.name: s for s in list_speakers(conv)}
    assert summary["Alice Example"].message_count == 2
    assert summary["Alice Example"].text_message_count == 1
    assert summary["Bob Example"].message_count == 2
    assert summary["Bob Example"].text_message_count == 1


def test_only_selected_speakers_text_is_used(basic_export):
    conv = parse_messenger([basic_export]).conversation
    msgs = speaker_text_messages(conv, "Alice Example")
    assert [m.text for m in msgs] == ["Hello Bob"]
    assert all(m.sender == "Alice Example" for m in msgs)


def test_unknown_speaker_raises(basic_export):
    conv = parse_messenger([basic_export]).conversation
    with pytest.raises(KeyError):
        speaker_text_messages(conv, "Mallory")
