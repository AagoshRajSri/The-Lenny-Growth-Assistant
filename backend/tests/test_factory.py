"""
test_factory.py
Verifies ProviderFactory resolves providers correctly from LLM_PROVIDER env var.
No database or network required.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest


def test_factory_returns_ollama(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    import importlib
    import app.agent.factory as fmod
    importlib.reload(fmod)
    provider = fmod.get_provider()
    from app.agent.ollama import OllamaProvider
    assert isinstance(provider, OllamaProvider)


def test_factory_returns_groq_by_default(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    import importlib
    import app.agent.factory as fmod
    importlib.reload(fmod)
    provider = fmod.get_provider()
    from app.agent.groq_provider import GroqProvider
    assert isinstance(provider, GroqProvider)


def test_factory_fallback_to_groq_on_empty(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    import importlib
    import app.agent.factory as fmod
    importlib.reload(fmod)
    provider = fmod.get_provider()
    from app.agent.groq_provider import GroqProvider
    assert isinstance(provider, GroqProvider)


def test_factory_case_insensitive(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "OLLAMA")
    import importlib
    import app.agent.factory as fmod
    importlib.reload(fmod)
    # factory.get_provider() lowercases the env var
    provider = fmod.get_provider()
    from app.agent.ollama import OllamaProvider
    assert isinstance(provider, OllamaProvider)
