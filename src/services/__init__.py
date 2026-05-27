"""Services layer for business logic

This module provides higher-level services for:
- Embedding generation and management
- LLM operations and prompt management
- Document processing and chunking
- Search operations across multiple sources
- Multi-stage RAG retrieval
"""

from services.embedding_service import EmbeddingService
from services.llm_service import LLMService, PromptTemplate
from services.document_processor import DocumentProcessor, DocumentChunk, TextCleaner
from services.search_service import SearchService
from services.retrieval_service import RetrievalService, BM25Scorer, RetrievalResult

__all__ = [
    "EmbeddingService",
    "LLMService",
    "PromptTemplate",
    "DocumentProcessor",
    "DocumentChunk",
    "TextCleaner",
    "SearchService",
    "RetrievalService",
    "BM25Scorer",
    "RetrievalResult",
]
