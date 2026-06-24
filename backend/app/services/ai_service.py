import logging
from typing import Optional, List
from app.config.settings import settings
from app.services.ai_provider import AIProvider
from app.services.groq_provider import GroqProvider
from app.services.gemini_provider import GeminiProvider
from app.services.mistral_provider import MistralProvider

logger = logging.getLogger(__name__)

class AIService:
    """
    AI Service Layer coordinating Llama/Groq, Gemini, and Mistral providers.
    Implements a sequential fallback chain.
    """
    def __init__(self):
        self.providers: List[AIProvider] = [
            GroqProvider(settings.GROQ_API_KEY),
            GeminiProvider(settings.GEMINI_API_KEY),
            MistralProvider(settings.MISTRAL_API_KEY)
        ]

    def generate(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        """
        Generate completion using sequential fallback: Groq -> Gemini -> Mistral.
        Raises RuntimeError if all providers fail.
        """
        errors = []
        for provider in self.providers:
            provider_name = provider.__class__.__name__
            try:
                logger.info(f"Attempting generation with {provider_name}...")
                response = provider.generate(prompt, system_instruction)
                logger.info(f"Generation successful using {provider_name}.")
                return response
            except Exception as e:
                logger.warning(f"{provider_name} failed: {e}")
                errors.append(f"{provider_name}: {e}")

        # All providers failed
        error_msg = f"All AI providers in fallback chain failed. Details: {', '.join(errors)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

# Singleton Instance
ai_service = AIService()
