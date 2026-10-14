import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def basic_export() -> dict:
    return json.loads((FIXTURES / "messenger_basic.json").read_text(encoding="utf-8"))


def to_mojibake(text: str) -> str:
    """Simulate Meta's export bug: UTF-8 bytes shown as Latin-1 characters."""
    return text.encode("utf-8").decode("latin-1")
