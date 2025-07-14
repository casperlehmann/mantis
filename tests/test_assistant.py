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
    
    def test_convert_text_format_raises_unrecognized_format(self, fake_mantis: 'MantisClient'):
        fake_mantis.open_ai_client.disabled = False
        fake_mantis.open_ai_client.get_completion = MagicMock()
        fake_mantis.open_ai_client.get_completion.return_value = "h1. Biggest heading\n\nh2. Bigger heading\n\nNormal *bold* _italic_ text"
        with pytest.raises(ValueError, match="Unrecognized format: fake_format"):
            fake_mantis.assistant.convert_text_format(
                '# Biggest heading\n\n## Bigger heading\n\nNormal *bold* _italic_ text',
                "fake_format"  # type: ignore
            )

    def test_convert_text_format_returns_no_changes_needed(self, fake_mantis: 'MantisClient'):
        fake_mantis.open_ai_client.disabled = False
        fake_mantis.open_ai_client.get_completion = MagicMock()
        fake_mantis.open_ai_client.get_completion.return_value = "No changes needed"
        result = fake_mantis.assistant.convert_text_format(
            'Plain text remains unchanged',
            TextFormat.JIRA)
        assert result == "Plain text remains unchanged"
    
    def test_convert_text_format_returns_has_a_question(self, fake_mantis: 'MantisClient'):
        fake_mantis.open_ai_client.disabled = False
        fake_mantis.open_ai_client.get_completion = MagicMock()
        fake_mantis.open_ai_client.get_completion.return_value = "I have a question: What is love?"
        with pytest.raises(ValueError, match="Question from AI: What is love?"):
            fake_mantis.assistant.convert_text_format(
                'Anything you always wanted to know?',
                TextFormat.JIRA)

    def test_make_verbose(self, fake_mantis: 'MantisClient'):
        fake_mantis.open_ai_client.disabled = False
        fake_mantis.open_ai_client.get_completion = MagicMock()
        fake_mantis.open_ai_client.get_completion.return_value = "1, 2, 3, 4, 5, 6, 7, 8, 9, 10 - this is a very important and detailed task!"
        result = fake_mantis.assistant.make_verbose('Count to 10. Very important.')
        assert result == "1, 2, 3, 4, 5, 6, 7, 8, 9, 10 - this is a very important and detailed task!"

    def test_make_verbose_no_changes_needed(self, fake_mantis: 'MantisClient'):
        fake_mantis.open_ai_client.disabled = False
        fake_mantis.open_ai_client.get_completion = MagicMock()
        fake_mantis.open_ai_client.get_completion.return_value = "No changes needed"
        result = fake_mantis.assistant.make_verbose('The most verbose text.')
        assert result == "The most verbose text."

    def test_make_verbose_has_a_question(self, fake_mantis: 'MantisClient'):
        fake_mantis.open_ai_client.disabled = False
        fake_mantis.open_ai_client.get_completion = MagicMock()
        fake_mantis.open_ai_client.get_completion.return_value = "I have a question: Who am I?"
        with pytest.raises(ValueError, match="Question from AI: Who am I?"):
            fake_mantis.assistant.make_verbose('Awkward silence.')
