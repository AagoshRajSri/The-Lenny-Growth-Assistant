"""
test_retrieval.py
Tests search_transcripts_core logic using mocked DB and embedding.
No live database or GPU required.
"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from unittest.mock import patch, MagicMock
sys.modules["claude_agent_sdk"] = MagicMock()

# Import app.agent.tools early to ensure it's registered in sys.modules
import app.agent.tools

def _make_chunk(content: str, transcript_id: int) -> MagicMock:
    chunk = MagicMock()
    chunk.content = content
    chunk.transcript_id = transcript_id
    return chunk


def _make_transcript(title: str, url: str) -> MagicMock:
    t = MagicMock()
    t.episode_title = title
    t.episode_url = url
    return t


@patch("app.agent.tools.SessionLocal")
@patch("app.agent.tools.SentenceTransformer")
def test_returns_ranked_chunks(MockST, MockSessionLocal):
    """search_transcripts_core returns chunk text with episode metadata."""
    # Mock encoder
    mock_model = MagicMock()
    mock_model.encode.return_value.tolist.return_value = [0.1, 0.2, 0.3]
    MockST.return_value = mock_model

    # Mock DB session
    mock_db = MagicMock()
    MockSessionLocal.return_value = mock_db

    chunks = [_make_chunk("Product market fit is key.", 1)]
    transcript = _make_transcript("Ep 1: PMF", "https://lenny.com/ep1")

    mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = chunks
    mock_db.query.return_value.filter.return_value.first.return_value = transcript

    from app.agent.tools import search_transcripts_core
    result = search_transcripts_core("product market fit", k=1)
    parsed = json.loads(result)

    assert len(parsed) == 1
    assert parsed[0]["episode_title"] == "Ep 1: PMF"
    assert parsed[0]["url"] == "https://lenny.com/ep1"
    assert "Product market fit" in parsed[0]["content"]


@patch("app.agent.tools.SessionLocal")
@patch("app.agent.tools.SentenceTransformer")
def test_empty_results(MockST, MockSessionLocal):
    """Returns empty JSON array when no chunks match."""
    mock_model = MagicMock()
    mock_model.encode.return_value.tolist.return_value = [0.0] * 384
    MockST.return_value = mock_model

    mock_db = MagicMock()
    MockSessionLocal.return_value = mock_db
    mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = []

    from app.agent.tools import search_transcripts_core
    result = search_transcripts_core("baking a cake", k=5)
    parsed = json.loads(result)
    assert parsed == []


@patch("app.agent.tools.SessionLocal")
@patch("app.agent.tools.SentenceTransformer")
def test_missing_transcript_skipped(MockST, MockSessionLocal):
    """Chunks with no matching transcript row are silently skipped."""
    mock_model = MagicMock()
    mock_model.encode.return_value.tolist.return_value = [0.1]
    MockST.return_value = mock_model

    mock_db = MagicMock()
    MockSessionLocal.return_value = mock_db

    orphan_chunk = _make_chunk("orphaned content", 999)
    mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = [orphan_chunk]
    # transcript lookup returns None
    mock_db.query.return_value.filter.return_value.first.return_value = None

    from app.agent.tools import search_transcripts_core
    result = search_transcripts_core("anything", k=1)
    parsed = json.loads(result)
    assert parsed == []
