from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseAIProvider(ABC):
    def __init__(self, model_name: str):
        self.model_name = model_name

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Returns the canonical provider name."""
        pass

    @abstractmethod
    def complete(self, messages: List[Dict[str, str]], system_prompt: str, response_format_json: bool = True) -> Dict[str, Any]:
        """
        Sends messages to the LLM and returns the completion.
        Should return a dictionary containing at least:
        - "raw_content": str
        - "parsed_json": Optional[Dict[str, Any]] (if response_format_json is True)
        - "provider": str
        - "model": str
        - "success": bool
        - "error": Optional[str]
        """
        pass

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Returns health status, available model, and configuration."""
        pass
