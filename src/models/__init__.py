"""
SQLAlchemy database models for PostgreSQL

Defines all tables and relationships for the research agent database.
"""

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, ForeignKey,
    JSON, Float, Index, UniqueConstraint, CheckConstraint, LargeBinary,
    ForeignKeyConstraint, Table
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional
import uuid

Base = declarative_base()


class User(Base):
    """User account model"""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    is_verified = Column(Boolean, default=False)
    role = Column(String(50), default="user", index=True)  # user, admin, researcher
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    research_sessions = relationship("ResearchSession", back_populates="user")
    reports = relationship("Report", back_populates="user")
    documents = relationship("Document", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")
    
    __table_args__ = (
        Index("idx_user_email", "email"),
        Index("idx_user_active", "is_active"),
    )


class ResearchSession(Base):
    """Research session model"""
    
    __tablename__ = "research_sessions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(500), nullable=True)
    query = Column(Text, nullable=False)
    research_plan = Column(JSON, nullable=True)  # Planner agent output
    status = Column(
        String(50),
        default="planning",
        index=True,
        # Statuses: planning, researching, generating, fact_checking, reviewing, completed, failed, cancelled
    )
    depth = Column(String(50), default="moderate")  # shallow, moderate, deep
    web_results = Column(JSON, nullable=True)
    academic_results = Column(JSON, nullable=True)
    document_results = Column(JSON, nullable=True)
    retrieval_results = Column(JSON, nullable=True)
    verification_report = Column(JSON, nullable=True)
    report_id = Column(String(36), ForeignKey("reports.id"), nullable=True)
    progress_percentage = Column(Integer, default=0)
    current_step = Column(String(255), nullable=True)
    error_message = Column(Text, nullable=True)
    knowledge_graph_id = Column(String(36), nullable=True)  # Neo4j graph ID
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    estimated_completion_time = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="research_sessions")
    report = relationship("Report", back_populates="session")
    sources = relationship("Source", back_populates="session", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_session_user_created", "user_id", "created_at"),
        Index("idx_session_status", "status"),
    )


class Report(Base):
    """Research report model"""
    
    __tablename__ = "reports"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("research_sessions.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    content_markdown = Column(Text, nullable=False)
    content_json = Column(JSON, nullable=True)  # Structured sections
    word_count = Column(Integer, default=0)
    citation_count = Column(Integer, default=0)
    completeness_score = Column(Float, default=0.0)  # 0.0 - 1.0
    consistency_score = Column(Float, default=0.0)  # 0.0 - 1.0
    readability_score = Column(Float, default=0.0)  # 0.0 - 1.0
    status = Column(String(50), default="draft")  # draft, published, archived
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    published_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="reports")
    session = relationship("ResearchSession", back_populates="report")
    citations = relationship("Citation", back_populates="report", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_report_user_created", "user_id", "created_at"),
        Index("idx_report_status", "status"),
    )


class Source(Base):
    """Research source/reference model"""
    
    __tablename__ = "sources"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("research_sessions.id"), nullable=False, index=True)
    source_type = Column(String(50), nullable=False)  # web, academic, document, internal
    title = Column(String(500), nullable=False)
    url = Column(String(2000), nullable=True)
    authors = Column(JSON, nullable=True)  # List of author names
    published_date = Column(DateTime, nullable=True)
    accessed_date = Column(DateTime, default=datetime.utcnow)
    content = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    relevance_score = Column(Float, default=0.0)  # 0.0 - 1.0
    source_reliability = Column(Float, default=0.5)  # 0.0 - 1.0
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("ResearchSession", back_populates="sources")
    citations = relationship("Citation", back_populates="source")
    
    __table_args__ = (
        Index("idx_source_session_type", "session_id", "source_type"),
    )


class Citation(Base):
    """Citation/reference model"""
    
    __tablename__ = "citations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id = Column(String(36), ForeignKey("reports.id"), nullable=False, index=True)
    source_id = Column(String(36), ForeignKey("sources.id"), nullable=False, index=True)
    claim_text = Column(Text, nullable=False)
    citation_text = Column(Text, nullable=False)  # Full citation
    citation_style = Column(String(50), default="apa")  # apa, mla, chicago, harvard, ieee
    confidence_score = Column(Float, default=0.0)  # 0.0 - 1.0
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    report = relationship("Report", back_populates="citations")
    source = relationship("Source", back_populates="citations")
    
    __table_args__ = (
        Index("idx_citation_report", "report_id"),
    )


class Document(Base):
    """Uploaded document model"""
    
    __tablename__ = "documents"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    filename = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)  # pdf, txt, markdown
    file_size = Column(Integer)  # Bytes
    content = Column(LargeBinary, nullable=True)
    text_content = Column(Text, nullable=True)
    metadata = Column(JSON, nullable=True)
    processing_status = Column(String(50), default="pending")  # pending, processing, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    processed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_document_user_created", "user_id", "created_at"),
    )


class DocumentChunk(Base):
    """Document chunk model (for RAG)"""
    
    __tablename__ = "document_chunks"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding_id = Column(String(255), nullable=True)  # Reference to ChromaDB embedding
    token_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    document = relationship("Document", back_populates="chunks")
    
    __table_args__ = (
        Index("idx_chunk_document", "document_id"),
        UniqueConstraint("document_id", "chunk_index", name="uq_chunk_index"),
    )


class Search(Base):
    """Search query history model"""
    
    __tablename__ = "searches"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("research_sessions.id"), nullable=False)
    search_type = Column(String(50), nullable=False)  # web, academic, document, entity
    query = Column(Text, nullable=False)
    results_count = Column(Integer, default=0)
    execution_time_ms = Column(Integer)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_search_session_type", "session_id", "search_type"),
    )


class AuditLog(Base):
    """Audit logging model"""
    
    __tablename__ = "audit_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)  # login, create_research, delete_report
    resource_type = Column(String(100), nullable=False)  # User, Research, Report
    resource_id = Column(String(36), nullable=True, index=True)
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(String(500), nullable=True)
    status = Column(String(50), default="success")  # success, failure
    error_message = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    __table_args__ = (
        Index("idx_audit_user_timestamp", "user_id", "timestamp"),
        Index("idx_audit_action_timestamp", "action", "timestamp"),
    )


class TokenBlacklist(Base):
    """Blacklisted tokens model (for logout)"""
    
    __tablename__ = "token_blacklist"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    token = Column(String(500), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    blacklisted_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False, index=True)
    
    __table_args__ = (
        Index("idx_token_expires", "expires_at"),
    )
