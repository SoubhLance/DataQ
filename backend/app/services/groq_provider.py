import logging
from typing import Optional
from groq import Groq
from app.services.ai_provider import AIProvider

logger = logging.getLogger(__name__)

class GroqProvider(AIProvider):
    """
    Groq AI Provider implementation using Llama3 model.
    """
    def __init__(self, api_key: str):
        self.api_key = api_key
        # Lazy initialization
        self._client: Optional[Groq] = None

    @property
    def client(self) -> Groq:
        if self._client is None:
            self._client = Groq(api_key=self.api_key)
        return self._client

    def generate(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        try:
            completion = self.client.chat.completions.create(
                messages=messages,
                model="llama3-8b-8192",
                temperature=0.0
            )
            content = completion.choices[0].message.content
            return content.strip() if content else ""
        except Exception as e:
            logger.exception(f"Groq API call failed: {e}")
            raise e
