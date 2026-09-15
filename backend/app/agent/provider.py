from typing import Protocol, AsyncIterator

class LLMProvider(Protocol):
    async def respond(self, session_id: int, user_message: str, history: list) -> AsyncIterator[str]:
        """
        Process a user message and return a streamed response.
        Surfaces citations or artifact IDs via inline response injection or structured payload.
        """
        ...
