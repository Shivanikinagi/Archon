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


class UserRegisterRequest(BaseModel):
    """Request for user registration."""
    email: str
    password: str
    name: str


class UserLoginRequest(BaseModel):
    """Request for user login."""
    email: str
    password: str


class RefreshTokenRequest(BaseModel):
    """Request for token refresh."""
    refresh_token: str


class ModelPullRequest(BaseModel):
    """Request to pull an Ollama model."""
    model_name: str


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
    error: Optional[str] = None
    current_step: Optional[str] = None


class ResearchReportResponse(BaseModel):
    """Research report response."""
    report_id: str
    session_id: str
    title: str
    content: str
    format: str = "markdown"
    citations: List[dict] = Field(default_factory=list)
    sources: List[dict] = Field(default_factory=list)
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


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    """User response."""
    user_id: int
    email: str
    name: str
    role: str = "user"
    created_at: Optional[datetime] = None


class ProgressResponse(BaseModel):
    """Research progress response."""
    session_id: str
    status: str
    progress: float = Field(default=0.0, ge=0.0, le=1.0)
    current_step: Optional[str] = None
    message: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.now)


class DocumentResponse(BaseModel):
    """Document response."""
    doc_id: str
    title: str
    filename: str
    content_type: str
    size: int
    uploaded_at: datetime
    status: str = "processing"


class EntityResponse(BaseModel):
    """Knowledge graph entity response."""
    node_id: str
    label: str
    node_type: str
    properties: dict = Field(default_factory=dict)


class RelationshipResponse(BaseModel):
    """Knowledge graph relationship response."""
    edge_id: str
    source_node_id: str
    target_node_id: str
    relationship_type: str
    properties: dict = Field(default_factory=dict)
    weight: float = 1.0


class GraphSearchResponse(BaseModel):
    """Knowledge graph search response."""
    entities: List[EntityResponse]
    relationships: List[RelationshipResponse]


class PathResponse(BaseModel):
    """Knowledge graph path response."""
    path: List[EntityResponse]
    length: int
    total_weight: float


class ReportSummaryResponse(BaseModel):
    """Report summary for listing."""
    report_id: str
    session_id: str
    title: str
    format: str
    generated_at: datetime
    word_count: int


class SystemStatsResponse(BaseModel):
    """System statistics response."""
    total_sessions: int
    total_reports: int
    total_documents: int
    total_users: int
    active_sessions: int
    system_load: float
    uptime_seconds: int


class UserAdminResponse(BaseModel):
    """User admin response."""
    user_id: int
    email: str
    name: str
    role: str
    is_active: bool = True
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None


class HealthDetailedResponse(BaseModel):
    """Detailed health check response."""
    status: str
    timestamp: datetime = Field(default_factory=datetime.now)
    version: str
    services: dict = Field(default_factory=dict)
