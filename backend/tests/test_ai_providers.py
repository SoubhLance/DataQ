import pytest
from unittest.mock import MagicMock, patch
from app.services.ai_provider import AIProvider
from app.services.groq_provider import GroqProvider
from app.services.gemini_provider import GeminiProvider
from app.services.mistral_provider import MistralProvider
from app.services.ai_service import AIService

class DummyProvider(AIProvider):
    def __init__(self, name: str, should_fail: bool = False, response: str = "") -> None:
        self.name = name
        self.should_fail = should_fail
        self.response = response

    def generate(self, prompt: str, system_instruction: str = None) -> str:
        if self.should_fail:
            raise RuntimeError(f"Provider {self.name} failed")
        return self.response

def test_ai_fallback_chain_success_primary():
    service = AIService()
    # Mock providers
    p1 = DummyProvider("Groq", should_fail=False, response="Groq working")
    p2 = DummyProvider("Gemini", should_fail=False, response="Gemini working")
    p3 = DummyProvider("Mistral", should_fail=False, response="Mistral working")
    service.providers = [p1, p2, p3]

    res = service.generate("Say only 'Groq working'")
    assert res == "Groq working"

def test_ai_fallback_chain_first_fails():
    service = AIService()
    # Mock providers: Groq fails, Gemini succeeds
    p1 = DummyProvider("Groq", should_fail=True)
    p2 = DummyProvider("Gemini", should_fail=False, response="Gemini working")
    p3 = DummyProvider("Mistral", should_fail=False, response="Mistral working")
    service.providers = [p1, p2, p3]

    res = service.generate("Say only 'Gemini working'")
    assert res == "Gemini working"

def test_ai_fallback_chain_first_two_fail():
    service = AIService()
    # Mock providers: Groq fails, Gemini fails, Mistral succeeds
    p1 = DummyProvider("Groq", should_fail=True)
    p2 = DummyProvider("Gemini", should_fail=True)
    p3 = DummyProvider("Mistral", should_fail=False, response="Mistral working")
    service.providers = [p1, p2, p3]

    res = service.generate("Say only 'Mistral working'")
    assert res == "Mistral working"

def test_ai_fallback_chain_all_fail():
    service = AIService()
    # Mock providers: all fail
    p1 = DummyProvider("Groq", should_fail=True)
    p2 = DummyProvider("Gemini", should_fail=True)
    p3 = DummyProvider("Mistral", should_fail=True)
    service.providers = [p1, p2, p3]

    with pytest.raises(RuntimeError) as excinfo:
        service.generate("Hello")
    assert "All AI providers in fallback chain failed" in str(excinfo.value)

@patch("app.services.groq_provider.Groq")
def test_groq_provider_generation(mock_groq_class):
    mock_client = MagicMock()
    mock_groq_class.return_value = mock_client
    mock_client.chat.completions.create.return_value.choices = [
        MagicMock(message=MagicMock(content="Groq working"))
    ]
    
    provider = GroqProvider(api_key="gsk_test")
    res = provider.generate("Say only 'Groq working'")
    assert res == "Groq working"
    mock_client.chat.completions.create.assert_called_once()

@patch("google.generativeai.GenerativeModel")
def test_gemini_provider_generation(mock_gen_model_class):
    mock_model = MagicMock()
    mock_gen_model_class.return_value = mock_model
    mock_model.generate_content.return_value = MagicMock(text="Gemini working")
    
    provider = GeminiProvider(api_key="AQ_test")
    res = provider.generate("Say only 'Gemini working'")
    assert res == "Gemini working"
    mock_model.generate_content.assert_called_once()

@patch("app.services.mistral_provider.Mistral")
def test_mistral_provider_generation(mock_mistral_class):
    mock_client = MagicMock()
    mock_mistral_class.return_value = mock_client
    mock_client.chat.complete.return_value.choices = [
        MagicMock(message=MagicMock(content="Mistral working"))
    ]
    
    provider = MistralProvider(api_key="mistral_test")
    res = provider.generate("Say only 'Mistral working'")
    assert res == "Mistral working"
    mock_client.chat.complete.assert_called_once()
