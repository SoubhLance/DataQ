import logging
from typing import Optional
import google.generativeai as genai
from app.services.ai_provider import AIProvider

logger = logging.getLogger(__name__)

class GeminiProvider(AIProvider):
    """
    Gemini AI Provider implementation.
    """
    def __init__(self, api_key: str):
        self.api_key = api_key
        # Configure once
        genai.configure(api_key=self.api_key)

    def generate(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        try:
            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                system_instruction=system_instruction
            )
            response = model.generate_content(prompt)
            content = response.text
            return content.strip() if content else ""
        except Exception as e:
            logger.exception(f"Gemini API call failed: {e}")
            raise e
