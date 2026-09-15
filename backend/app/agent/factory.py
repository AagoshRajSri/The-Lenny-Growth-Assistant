import os
from app.agent.provider import LLMProvider

def get_provider() -> LLMProvider:
    provider_name = os.environ.get("LLM_PROVIDER", "anthropic").lower()
    
    if provider_name == "ollama":
        from app.agent.ollama import OllamaProvider
        return OllamaProvider()
    else:
        from app.agent.anthropic import AnthropicAgentProvider
        return AnthropicAgentProvider()
