import pytest
from unittest.mock import MagicMock

from ai.gemini import Gemini


class FakeResponse:
    def __init__(self, text):
        self.text = text

@pytest.fixture
def mock_genai_client(mocker):
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = FakeResponse("mocked response")
    mocker.patch("ai.gemini.genai.Client", return_value=mock_client)
    return mock_client

@pytest.mark.asyncio
async def test_chat_with_system_prompt(mock_genai_client):
    gemini = Gemini(
        api_key="fake-key",
        system_prompt="SYSTEM PROMPT"
    )
    response = await gemini.chat("Hello")
    assert response == "mocked response"

    mock_genai_client.models.generate_content.assert_called_once()
    call_args = mock_genai_client.models.generate_content.call_args[1]
    assert "SYSTEM PROMPT" in call_args["contents"]
    assert "Hello" in call_args["contents"]

@pytest.mark.asyncio
async def test_summarize_without_prompt_raises():
    gemini = Gemini(api_key="fake-key")

    with pytest.raises(ValueError):
        await gemini.summarize("Some text")

@pytest.mark.asyncio
async def test_translate_without_prompt_raises():
    gemini = Gemini(api_key="fake-key")
    with pytest.raises(ValueError):
        await gemini.translate("Hello", "tr")

@pytest.mark.asyncio
async def test_detect_language_normalizes_output(mock_genai_client):
    mock_genai_client.models.generate_content.return_value = FakeResponse(" EN ")
    gemini = Gemini(api_key="fake-key")
    lang = await gemini.detect_language("Hello world")
    assert lang == "en"