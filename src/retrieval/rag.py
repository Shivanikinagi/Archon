"""
RAG (Retrieval-Augmented Generation) retriever.
"""

from typing import Optional
from src.core.base import BaseRetriever
from src.core.types import ResearchQuery, RetrievalResult, DocumentChunk, SourceType
from src.core.logger import get_logger
from src.core.config import get_config

logger = get_logger(__name__)


class RAGRetriever(BaseRetriever):
    """
    RAG retriever for semantic search using vector embeddings.
    """

    def __init__(self, vector_store, embedding_service, config=None):
        """
        Initialize RAG retriever.

        Args:
            vector_store: Vector store instance (ChromaDB, etc.)
            embedding_service: Embedding service for query encoding
            config: Configuration object
        """
        super().__init__("RAG Retriever")
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.config = config or get_config()

    async def retrieve(
        self,
        query: ResearchQuery,
        top_k: int = 10,
    ) -> list[RetrievalResult]:
        """
        Retrieve documents using RAG.

        Args:
            query: Research query
            top_k: Number of top results

        Returns:
            List of retrieval results ranked by relevance
        """
        try:
            # Generate embedding for query
            query_embedding = await self.embedding_service.embed_text(query.query_text)

            # Search vector store
            results = await self.vector_store.search(query_embedding, top_k=top_k)

            # Convert to RetrievalResult objects
            retrieval_results = []
            for rank, (chunk, similarity_score) in enumerate(results, 1):
                if similarity_score >= self.config.rag.similarity_threshold:
                    result = RetrievalResult(
                        chunk=chunk,
                        similarity_score=similarity_score,
                        rank=rank,
                        retrieval_method="rag",
                    )
                    retrieval_results.append(result)

            self.logger.info(
                f"RAG retrieval returned {len(retrieval_results)} results "
                f"for query: {query.query_text}"
            )
            return retrieval_results

        except Exception as e:
            self.logger.error(f"RAG retrieval failed: {str(e)}")
            return []

    async def retrieve_by_similarity(
        self,
        embedding: list[float],
        top_k: int = 10,
    ) -> list[RetrievalResult]:
        """
        Retrieve documents by embedding similarity.

        Args:
            embedding: Query embedding vector
            top_k: Number of top results

        Returns:
            List of retrieval results
        """
        try:
            results = await self.vector_store.search(embedding, top_k=top_k)

            retrieval_results = []
            for rank, (chunk, similarity_score) in enumerate(results, 1):
                result = RetrievalResult(
                    chunk=chunk,
                    similarity_score=similarity_score,
                    rank=rank,
                    retrieval_method="rag",
                )
                retrieval_results.append(result)

            return retrieval_results

        except Exception as e:
            self.logger.error(f"Similarity retrieval failed: {str(e)}")
            return []
