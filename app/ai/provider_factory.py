from typing import Optional
from app.config import Config
from app.ai.base_provider import BaseAIProvider
from app.ai.gemini_provider import GeminiProvider
from app.ai.groq_provider import GroqProvider
from app.ai.openrouter_provider import OpenRouterProvider
from app.ai.ollama_provider import OllamaProvider
from app.ai.local_fallback_provider import LocalFallbackProvider

class ProviderFactory:
    _instance: Optional[BaseAIProvider] = None

    @classmethod
    def get_provider(cls, force_provider: Optional[str] = None) -> BaseAIProvider:
        provider_type = (force_provider or Config.AI_PROVIDER).lower()

        if provider_type == "gemini":
            if Config.GEMINI_API_KEY:
                return GeminiProvider(api_key=Config.GEMINI_API_KEY, model_name=Config.GEMINI_MODEL)
            return LocalFallbackProvider()

        elif provider_type == "groq":
            if Config.GROQ_API_KEY:
                return GroqProvider(api_key=Config.GROQ_API_KEY, model_name=Config.GROQ_MODEL)
            return LocalFallbackProvider()

        elif provider_type == "openrouter":
            if Config.OPENROUTER_API_KEY:
                return OpenRouterProvider(api_key=Config.OPENROUTER_API_KEY, model_name=Config.OPENROUTER_MODEL)
            return LocalFallbackProvider()

        elif provider_type == "ollama":
            return OllamaProvider(base_url=Config.OLLAMA_BASE_URL, model_name=Config.OLLAMA_MODEL)

        elif provider_type == "auto":
            # Smart auto-detection order
            if Config.GEMINI_API_KEY:
                return GeminiProvider(api_key=Config.GEMINI_API_KEY, model_name=Config.GEMINI_MODEL)
            elif Config.GROQ_API_KEY:
                return GroqProvider(api_key=Config.GROQ_API_KEY, model_name=Config.GROQ_MODEL)
            elif Config.OPENROUTER_API_KEY:
                return OpenRouterProvider(api_key=Config.OPENROUTER_API_KEY, model_name=Config.OPENROUTER_MODEL)
            else:
                return LocalFallbackProvider()

        # Default fallback
        return LocalFallbackProvider()
