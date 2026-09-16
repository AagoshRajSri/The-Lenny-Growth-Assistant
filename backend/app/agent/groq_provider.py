import os
import json
import asyncio
from typing import AsyncIterator

from app.agent.tools import search_transcripts_core
from groq import AsyncGroq
import groq

LLM_TIMEOUT = float(os.environ.get("LLM_TIMEOUT_SECONDS", "30"))
GROQ_MODEL = os.environ.get("GROQ_MODEL", "qwen/qwen3.8-27b")

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


class GroqProvider:
    def __init__(self):
        self.model = os.environ.get("GROQ_MODEL", GROQ_MODEL)
        self.api_key = os.environ.get("GROQ_API_KEY", "")
        self.client = AsyncGroq(api_key=self.api_key)

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
            async with asyncio.timeout(LLM_TIMEOUT):
                stream = await self.client.chat.completions.create(
                    messages=messages,
                    model=GROQ_MODEL,
                    temperature=0.0,
                    stream=True,
                )
                async for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content is not None:
                        yield chunk.choices[0].delta.content

        except asyncio.TimeoutError:
            yield json.dumps({
                "error": True,
                "message": "Generation timed out, please retry.",
                "code": "timeout",
            })
        except groq.AuthenticationError:
            yield json.dumps({
                "error": True,
                "message": "Groq API key is missing or invalid.",
                "code": "auth_error",
            })
        except groq.APIConnectionError:
            yield json.dumps({
                "error": True,
                "message": "Groq service is currently unreachable.",
                "code": "unreachable",
            })
        except Exception as e:
            yield json.dumps({
                "error": True,
                "message": "Groq service encountered an error.",
                "details": str(e),
                "code": "provider_error",
            })
