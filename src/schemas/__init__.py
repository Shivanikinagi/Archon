"""
Pydantic request and response schemas for API validation

Handles all request/response validation and serialization.
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class UserRole(str, Enum):
    """User role enum"""
    USER = "user"
    RESEARCHER = "researcher"
    ADMIN = "admin"


class ResearchStatus(str, Enum):
    """Research session status enum"""
    PLANNING = "planning"
    RESEARCHING = "researching"
    GENERATING = "generating"
    FACT_CHECKING = "fact_checking"
    REVIEWING = "reviewing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ResearchDepth(str, Enum):
    """Research depth enum"""
    SHALLOW = "shallow"
    MODERATE = "moderate"
    DEEP = "deep"


class CitationStyle(str, Enum):
    """Citation style enum"""
    APA = "apa"
    MLA = "mla"
    CHICAGO = "chicago"
    HARVARD = "harvard"
    IEEE = "ieee"


# ============================================================================
# USER SCHEMAS
# ============================================================================

class UserBase(BaseModel):
    """Base user schema"""
    username: str = Field(..., min_length=3, max_length=255)
    email: EmailStr
    full_name: Optional[str] = Field(None, max_length=255)


class UserCreate(UserBase):
    """User creation schema"""
    password: str = Field(..., min_length=8)
    
    @field_validator("password")
    def validate_password(cls, v):
        """Validate password strength"""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain digit")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError("Password must contain special character")
        return v


class UserResponse(UserBase):
    """User response schema"""
    id: int
    is_active: bool
    is_verified: bool
    role: UserRole
    created_at: datetime
    last_login: Optional[datetime]
    
    class Config:
        from_attributes = True


# ============================================================================
# AUTHENTICATION SCHEMAS
# ============================================================================

class LoginRequest(BaseModel):
    """Login request schema"""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Token response schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    """Token refresh request schema"""
    refresh_token: str


# ============================================================================
# RESEARCH SCHEMAS
# ============================================================================

class ResearchRequest(BaseModel):
    """Research session creation request"""
    query: str = Field(..., min_length=5, max_length=500)
    depth: ResearchDepth = ResearchDepth.MODERATE
    max_sources: int = Field(50, ge=1, le=500)
    include_citations: bool = True
    citation_style: CitationStyle = CitationStyle.APA
    
    @field_validator("query")
    def validate_query(cls, v):
        """Validate research query"""
        # No SQL injection attempts
        if any(char in v for char in [";", "--", "/*", "*/"]):
            raise ValueError("Invalid characters in query")
        
        # No excessive special characters
        special_chars = sum(1 for c in v if not c.isalnum() and c != " ")
        if special_chars > len(v) * 0.3:
            raise ValueError("Too many special characters")
        
        return v.strip()


class ResearchResponse(BaseModel):
    """Research session response"""
    session_id: str
    status: ResearchStatus
    progress: int
    created_at: datetime
    estimated_completion: Optional[datetime]
    error: Optional[str] = None


class ResearchStatusResponse(BaseModel):
    """Research status response"""
    session_id: str
    status: ResearchStatus
    progress: int
    current_step: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]
    estimated_completion: Optional[datetime]
    error: Optional[str] = None


class ResearchReportResponse(BaseModel):
    """Research report response"""
    report_id: str
    session_id: str
    title: str
    content_markdown: str
    word_count: int
    citation_count: int
    completeness_score: float
    consistency_score: float
    readability_score: float
    created_at: datetime
    published_at: Optional[datetime]


# ============================================================================
# REPORT SCHEMAS
# ============================================================================

class ReportListResponse(BaseModel):
    """Report list response"""
    reports: List[ResearchReportResponse]
    total: int
    skip: int
    limit: int


class ReportExportRequest(BaseModel):
    """Report export request"""
    format: str = Field("pdf")  # pdf, html, markdown, json
    
    @field_validator("format")
    def validate_format(cls, v):
        """Validate export format"""
        if v not in ["pdf", "html", "markdown", "json"]:
            raise ValueError("Invalid export format")
        return v


# ============================================================================
# DOCUMENT SCHEMAS
# ============================================================================

class DocumentResponse(BaseModel):
    """Document response schema"""
    document_id: str
    filename: str
    file_type: str
    file_size: int
    processing_status: str
    created_at: datetime
    processed_at: Optional[datetime]


class DocumentListResponse(BaseModel):
    """Document list response"""
    documents: List[DocumentResponse]
    total: int


# ============================================================================
# GRAPH SCHEMAS
# ============================================================================

class EntityNode(BaseModel):
    """Entity node in knowledge graph"""
    id: str
    label: str
    name: str
    type: str  # Person, Organization, Concept, etc.
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class RelationshipEdge(BaseModel):
    """Relationship edge in knowledge graph"""
    id: str
    source_id: str
    target_id: str
    type: str  # MENTIONS, SUPPORTS, CONTRADICTS, etc.
    weight: float = 1.0
    metadata: Optional[Dict[str, Any]] = None


class GraphVisualization(BaseModel):
    """Graph visualization in vis.js format"""
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]


class GraphEntitiesResponse(BaseModel):
    """Graph entities response"""
    entities: List[EntityNode]


class GraphRelationshipsResponse(BaseModel):
    """Graph relationships response"""
    relationships: List[RelationshipEdge]


# ============================================================================
# ERROR SCHEMAS
# ============================================================================

class ErrorResponse(BaseModel):
    """Error response schema"""
    code: str
    message: str
    status_code: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: Optional[Dict[str, Any]] = None


class ValidationErrorResponse(BaseModel):
    """Validation error response"""
    code: str = "VALIDATION_ERROR"
    message: str = "Validation failed"
    status_code: int = 400
    errors: List[Dict[str, str]]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# PAGINATION SCHEMAS
# ============================================================================

class PaginationParams(BaseModel):
    """Pagination parameters"""
    skip: int = Field(0, ge=0)
    limit: int = Field(10, ge=1, le=100)


# ============================================================================
# HEALTH CHECK SCHEMAS
# ============================================================================

class HealthResponse(BaseModel):
    """Health check response"""
    status: str = "healthy"
    version: str
    environment: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
