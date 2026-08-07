"""SQLAlchemy ORM models for persistent database storage."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Float
from sqlalchemy.dialects.postgresql import UUID, ARRAY
import uuid

from .database import Base


class Conversation(Base):
    """Stores multi-turn chat conversations."""

    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True)
    session_id = Column(UUID(as_uuid=True), default=uuid.uuid4, nullable=False, index=True)
    messages = Column(JSON, nullable=False, default=list)
    model_id = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata_json = Column(JSON, nullable=True)

    def __repr__(self) -> str:
        return f"<Conversation(session_id={self.session_id}, messages={len(self.messages)})>"


class Document(Base):
    """Stores documents and their embeddings for RAG."""

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True)
    filename = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=False, index=True)
    chunks = Column(JSON, nullable=False, default=list)
    embeddings = Column(JSON, nullable=False, default=list)
    chunk_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    metadata_json = Column(JSON, nullable=True)

    def __repr__(self) -> str:
        return f"<Document(filename={self.filename}, chunks={self.chunk_count})>"


class DocumentEmbedding(Base):
    """Stores individual chunk embeddings for efficient search."""

    __tablename__ = "document_embeddings"

    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    embedding = Column(ARRAY(Float), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<DocumentEmbedding(doc_id={self.document_id}, chunk={self.chunk_index})>"


class Resume(Base):
    """Stores parsed resume data."""

    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True)
    filename = Column(String(255), nullable=False)
    raw_text = Column(Text, nullable=False)
    parsed_data = Column(JSON, nullable=False)
    full_name = Column(String(255), nullable=True, index=True)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(20), nullable=True)
    skills = Column(ARRAY(String), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    metadata_json = Column(JSON, nullable=True)

    def __repr__(self) -> str:
        return f"<Resume(name={self.full_name}, email={self.email})>"


class Question(Base):
    """Stores Q&A history for audit trail."""

    __tablename__ = "questions"

    id = Column(Integer, primary_key=True)
    session_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    document_id = Column(Integer, nullable=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    used_rag = Column(Integer, default=0)
    model_id = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    metadata_json = Column(JSON, nullable=True)

    def __repr__(self) -> str:
        return f"<Question(session={self.session_id}, rag={bool(self.used_rag)})>"
