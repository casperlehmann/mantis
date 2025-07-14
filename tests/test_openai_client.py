import pytest
from unittest.mock import MagicMock

from mantis.mantis_client import MantisClient


class TestOpenAIClient:
    def test_get_completion_is_disabled(self, fake_mantis: MantisClient):
        fake_mantis.open_ai_client.disabled = True
        with pytest.raises(ConnectionError):
            fake_mantis.open_ai_client.get_completion("input", "prompt")

    def test_get_completion_empty_response(self, fake_mantis: MantisClient):
        fake_mantis.open_ai_client.disabled = False
        open_ai_mock = MagicMock()
        completion = MagicMock()
        fake_mantis.open_ai_client.open_ai = open_ai_mock
        open_ai_mock.chat.completions.create = completion
        completion.return_value.choices = [
            type("obj", (), {"message": type("msg", (), {"content": None})()})
        ]
        with pytest.raises(ValueError):
            fake_mantis.open_ai_client.get_completion("input", "prompt")
  
    def test_get_completion_valid_response(self, fake_mantis: MantisClient):
        fake_mantis.open_ai_client.disabled = False
        open_ai_mock = MagicMock()
        completion = MagicMock()
        fake_mantis.open_ai_client.open_ai = open_ai_mock
        open_ai_mock.chat.completions.create = completion
        completion.return_value.choices = [
            type("obj", (), {"message": type("msg", (), {"content": "Hello world!"})()})
        ]
        result = fake_mantis.open_ai_client.get_completion("input", "prompt")
        assert result == "Hello world!"
