import pytest
from unittest.mock import MagicMock, patch
from src.mantis.openai_client import OpenAIClient

class DummyOptions:
    chat_gpt_activated = True
    chat_gpt_base_url = "https://api.openai.com/v1"
    chat_gpt_api_key = "fake_key"

class DummyMantis:
    def __init__(self, activated=True):
        self.options = DummyOptions()
        self.options.chat_gpt_activated = activated

def test_openai_client_disabled():
    mantis = DummyMantis(activated=False)
    client = OpenAIClient(mantis)
    with pytest.raises(ConnectionError):
        client.get_completion("input", "prompt")

@patch("src.mantis.openai_client.OpenAI")
def test_openai_client_empty_response(MockOpenAI):
    mantis = DummyMantis()
    client = OpenAIClient(mantis)
    mock_instance = MockOpenAI.return_value
    mock_chat = mock_instance.chat
    mock_completions = mock_chat.completions
    mock_create = mock_completions.create
    mock_create.return_value.choices = [type("obj", (), {"message": type("msg", (), {"content": None})()})]
    with pytest.raises(ValueError):
        client.get_completion("input", "prompt")

@patch("src.mantis.openai_client.OpenAI")
def test_openai_client_valid_response(MockOpenAI):
    mantis = DummyMantis()
    client = OpenAIClient(mantis)
    mock_instance = MockOpenAI.return_value
    mock_chat = mock_instance.chat
    mock_completions = mock_chat.completions
    mock_create = mock_completions.create
    mock_create.return_value.choices = [type("obj", (), {"message": type("msg", (), {"content": "Hello world!"})()})]
    result = client.get_completion("input", "prompt")
    assert result == "Hello world!"
