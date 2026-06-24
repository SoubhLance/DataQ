from abc import ABC, abstractmethod
from typing import Optional

class AIProvider(ABC):
    """
    Abstract Base Class representing an AI Provider.
    """
    @abstractmethod
    def generate(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        """
        Generate chat completion response from the AI provider.
        """
        pass
