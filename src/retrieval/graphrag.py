"""
GraphRAG retriever for semantic relationship-based retrieval.
"""

from typing import Optional
from src.core.base import BaseRetriever
from src.core.types import ResearchQuery, RetrievalResult, DocumentChunk
from src.core.logger import get_logger
from src.core.config import get_config

logger = get_logger(__name__)


class GraphRAGRetriever(BaseRetriever):
    """
    GraphRAG retriever for semantic relationship-based search.
    Uses knowledge graphs to find relevant information through relationships.
    """

    def __init__(self, graph_store, rag_retriever, config=None):
        """
        Initialize GraphRAG retriever.

        Args:
            graph_store: Knowledge graph store (Neo4j, etc.)
            rag_retriever: RAG retriever for initial candidate retrieval
            config: Configuration object
        """
        super().__init__("GraphRAG Retriever")
        self.graph_store = graph_store
        self.rag_retriever = rag_retriever
        self.config = config or get_config()

    async def retrieve(
        self,
        query: ResearchQuery,
        top_k: int = 10,
    ) -> list[RetrievalResult]:
        """
        Retrieve documents using GraphRAG.

        Args:
            query: Research query
            top_k: Number of top results

        Returns:
            List of retrieval results ranked by relevance
        """
        try:
            # First, get initial candidates using RAG
            rag_results = await self.rag_retriever.retrieve(query, top_k=top_k * 2)

            if not rag_results:
                self.logger.warning("No RAG results to expand with GraphRAG")
                return []

            # Expand results using graph relationships
            expanded_results = []
            for rag_result in rag_results:
                # Try to get related nodes from graph
                neighbors = await self._get_related_documents(rag_result.chunk)
                expanded_results.extend(neighbors)

            # Deduplicate and rerank
            unique_results = self._deduplicate_results(expanded_results)
            ranked_results = self._rerank_results(unique_results, query, top_k)

            self.logger.info(
                f"GraphRAG retrieval returned {len(ranked_results)} results "
                f"for query: {query.query_text}"
            )
            return ranked_results

        except Exception as e:
            self.logger.error(f"GraphRAG retrieval failed: {str(e)}")
            # Fall back to RAG
            return await self.rag_retriever.retrieve(query, top_k=top_k)

    async def retrieve_by_similarity(
        self,
        embedding: list[float],
        top_k: int = 10,
    ) -> list[RetrievalResult]:
        """
        Retrieve documents by embedding similarity with graph expansion.

        Args:
            embedding: Query embedding vector
            top_k: Number of top results

        Returns:
            List of retrieval results
        """
        # Delegate to RAG retriever
        return await self.rag_retriever.retrieve_by_similarity(embedding, top_k)

    async def _get_related_documents(self, chunk: DocumentChunk) -> list[RetrievalResult]:
        """Get related documents from the knowledge graph."""
        results = []
        try:
            # Extract entities/topics from chunk (simplified)
            # In practice, would use NER or other entity extraction
            node_id = chunk.chunk_id

            # Get neighbors in graph
            neighbors = await self.graph_store.get_neighbors(
                node_id,
                max_hops=self.config.graphrag.max_hops,
            )

            for rank, neighbor in enumerate(neighbors, 1):
                # Create a retrieval result for each neighbor
                result = RetrievalResult(
                    chunk=chunk,  # Would reconstruct from neighbor
                    similarity_score=neighbor.relevance_score,
                    rank=rank,
                    retrieval_method="graphrag",
                )
                results.append(result)

        except Exception as e:
            self.logger.debug(f"Failed to get related documents: {str(e)}")

        return results

    def _deduplicate_results(
        self,
        results: list[RetrievalResult],
    ) -> list[RetrievalResult]:
        """Remove duplicate results."""
        seen_ids = set()
        unique_results = []

        for result in results:
            if result.chunk.chunk_id not in seen_ids:
                seen_ids.add(result.chunk.chunk_id)
                unique_results.append(result)

        return unique_results

    def _rerank_results(
        self,
        results: list[RetrievalResult],
        query: ResearchQuery,
        top_k: int,
    ) -> list[RetrievalResult]:
        """Rerank results by relevance."""
        # Sort by similarity score and apply cutoff
        sorted_results = sorted(
            results,
            key=lambda r: r.similarity_score,
            reverse=True,
        )

        filtered_results = [
            r for r in sorted_results
            if r.similarity_score >= self.config.graphrag.similarity_cutoff
        ]

        return filtered_results[:top_k]
