from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, relationship, Mapped, mapped_column
from pgvector.sqlalchemy import Vector

Base = declarative_base()

class Session(Base):
    __tablename__ = 'sessions'
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    title: Mapped[Optional[str]] = mapped_column(String(255))
    model_provider: Mapped[Optional[str]] = mapped_column(String(100))

    messages: Mapped[List["Message"]] = relationship(back_populates="session")
    artifacts: Mapped[List["Artifact"]] = relationship(back_populates="session")

class Message(Base):
    __tablename__ = 'messages'
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(ForeignKey('sessions.id'))
    role: Mapped[str] = mapped_column(String(50))
    content: Mapped[str] = mapped_column(Text)
    citations: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    session: Mapped["Session"] = relationship(back_populates="messages")
    artifacts: Mapped[List["Artifact"]] = relationship(back_populates="message")

class Transcript(Base):
    __tablename__ = 'transcripts'
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    episode_title: Mapped[str] = mapped_column(String(500))
    episode_url: Mapped[Optional[str]] = mapped_column(String(500))
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    chunks: Mapped[List["Chunk"]] = relationship(back_populates="transcript")

class Chunk(Base):
    __tablename__ = 'chunks'
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    transcript_id: Mapped[int] = mapped_column(ForeignKey('transcripts.id'))
    content: Mapped[str] = mapped_column(Text)
    chunk_index: Mapped[int] = mapped_column(Integer)
    embedding: Mapped[Optional[list[float]]] = mapped_column(Vector(384))

    transcript: Mapped["Transcript"] = relationship(back_populates="chunks")

class Artifact(Base):
    __tablename__ = 'artifacts'
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(ForeignKey('sessions.id'))
    message_id: Mapped[int] = mapped_column(ForeignKey('messages.id'))
    type: Mapped[str] = mapped_column(String(50)) # markdown|html
    raw_content: Mapped[str] = mapped_column(Text)
    sanitized_content: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    session: Mapped["Session"] = relationship(back_populates="artifacts")
    message: Mapped["Message"] = relationship(back_populates="artifacts")
