import pytest
from unittest.mock import MagicMock
from src.assistant.assistant import Assistant, TextFormat

class DummyMantis:
    def __init__(self):
        self.open_ai_client = MagicMock()

def test_convert_text_format_no_changes():
    mantis = DummyMantis()
    mantis.open_ai_client.get_completion.return_value = "No changes needed"
    assistant = Assistant(mantis)
    result = assistant.convert_text_format("Some text", TextFormat.MARKDOWN)
    assert result == "Some text"

def test_convert_text_format_question():
    mantis = DummyMantis()
    mantis.open_ai_client.get_completion.return_value = "I have a question: What is the format?"
    assistant = Assistant(mantis)
    with pytest.raises(ValueError) as exc:
        assistant.convert_text_format("Some text", TextFormat.MARKDOWN)
    assert "Question from AI" in str(exc.value)

def test_convert_text_format_conversion():
    mantis = DummyMantis()
    mantis.open_ai_client.get_completion.return_value = "Converted text"
    assistant = Assistant(mantis)
    result = assistant.convert_text_format("Some text", TextFormat.MARKDOWN)
    assert result == "Converted text"
