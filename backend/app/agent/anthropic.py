import os
import sys
import json
import asyncio
from typing import AsyncIterator, Dict

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Message
from app.agent.tools import mcp_server

LLM_TIMEOUT = float(os.environ.get("LLM_TIMEOUT_SECONDS", "30"))

try:
    from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient
    _SDK_AVAILABLE = True
except ImportError:
    _SDK_AVAILABLE = False

DB_URL = os.environ.get("DATABASE_URL", "postgresql://user:password@localhost:5432/dbname")
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

SYSTEM_PROMPT = (
    "You are the Lenny Growth Assistant. Answer questions ONLY using information from the retrieved "
    "transcript content via search_transcripts. Always cite the episode title and URL inline. "
    "If the provided transcripts do not contain the answer, state clearly: "
    "\"I'm sorry, the transcripts don't cover this topic. Please ask something related to Lenny's Podcast.\"\n"
    "Do not hallucinate."
)


class AnthropicAgentProvider:
    def __init__(self):
        self.clients: Dict[int, object] = {}

    def _get_or_create_client(self, session_id: int):
        if not _SDK_AVAILABLE:
            raise RuntimeError("claude_agent_sdk is not installed or unavailable.")
        if session_id in self.clients:
            return self.clients[session_id]

        options = ClaudeAgentOptions(
            mcp_server=mcp_server,
            allowed_tools=["search_transcripts", "write_ship30_essay", "render_artifact"],
            disallowed_tools=["read_file", "write_file", "run_shell_command", "fetch_url"],
            system_prompt=SYSTEM_PROMPT,
        )
        client = ClaudeSDKClient(options=options)

        db = SessionLocal()
        try:
            history = db.query(Message).filter(Message.session_id == session_id).order_by(Message.created_at.asc()).all()
            for msg in history:
                client.add_message_to_history(role=msg.role, content=msg.content)
        finally:
            db.close()

        self.clients[session_id] = client
        return client

    async def respond(self, session_id: int, user_message: str, history: list) -> AsyncIterator[str]:
        try:
            client = self._get_or_create_client(session_id)
            async with asyncio.timeout(LLM_TIMEOUT):
                async for token in client.stream_message(user_message):
                    yield token
        except TimeoutError:
            yield json.dumps({
                "error": True,
                "message": "Generation timed out, please retry.",
                "code": "timeout",
            })
        except RuntimeError as e:
            # SDK not installed or missing API key
            yield json.dumps({
                "error": True,
                "message": f"Anthropic service unavailable: {e}",
                "code": "provider_error",
            })
        except Exception as e:
            err_str = str(e)
            if "api_key" in err_str.lower() or "authentication" in err_str.lower():
                yield json.dumps({
                    "error": True,
                    "message": "Anthropic API key is missing or invalid.",
                    "code": "auth_error",
                })
            else:
                yield json.dumps({
                    "error": True,
                    "message": "Anthropic service is currently unavailable.",
                    "details": err_str,
                    "code": "provider_error",
                })
