import logging
from typing import Optional
from mistralai.client.sdk import Mistral
from app.services.ai_provider import AIProvider

logger = logging.getLogger(__name__)

class MistralProvider(AIProvider):
    """
    Mistral AI Provider implementation.
    """
    def __init__(self, api_key: str):
        self.api_key = api_key
        self._client: Optional[Mistral] = None

    @property
    def client(self) -> Mistral:
        if self._client is None:
            self._client = Mistral(api_key=self.api_key)
        return self._client

    def generate(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self.client.chat.complete(
                model="mistral-large-latest",
                messages=messages,
                temperature=0.0
            )
            content = response.choices[0].message.content
            # Handle potential union/type wrapper if any, though standard is string
            if not isinstance(content, str):
                content = str(content)
            return content.strip() if content else ""
        except Exception as e:
            logger.exception(f"Mistral API call failed: {e}")
            raise e
