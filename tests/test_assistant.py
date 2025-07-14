import pytest
from unittest.mock import MagicMock
from enums.text_format import TextFormat
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mantis.mantis_client import MantisClient


class TestAssistant:
    def test_convert_text_format_j_to_m(self, fake_mantis: 'MantisClient'):
        fake_mantis.open_ai_client.disabled = False
        fake_mantis.open_ai_client.get_completion = MagicMock()
        fake_mantis.open_ai_client.get_completion.return_value = "# Biggest heading\n\n## Bigger heading\n\nNormal *bold* _italic_ text"
        result = fake_mantis.assistant.convert_text_format(
            'h1. Biggest heading\n\nh2. Bigger heading\n\nNormal *bold* _italic_ text',
            TextFormat.MARKDOWN)
        assert result == "# Biggest heading\n\n## Bigger heading\n\nNormal *bold* _italic_ text"

    def test_convert_text_format_m_to_j(self, fake_mantis: 'MantisClient'):
        fake_mantis.open_ai_client.disabled = False
        fake_mantis.open_ai_client.get_completion = MagicMock()
        fake_mantis.open_ai_client.get_completion.return_value = "h1. Biggest heading\n\nh2. Bigger heading\n\nNormal *bold* _italic_ text"
        result = fake_mantis.assistant.convert_text_format(
            '# Biggest heading\n\n## Bigger heading\n\nNormal *bold* _italic_ text',
            TextFormat.JIRA)
        assert result == "h1. Biggest heading\n\nh2. Bigger heading\n\nNormal *bold* _italic_ text"
        


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

def test_make_verbose_no_changes():
    mantis = DummyMantis()
    mantis.open_ai_client.get_completion.return_value = "No changes needed"
    assistant = Assistant(mantis)
    result = assistant.make_verbose("Some task")
    assert result == "Some task"

def test_make_verbose_question():
    mantis = DummyMantis()
    mantis.open_ai_client.get_completion.return_value = "I have a question: Can you clarify?"
    assistant = Assistant(mantis)
    with pytest.raises(ValueError) as exc:
        assistant.make_verbose("Some task")
    assert "Question from AI" in str(exc.value)

def test_make_verbose_conversion():
    mantis = DummyMantis()
    mantis.open_ai_client.get_completion.return_value = "This is a very important and detailed task!"
    assistant = Assistant(mantis)
    result = assistant.make_verbose("Some task")
    assert result == "This is a very important and detailed task!"
