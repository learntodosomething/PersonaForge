import json

import pytest
from conftest import to_mojibake

from app.importers.messenger import MessengerImportError, parse_messenger, repair_mojibake
from app.schemas.messages import MessageKind


def test_valid_export_is_normalized_and_sorted(basic_export):
    result = parse_messenger([basic_export])
    msgs = result.conversation.messages
    assert [m.timestamp for m in msgs] == sorted(m.timestamp for m in msgs)
    assert [m.kind for m in msgs] == [
        MessageKind.OTHER, MessageKind.TEXT, MessageKind.MEDIA, MessageKind.TEXT
    ]
    assert result.report.messages_total == result.report.messages_kept == 4
    assert result.conversation.participants == ["Alice Example", "Bob Example"]


def test_text_and_non_text_messages(basic_export):
    msgs = parse_messenger([basic_export]).conversation.messages
    media = next(m for m in msgs if m.kind is MessageKind.MEDIA)
    assert media.text is None and media.has_attachment
    call = next(m for m in msgs if m.kind is MessageKind.OTHER)
    assert call.text is None


def test_empty_messages_array_gives_warning_not_crash():
    result = parse_messenger([{"participants": [], "messages": []}])
    assert result.conversation.messages == []
    assert result.report.warnings


def test_missing_messages_key_is_error():
    with pytest.raises(MessengerImportError, match="messages"):
        parse_messenger([{"participants": []}])


def test_malformed_json_error_does_not_leak_content():
    secret = "TOP-SECRET-MESSAGE"
    with pytest.raises(MessengerImportError) as exc:
        parse_messenger([b'{"messages": [ {"content": "' + secret.encode() + b'" '])
    assert secret not in str(exc.value)


def test_non_object_and_invalid_encoding():
    with pytest.raises(MessengerImportError):
        parse_messenger([b"[1, 2, 3]"])
    with pytest.raises(MessengerImportError):
        parse_messenger([b"\xff\xfe\x00bad"])


def test_missing_sender_is_counted_and_kept():
    data = {"messages": [{"timestamp_ms": 1700000000000, "content": "hi"}]}
    result = parse_messenger([data])
    assert result.conversation.messages[0].sender is None
    assert result.report.missing_sender == 1


@pytest.mark.parametrize("bad_ts", [None, "yesterday", True, 1e30, -1e30])
def test_invalid_timestamps_are_skipped(bad_ts):
    data = {"messages": [{"sender_name": "A", "timestamp_ms": bad_ts, "content": "x"}]}
    result = parse_messenger([data])
    assert result.conversation.messages == []
    assert result.report.skipped_invalid_timestamp == 1


def test_empty_records_skipped():
    data = {"messages": [{"sender_name": "A", "timestamp_ms": 1700000000000}, "junk"]}
    result = parse_messenger([data])
    assert result.report.skipped_empty == 2


def test_multiple_files_are_merged_in_order(basic_export):
    second = {
        "participants": [{"name": "Carol Example"}],
        "messages": [{"sender_name": "Carol Example", "timestamp_ms": 1600000000000, "content": "old"}],
    }
    result = parse_messenger([basic_export, second])
    assert result.report.files_read == 2
    assert result.conversation.messages[0].text == "old"
    assert "Carol Example" in result.conversation.participants


def test_hungarian_mojibake_is_repaired():
    original = "Árvíztűrő tükörfúrógép, szia!"
    data = {
        "title": to_mojibake("Beszélgetés"),
        "participants": [{"name": to_mojibake("Kovács Éva")}],
        "messages": [
            {"sender_name": to_mojibake("Kovács Éva"), "timestamp_ms": 1700000000000,
             "content": to_mojibake(original)}
        ],
    }
    result = parse_messenger([json.dumps(data)])
    assert result.conversation.messages[0].text == original
    assert result.conversation.participants == ["Kovács Éva"]
    assert result.conversation.title == "Beszélgetés"
    assert result.report.encoding_repaired


def test_correct_unicode_is_left_alone():
    assert repair_mojibake("Árvíztűrő") == ("Árvíztűrő", False)
    assert repair_mojibake("plain ascii") == ("plain ascii", False)
