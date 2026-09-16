"""
Lenny Growth Assistant – FastAPI application entry point.

Routes:
  POST   /api/sessions                        – Create session
  GET    /api/sessions/{id}/messages          – Conversation history
  POST   /api/sessions/{id}/chat              – SSE token stream
  GET    /api/artifacts/{id}                  – Serve sanitized artifact
  GET    /api/config                          – Active provider settings
  GET    /healthz                             – Health check (DB + Ollama)
"""
import os
import json
import time
import logging
import asyncio

import httpx
from dotenv import load_dotenv

# Load root and local .env files
_root_env = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
if os.path.exists(_root_env):
    load_dotenv(_root_env)
load_dotenv()
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.schemas import (
    CreateSessionRequest, SessionResponse,
    ChatRequest, MessageResponse,
    ArtifactResponse, ConfigResponse, HealthStatus,
    ErrorDetail, ErrorResponse,
)
from app.logging_middleware import LoggingMiddleware, configure_logging
from app.database import SessionLocal
from app.db_retry import with_db_retry
from models import Session as DBSession, Message, Artifact
from app.agent.factory import get_provider

configure_logging()
logger = logging.getLogger("api")

# ─── App ────────────────────────────────────────────────────────────────────

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Lenny Growth Assistant API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url=None,
)

# Allow CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(LoggingMiddleware)


# ─── Global exception handler ───────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception", extra={"path": request.url.path})
    return JSONResponse(
        status_code=500,
        content={"error": {"code": 500, "message": "An unexpected error occurred."}},
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.status_code, "message": exc.detail}},
    )


# ─── Helper ─────────────────────────────────────────────────────────────────

def _get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ─── Routes ─────────────────────────────────────────────────────────────────

@app.get("/")
def read_root():
    return {"service": "Lenny Growth Assistant API", "status": "running"}


@app.get("/api/config", response_model=ConfigResponse)
def get_config():
    return ConfigResponse(
        llm_provider=os.environ.get("LLM_PROVIDER", "groq").lower(),
        ollama_model=os.environ.get("OLLAMA_MODEL", "llama3.2:3b"),
        ollama_base_url=os.environ.get("OLLAMA_BASE_URL", "http://host.docker.internal:11434"),
    )


@app.get("/healthz")
async def health_check():
    from fastapi import Depends
    import os as _os

    db_status = "connected"
    try:
        def _check_db():
            db = SessionLocal()
            try:
                db.execute(text("SELECT 1"))
            finally:
                db.close()
        with_db_retry(_check_db)
    except Exception:
        db_status = "unavailable"

    provider = _os.environ.get("LLM_PROVIDER", "groq").lower()
    ollama_base = _os.environ.get("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
    ollama_status = "not_configured"

    if provider == "ollama":
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(f"{ollama_base}/api/version")
                ollama_status = "reachable" if resp.status_code == 200 else "unreachable"
        except Exception:
            ollama_status = "unreachable"

    overall = "ok" if db_status == "connected" else "degraded"

    return HealthStatus(
        status=overall,
        db=db_status,
        llm_provider=provider,
        ollama_status=ollama_status,
    )


# ─── Sessions ───────────────────────────────────────────────────────────────

@app.post("/api/sessions", response_model=SessionResponse, status_code=201)
def create_session(body: CreateSessionRequest):
    def _do_create():
        db = SessionLocal()
        try:
            session = DBSession(
                title=body.title,
                model_provider=body.model_provider,
            )
            db.add(session)
            db.commit()
            db.refresh(session)
            logger.info("Session created", extra={"session_id": session.id})
            return SessionResponse(
                id=session.id,
                title=session.title,
                model_provider=session.model_provider,
                created_at=session.created_at,
            )
        finally:
            db.close()
    return with_db_retry(_do_create)


@app.get("/api/sessions", response_model=list[SessionResponse])
def get_sessions():
    def _do_get():
        db = SessionLocal()
        try:
            sessions = (
                db.query(DBSession)
                .order_by(DBSession.created_at.desc())
                .all()
            )
            return [
                SessionResponse(
                    id=s.id,
                    title=s.title,
                    model_provider=s.model_provider,
                    created_at=s.created_at,
                )
                for s in sessions
            ]
        finally:
            db.close()
    return with_db_retry(_do_get)


@app.get("/api/sessions/{session_id}/messages", response_model=list[MessageResponse])
def get_messages(session_id: int):
    def _do_get():
        db = SessionLocal()
        try:
            session = db.query(DBSession).filter(DBSession.id == session_id).first()
            if not session:
                raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

            messages = (
                db.query(Message)
                .filter(Message.session_id == session_id)
                .order_by(Message.created_at.asc())
                .all()
            )
            return [
                MessageResponse(
                    id=m.id,
                    session_id=m.session_id,
                    role=m.role,
                    content=m.content,
                    citations=m.citations,
                    created_at=m.created_at,
                )
                for m in messages
            ]
        finally:
            db.close()
    return with_db_retry(_do_get)


# ─── Chat (SSE) ─────────────────────────────────────────────────────────────

@app.post("/api/sessions/{session_id}/chat")
async def chat(session_id: int, body: ChatRequest, request: Request):
    # Validate session exists
    def _do_validate():
        db = SessionLocal()
        try:
            session = db.query(DBSession).filter(DBSession.id == session_id).first()
            if not session:
                raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

            history = (
                db.query(Message)
                .filter(Message.session_id == session_id)
                .order_by(Message.created_at.asc())
                .all()
            )
            return [{"role": m.role, "content": m.content} for m in history]
        finally:
            db.close()

    history_dicts = with_db_retry(_do_validate)

    user_message = body.message
    request_id = getattr(request.state, "request_id", "unknown")

    async def event_generator():
        provider = get_provider()
        full_response = []
        retrieval_hits = 0
        artifact_id = None
        citations = []
        start = time.perf_counter()

        try:
            async for token in provider.respond(session_id, user_message, history_dicts):
                # Detect structured error payload
                try:
                    data = json.loads(token)
                    if isinstance(data, dict) and data.get("error"):
                        yield {"event": "error", "data": token}
                        return
                except (json.JSONDecodeError, ValueError):
                    pass

                full_response.append(token)
                yield {"event": "token", "data": token}

            # Combine full answer
            answer = "".join(full_response)

            # Persist user message
            db2 = SessionLocal()
            try:
                user_msg = Message(
                    session_id=session_id,
                    role="user",
                    content=user_message,
                )
                db2.add(user_msg)
                db2.flush()

                assistant_msg = Message(
                    session_id=session_id,
                    role="assistant",
                    content=answer,
                    citations=citations if citations else None,
                )
                db2.add(assistant_msg)
                db2.commit()
            except Exception as db_err:
                logger.warning(f"Failed to persist messages: {db_err}", extra={"session_id": session_id})
            finally:
                db2.close()

            latency_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.info(
                "Chat complete",
                extra={
                    "request_id": request_id,
                    "session_id": session_id,
                    "provider": os.environ.get("LLM_PROVIDER", "groq"),
                    "latency_ms": latency_ms,
                    "retrieval_hits": retrieval_hits,
                },
            )

            # Final metadata event
            yield {
                "event": "done",
                "data": json.dumps({
                    "citations": citations,
                    "artifact_id": artifact_id,
                }),
            }

        except Exception as e:
            logger.exception("Error during chat stream", extra={"session_id": session_id})
            yield {
                "event": "error",
                "data": json.dumps({"error": {"code": 500, "message": str(e)}}),
            }

    return EventSourceResponse(event_generator())


# ─── Artifacts ──────────────────────────────────────────────────────────────

@app.get("/api/artifacts/{artifact_id}", response_model=ArtifactResponse)
def get_artifact(artifact_id: int):
    def _do_get():
        db = SessionLocal()
        try:
            artifact = db.query(Artifact).filter(Artifact.id == artifact_id).first()
            if not artifact:
                raise HTTPException(status_code=404, detail=f"Artifact {artifact_id} not found")

            return ArtifactResponse(
                id=artifact.id,
                type=artifact.type,
                sanitized_content=artifact.sanitized_content,
                created_at=artifact.created_at,
            )
        finally:
            db.close()
    return with_db_retry(_do_get)
