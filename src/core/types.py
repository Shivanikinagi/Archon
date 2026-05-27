"""
Type definitions and enums for the research agent system.
"""

from enum import Enum
from typing import Literal, TypeAlias
from dataclasses import dataclass
from datetime import datetime


class ResearchDepth(str, Enum):
    """Depth of research to perform."""
    SHALLOW = "shallow"      # Quick overview, 2-3 sources
    MODERATE = "moderate"    # Balanced research, 5-10 sources
    DEEP = "deep"           # Comprehensive research, 10+ sources
    EXHAUSTIVE = "exhaustive"  # Maximum depth, 20+ sources


class SourceType(str, Enum):
    """Types of research sources."""
    WEB = "web"              # General web pages
    ACADEMIC = "academic"    # Research papers and journals
    NEWS = "news"           # News articles
    DOCUMENTATION = "docs"   # Official documentation
    BOOKS = "books"         # Books and publications
    UPLOADED = "uploaded"    # User-uploaded documents


class ReportFormat(str, Enum):
    """Output format for research reports."""
    MARKDOWN = "markdown"
    HTML = "html"
    PDF = "pdf"
    JSON = "json"
    DOCX = "docx"


class CitationStyle(str, Enum):
    """Citation formatting styles."""
    APA = "apa"
    MLA = "mla"
    CHICAGO = "chicago"
    HARVARD = "harvard"
    IEEE = "ieee"


class AgentRole(str, Enum):
    """Roles of different agents in the system."""
    PLANNER = "planner"
    SEARCHER = "searcher"
    WRITER = "writer"
    FACT_CHECKER = "fact_checker"
    REVIEWER = "reviewer"
    ORCHESTRATOR = "orchestrator"


class ResearchStatus(str, Enum):
    """Status of a research session."""
    INITIALIZED = "initialized"
    PLANNING = "planning"
    RESEARCHING = "researching"
    PROCESSING = "processing"
    WRITING = "writing"
    FACT_CHECKING = "fact_checking"
    REVIEWING = "reviewing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# Type aliases for common patterns
DocumentId: TypeAlias = str
NodeId: TypeAlias = str
EdgeId: TypeAlias = str
SessionId: TypeAlias = str
ReportId: TypeAlias = str


@dataclass
class Source:
    """Reference source for research content."""
    url: str
    title: str
    source_type: SourceType
    retrieved_at: datetime
    author: str | None = None
    publication_date: datetime | None = None
    content_type: str | None = None  # MIME type
    confidence: float = 1.0  # Confidence score 0-1


@dataclass
class Citation:
    """Citation information for a source."""
    source: Source
    style: CitationStyle
    formatted_text: str
    page_number: int | None = None


@dataclass
class ResearchQuery:
    """Structured research query."""
    query_text: str
    depth: ResearchDepth = ResearchDepth.MODERATE
    source_types: list[SourceType] | None = None
    max_results: int | None = None
    language: str = "en"
    include_citations: bool = True
    citation_style: CitationStyle = CitationStyle.APA


@dataclass
class ResearchPlan:
    """Research plan with structured subtopics."""
    main_query: str
    subtopics: list[str]
    search_queries: list[str]
    research_depth: ResearchDepth
    estimated_sources: int
    timeline_minutes: int


@dataclass
class DocumentChunk:
    """A chunk of processed document."""
    chunk_id: str
    document_id: str
    content: str
    source: Source
    metadata: dict
    embedding: list[float] | None = None
    chunk_index: int | None = None
    total_chunks: int | None = None


@dataclass
class KnowledgeGraphNode:
    """Node in the knowledge graph."""
    node_id: str
    label: str
    node_type: str
    properties: dict
    embedding: list[float] | None = None
    relevance_score: float = 1.0


@dataclass
class KnowledgeGraphEdge:
    """Edge in the knowledge graph."""
    edge_id: str
    source_node_id: str
    target_node_id: str
    relationship_type: str
    properties: dict
    weight: float = 1.0


@dataclass
class RetrievalResult:
    """Result from retrieval operations."""
    chunk: DocumentChunk
    similarity_score: float
    rank: int
    retrieval_method: Literal["rag", "graphrag", "fusion"]
    metadata: dict | None = None


@dataclass
class ClaimVerification:
    """Result of fact-checking a claim."""
    claim: str
    status: Literal["verified", "disputed", "unverifiable"]
    confidence: float
    supporting_sources: list[Source]
    contradicting_sources: list[Source]
    explanation: str
