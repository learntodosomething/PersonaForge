import json
from pathlib import Path

from app.importers.messenger import parse_messenger
from app.schemas.messages import MessageKind

FIXTURES = Path(__file__).parent / "fixtures"


def _e2ee() -> dict:
    return json.loads((FIXTURES / "messenger_e2ee.json").read_text(encoding="utf-8"))


def test_e2ee_export_is_parsed():
    result = parse_messenger([_e2ee()])
    conv, report = result.conversation, result.report
    assert conv.title == "Synthetic chat_10"
    assert conv.participants == ["Alice Example", "Bob Example"]
    assert [m.kind for m in conv.messages] == [MessageKind.TEXT, MessageKind.MEDIA, MessageKind.TEXT]
    assert conv.messages[0].text == "jó reggelt ❤️"
    assert conv.messages[1].has_attachment and conv.messages[1].text is None
    assert report.messages_total == 4
    assert report.messages_kept == 3
    assert report.skipped_empty == 1  # the unsent message
    assert report.skipped_invalid_timestamp == 0 and report.missing_sender == 0


def test_dyi_and_e2ee_files_are_merged_in_order_and_deduplicated(basic_export):
    older = {
        "participants": [{"name": "Alice Example"}, {"name": "Bob Example"}],
        "title": "Synthetic chat",
        "messages": [  # newest first, like a "download your information" file
            {"sender_name": "Bob Example", "timestamp_ms": 1706957309084, "content": "overlap"},
            {"sender_name": "Alice Example", "timestamp_ms": 1700000000000, "content": "old"},
        ],
    }
    newer = _e2ee()
    newer["messages"].append(  # same message also present in the older file
        {"senderName": "Bob Example", "text": "overlap", "timestamp": 1706957309084,
         "type": "text", "media": [], "isUnsent": False}
    )
    result = parse_messenger([older, newer])
    msgs = result.conversation.messages
    assert [m.timestamp for m in msgs] == sorted(m.timestamp for m in msgs)
    assert result.report.duplicates_removed == 1
    assert sum(1 for m in msgs if m.text == "overlap") == 1
    assert result.conversation.title == "Synthetic chat"  # first file wins
    assert result.report.files_read == 2
