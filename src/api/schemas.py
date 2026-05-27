"""
REST API layer for the Deep Research Agent.
"""

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum

from src.core.types import (
    ResearchDepth,
    SourceType,
    ReportFormat,
    CitationStyle,
)


# Request Models
class ResearchRequest(BaseModel):
    """Request for starting a research session."""
    query: str = Field(..., description="Research query")
    depth: ResearchDepth = Field(default=ResearchDepth.MODERATE, description="Research depth")
    source_types: Optional[List[SourceType]] = Field(default=None, description="Source types to use")
    max_results: Optional[int] = Field(default=None, description="Maximum results")
    include_citations: bool = Field(default=True, description="Include citations")
    citation_style: CitationStyle = Field(default=CitationStyle.APA, description="Citation style")


class DocumentUploadRequest(BaseModel):
    """Request for uploading documents."""
    title: str
    description: Optional[str] = None


# Response Models
class SourceResponse(BaseModel):
    """Source response."""
    url: str
    title: str
    source_type: str
    author: Optional[str] = None
    publication_date: Optional[datetime] = None
    confidence: float


class CitationResponse(BaseModel):
    """Citation response."""
    formatted_text: str
    style: str
    source: SourceResponse


class DocumentChunkResponse(BaseModel):
    """Document chunk response."""
    chunk_id: str
    document_id: str
    content: str
    source: SourceResponse


class RetrievalResultResponse(BaseModel):
    """Retrieval result response."""
    chunk: DocumentChunkResponse
    similarity_score: float
    rank: int
    retrieval_method: str


class ResearchPlanResponse(BaseModel):
    """Research plan response."""
    main_query: str
    subtopics: List[str]
    search_queries: List[str]
    research_depth: str
    estimated_sources: int
    timeline_minutes: int


class ResearchSessionResponse(BaseModel):
    """Research session response."""
    session_id: str
    status: str
    query: str
    research_depth: str
    created_at: datetime
    progress: float = Field(default=0.0, ge=0.0, le=1.0)


class ResearchReportResponse(BaseModel):
    """Research report response."""
    report_id: str
    session_id: str
    title: str
    content: str
    format: str = "markdown"
    citations: List[CitationResponse]
    sources: List[SourceResponse]
    generated_at: datetime
    word_count: int


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.now)
    services: dict = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
