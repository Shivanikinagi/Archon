"""Services layer for business logic

This module provides higher-level services for:
- Embedding generation and management
- LLM operations and prompt management
- Document processing and chunking
- Search operations across multiple sources
- Multi-stage RAG retrieval
"""

# Avoid eager imports to prevent circular imports
# Import directly from submodules as needed

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
