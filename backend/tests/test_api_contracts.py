"""
test_api_contracts.py
Tests all routes for correct HTTP status codes, response shapes,
and structured error envelopes.
Uses FastAPI TestClient with a fully mocked DB so no live DB is required.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/testdb")
    from main import app
    return TestClient(app, raise_server_exceptions=False)


# ─── /healthz ────────────────────────────────────────────────────────────────

def test_healthz_returns_200_with_db_down(client):
    """Health endpoint must never return 500 even if DB is down."""
    with patch("main.SessionLocal") as mock_sl:
        mock_db = MagicMock()
        mock_db.execute.side_effect = Exception("DB offline")
        mock_sl.return_value = mock_db
        resp = client.get("/healthz")
    assert resp.status_code == 200
    body = resp.json()
    assert "status" in body
    assert body["db"] == "unavailable"


def test_healthz_reports_ollama_status(client):
    """healthz reports ollama_status when provider=ollama."""
    resp = client.get("/healthz")
    assert resp.status_code == 200
    body = resp.json()
    assert "ollama_status" in body


# ─── /api/config ─────────────────────────────────────────────────────────────

def test_config_returns_provider(client):
    resp = client.get("/api/config")
    assert resp.status_code == 200
    body = resp.json()
    assert body["llm_provider"] == "groq"
    assert "ollama_model" in body
    assert "ollama_base_url" in body


# ─── /api/sessions ───────────────────────────────────────────────────────────

def test_create_session_success(client):
    """Should return 201 with properly structured JSON."""
    with patch("main.SessionLocal") as mock_sl:
        import datetime
        mock_session_obj = MagicMock()
        mock_session_obj.id = 42
        mock_session_obj.title = "Strategy 2026"
        mock_session_obj.model_provider = "groq"
        mock_session_obj.created_at = datetime.datetime(2026, 1, 1, 0, 0, 0)

        mock_db = MagicMock()
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = lambda s: None
        mock_sl.return_value = mock_db
        
        with patch("main.DBSession", return_value=mock_session_obj):
            resp = client.post("/api/sessions", json={
                "title": "Strategy 2026",
                "model_provider": "groq"
            })
            
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Strategy 2026"
    assert data["model_provider"] == "groq"


def test_create_session_missing_body(client):
    """Empty body should be accepted and return 201."""
    with patch("main.SessionLocal") as mock_sl:
        import datetime
        mock_session_obj = MagicMock()
        mock_session_obj.id = 42
        mock_session_obj.title = None
        mock_session_obj.model_provider = "groq"
        
        mock_db = MagicMock()
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = lambda s: None
        mock_sl.return_value = mock_db
        
        with patch("main.DBSession", return_value=mock_session_obj):
            resp = client.post("/api/sessions", json={})
            
    assert resp.status_code == 201


# ─── /api/sessions/{id}/messages ─────────────────────────────────────────────

def test_get_messages_not_found(client):
    with patch("main.SessionLocal") as mock_sl:
        mock_db = MagicMock()
        from models import Session as DBSession, Message
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_sl.return_value = mock_db
        resp = client.get("/api/sessions/9999/messages")
    assert resp.status_code == 404
    body = resp.json()
    assert "error" in body
    assert body["error"]["code"] == 404


def test_get_messages_bad_id_type(client):
    resp = client.get("/api/sessions/not-a-number/messages")
    assert resp.status_code == 422


# ─── /api/artifacts/{id} ─────────────────────────────────────────────────────

def test_get_artifact_not_found(client):
    with patch("main.SessionLocal") as mock_sl:
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_sl.return_value = mock_db
        resp = client.get("/api/artifacts/9999")
    assert resp.status_code == 404
    body = resp.json()
    assert "error" in body
    assert body["error"]["code"] == 404


def test_get_artifact_success(client):
    import datetime
    with patch("main.SessionLocal") as mock_sl:
        mock_artifact = MagicMock()
        mock_artifact.id = 1
        mock_artifact.type = "html"
        mock_artifact.sanitized_content = "<p>Hello</p>"
        mock_artifact.created_at = datetime.datetime(2026, 1, 1)

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_artifact
        mock_sl.return_value = mock_db
        resp = client.get("/api/artifacts/1")
    assert resp.status_code == 200
    body = resp.json()
    assert body["sanitized_content"] == "<p>Hello</p>"
    assert "raw_content" not in body  # raw MUST NOT be served


# ─── Global error handler ─────────────────────────────────────────────────────

def test_error_envelope_shape_on_404(client):
    """All 4xx responses must use the {"error": {"code": N, "message": ...}} envelope."""
    with patch("main.SessionLocal") as mock_sl:
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_sl.return_value = mock_db
        resp = client.get("/api/artifacts/0")
    body = resp.json()
    assert isinstance(body.get("error"), dict)
    assert "code" in body["error"]
    assert "message" in body["error"]
