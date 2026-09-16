import os
from app.agent.provider import LLMProvider

def get_provider() -> LLMProvider:
    provider_name = os.environ.get("LLM_PROVIDER", "groq").lower()

    if provider_name == "ollama":
        from app.agent.ollama import OllamaProvider
        return OllamaProvider()
    else:
        # Default to Groq
        from app.agent.groq_provider import GroqProvider
        return GroqProvider()
