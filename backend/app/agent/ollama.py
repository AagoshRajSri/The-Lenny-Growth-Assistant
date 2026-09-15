import os
import json
import asyncio
import httpx
from typing import AsyncIterator

from app.agent.tools import search_transcripts_core

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:3b")
LLM_TIMEOUT = float(os.environ.get("LLM_TIMEOUT_SECONDS", "30"))

OUT_OF_CORPUS_SYSTEM = (
    "You are the Lenny Growth Assistant.\n"
    "The knowledge-base search returned NO relevant transcript chunks for this query.\n"
    "You MUST respond with exactly this message and no other content:\n"
    "\"I'm sorry, the transcripts don't cover this topic. "
    "Please ask something related to Lenny's Podcast or Newsletter.\"\n"
    "Do not attempt to answer from general knowledge."
)


def _build_system_prompt(context_json: str) -> str:
    try:
        chunks = json.loads(context_json)
    except Exception:
        chunks = []

    if not chunks:
        return OUT_OF_CORPUS_SYSTEM

    return (
        "You are the Lenny Growth Assistant. Answer questions ONLY using information from the retrieved "
        "transcript content below. Always cite the episode title and URL inline. "
        "If the provided transcripts do not contain the answer, state clearly: "
        "\"I'm sorry, the transcripts don't cover this topic.\"\n\n"
        f"RETRIEVED CONTEXT:\n{context_json}"
    )


class OllamaProvider:
    async def respond(self, session_id: int, user_message: str, history: list) -> AsyncIterator[str]:
        # Pre-retrieval
        try:
            context = search_transcripts_core(user_message, k=5)
        except Exception as e:
            context = "[]"

        system_prompt = _build_system_prompt(context)

        messages = [{"role": "system", "content": system_prompt}]
        for msg in history:
            messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
        messages.append({"role": "user", "content": user_message})

        try:
            async with httpx.AsyncClient() as client:
                async with asyncio.timeout(LLM_TIMEOUT):
                    response = await client.post(
                        f"{OLLAMA_BASE_URL}/api/chat",
                        json={"model": OLLAMA_MODEL, "messages": messages, "stream": True},
                        timeout=httpx.Timeout(LLM_TIMEOUT, connect=5.0),
                    )
                    response.raise_for_status()

                    async for line in response.aiter_lines():
                        if line:
                            try:
                                data = json.loads(line)
                                if "message" in data and "content" in data["message"]:
                                    yield data["message"]["content"]
                            except json.JSONDecodeError:
                                pass

        except TimeoutError:
            yield json.dumps({
                "error": True,
                "message": "Generation timed out, please retry.",
                "code": "timeout",
            })
        except httpx.ConnectError:
            yield json.dumps({
                "error": True,
                "message": "Ollama service is currently unreachable.",
                "code": "unreachable",
            })
        except Exception as e:
            yield json.dumps({
                "error": True,
                "message": "Ollama service is currently unreachable.",
                "details": str(e),
                "code": "provider_error",
            })
