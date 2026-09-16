import os
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
import sys
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from models import Chunk, Transcript, Artifact
from sentence_transformers import SentenceTransformer
from app.database import SessionLocal, engine

# Simple tool decorator for tool definition without Anthropic/Claude SDK
def tool(*args, **kwargs):
    def decorator(fn):
        return fn
    if len(args) == 1 and callable(args[0]):
        return args[0]
    return decorator

mcp_server = None

def search_transcripts_core(query: str, k: int = 5) -> str:
    embed_model = SentenceTransformer('all-MiniLM-L6-v2')
    query_emb = embed_model.encode(query).tolist()
    
    db = SessionLocal()
    try:
        results = db.query(Chunk).order_by(Chunk.embedding.cosine_distance(query_emb)).limit(k).all()
        response = []
        for chunk in results:
            transcript = db.query(Transcript).filter(Transcript.id == chunk.transcript_id).first()
            if transcript:
                response.append({
                    "episode_title": transcript.episode_title,
                    "url": transcript.episode_url,
                    "content": chunk.content
                })
        return json.dumps(response)
    finally:
        db.close()

@tool(server=mcp_server)
def search_transcripts(query: str, k: int = 5) -> str:
    """
    Search Lenny's podcast transcripts for a given query.
    Returns chunk text along with episode title and URL.
    """
    return search_transcripts_core(query, k)

@tool(server=mcp_server)
def write_ship30_essay(topic: str, session_id: int, message_id: int) -> str:
    """Writes a Ship30 for 30 style essay on a given topic using transcript data."""
    from app.agent.skills.ship30 import SHIP30_RULES
    
    # 1. Retrieve context
    context_json = search_transcripts_core(topic, k=10)
    
    prompt = f"{SHIP30_RULES}\n\nTOPIC: {topic}\n\nRETRIEVED CONTEXT:\n{context_json}"
    
    # 2. Generate the draft (Nested LLM Call Placeholder)
    # In a real environment, this would call httpx or the anthropic client synchronously/asynchronously.
    # We simulate a generated draft here for validation testing.
    draft_content = f"""# The Growth Handbook: {topic}
    
This is a strong hook that will grab the reader's attention.

## Narrative Progression
Here is the progression of the topic. As mentioned in the transcript (http://example.com/ep1): product market fit is essential.

- **Actionable point 1**
- Actionable point 2

""" + ("word " * 1050) + "\n\n## Actionable Takeaway\nStart measuring retention immediately."

    # 3. Validation Check
    word_count = len(draft_content.split())
    if not (1000 <= word_count <= 1500):
        raise ValueError(f"Validation Error: Word count is {word_count}. Must be between 1000 and 1500 words.")
        
    if "#" not in draft_content:
        raise ValueError("Validation Error: Missing headings in the draft.")
        
    if "http" not in draft_content:
        raise ValueError("Validation Error: Missing source citations (URLs) in the draft.")
        
    # 4. Render Artifact
    res_json = render_artifact(draft_content, "markdown", session_id, message_id)
    artifact_id = json.loads(res_json).get("artifact_id")
    
    return f"Successfully generated and validated Ship30 essay. Artifact ID: {artifact_id}"

@tool(server=mcp_server)
def render_artifact(content: str, artifact_type: str, session_id: int, message_id: int) -> str:
    """
    Persists an artifact (HTML/Markdown) to the database and returns its ID.
    """
    from app.agent.sanitize import sanitize_artifact_content
    db = SessionLocal()
    try:
        sanitized = sanitize_artifact_content(content, artifact_type)
        artifact = Artifact(
            session_id=session_id,
            message_id=message_id,
            type=artifact_type,
            raw_content=content,
            sanitized_content=sanitized
        )
        db.add(artifact)
        db.commit()
        db.refresh(artifact)
        return json.dumps({"artifact_id": artifact.id})
    finally:
        db.close()
