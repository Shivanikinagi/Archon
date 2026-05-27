"""
Hybrid retriever combining RAG and GraphRAG with reciprocal rank fusion.

Retrieves candidates from both semantic (RAG) and graph-based (GraphRAG)
retrievers, normalizes their scores, and fuses the result lists using
reciprocal rank fusion (RRF) to produce a single ranked output.
"""

import asyncio

from src.core.base import BaseRetriever
from src.core.types import ResearchQuery, RetrievalResult, DocumentChunk
from src.core.logger import get_logger
from src.core.config import get_config

from src.retrieval.rag import RAGRetriever
from src.retrieval.graphrag import GraphRAGRetriever

logger = get_logger(__name__)


class HybridRetriever(BaseRetriever):
    """
    Hybrid retriever that combines RAG and GraphRAG results.

    Candidates are fetched from both retrievers concurrently, scores are
    normalized to the [0, 1] range, and the two ranked lists are fused
    via reciprocal rank fusion (RRF). Results are deduplicated by chunk_id
    and returned as a single ranked list capped at ``top_k``.
    """

    def __init__(
        self,
        rag_retriever: RAGRetriever,
        graphrag_retriever: GraphRAGRetriever,
        config=None,
    ):
        """
        Initialize the hybrid retriever.

        Args:
            rag_retriever: RAG retriever instance for semantic search.
            graphrag_retriever: GraphRAG retriever instance for graph-based search.
            config: Optional configuration object.
        """
        super().__init__("Hybrid Retriever")
        self.rag_retriever = rag_retriever
        self.graphrag_retriever = graphrag_retriever
        self.config = config or get_config()

    async def retrieve(
        self,
        query: ResearchQuery,
        top_k: int = 10,
    ) -> list[RetrievalResult]:
        """
        Retrieve documents using hybrid RAG + GraphRAG fusion.

        Both retrievers are queried concurrently (requesting ``top_k * 2``
        candidates each). Their result lists are normalized and fused with
        RRF. The final list is deduplicated by ``chunk_id`` and truncated
        to ``top_k``.

        Args:
            query: The research query.
            top_k: Number of top results to return.

        Returns:
            Fused and ranked list of ``RetrievalResult`` objects.
        """
        try:
            # Concurrent retrieval from both sources
            rag_results, graphrag_results = await asyncio.gather(
                self.rag_retriever.retrieve(query, top_k=top_k * 2),
                self.graphrag_retriever.retrieve(query, top_k=top_k * 2),
                return_exceptions=True,
            )

            if isinstance(rag_results, Exception):
                self.logger.error(f"RAG retrieval failed: {rag_results}")
                rag_results = []
            if isinstance(graphrag_results, Exception):
                self.logger.error(f"GraphRAG retrieval failed: {graphrag_results}")
                graphrag_results = []

            if not rag_results and not graphrag_results:
                self.logger.warning("No results from either retriever")
                return []

            # Normalize scores independently
            rag_results = self._normalize_scores(rag_results)
            graphrag_results = self._normalize_scores(graphrag_results)

            # Reciprocal rank fusion
            fused_scores = self._reciprocal_rank_fusion(
                rag_results, graphrag_results, k=60
            )

            # Sort by fused score descending
            sorted_items = sorted(
                fused_scores.items(),
                key=lambda item: item[1],
                reverse=True,
            )

            # Build final results
            final_results: list[RetrievalResult] = []
            for rank, (chunk_id, fused_score) in enumerate(sorted_items, 1):
                chunk = self._get_chunk_by_id(rag_results + graphrag_results, chunk_id)
                if chunk is None:
                    continue

                result = RetrievalResult(
                    chunk=chunk,
                    similarity_score=fused_score,
                    rank=rank,
                    retrieval_method="fusion",
                    metadata={
                        "rag_score": self._get_score_for_chunk(rag_results, chunk_id),
                        "graphrag_score": self._get_score_for_chunk(
                            graphrag_results, chunk_id
                        ),
                    },
                )
                final_results.append(result)

            self.logger.info(
                f"Hybrid retrieval returned {len(final_results)} fused results "
                f"for query: {query.query_text}"
            )
            return final_results[:top_k]

        except Exception as exc:
            self.logger.error(f"Hybrid retrieval failed: {exc}")
            # Fallback to pure RAG
            return await self.rag_retriever.retrieve(query, top_k=top_k)

    async def retrieve_by_similarity(
        self,
        embedding: list[float],
        top_k: int = 10,
    ) -> list[RetrievalResult]:
        """
        Retrieve documents by embedding similarity using hybrid fusion.

        Args:
            embedding: Query embedding vector.
            top_k: Number of top results to return.

        Returns:
            Fused and ranked list of ``RetrievalResult`` objects.
        """
        try:
            rag_results, graphrag_results = await asyncio.gather(
                self.rag_retriever.retrieve_by_similarity(embedding, top_k=top_k * 2),
                self.graphrag_retriever.retrieve_by_similarity(
                    embedding, top_k=top_k * 2
                ),
                return_exceptions=True,
            )

            if isinstance(rag_results, Exception):
                self.logger.error(f"RAG similarity retrieval failed: {rag_results}")
                rag_results = []
            if isinstance(graphrag_results, Exception):
                self.logger.error(
                    f"GraphRAG similarity retrieval failed: {graphrag_results}"
                )
                graphrag_results = []

            rag_results = self._normalize_scores(rag_results)
            graphrag_results = self._normalize_scores(graphrag_results)

            fused_scores = self._reciprocal_rank_fusion(
                rag_results, graphrag_results, k=60
            )

            sorted_items = sorted(
                fused_scores.items(),
                key=lambda item: item[1],
                reverse=True,
            )

            final_results: list[RetrievalResult] = []
            for rank, (chunk_id, fused_score) in enumerate(sorted_items, 1):
                chunk = self._get_chunk_by_id(rag_results + graphrag_results, chunk_id)
                if chunk is None:
                    continue

                result = RetrievalResult(
                    chunk=chunk,
                    similarity_score=fused_score,
                    rank=rank,
                    retrieval_method="fusion",
                )
                final_results.append(result)

            return final_results[:top_k]

        except Exception as exc:
            self.logger.error(f"Hybrid similarity retrieval failed: {exc}")
            return await self.rag_retriever.retrieve_by_similarity(embedding, top_k)

    def _normalize_scores(
        self, results: list[RetrievalResult]
    ) -> list[RetrievalResult]:
        """
        Normalize similarity scores to the [0, 1] range.

        Min-max normalization is applied so that scores from different
        retrievers are comparable.

        Args:
            results: List of retrieval results.

        Returns:
            The same list with updated ``similarity_score`` values.
        """
        if not results:
            return []

        scores = [r.similarity_score for r in results]
        min_score = min(scores)
        max_score = max(scores)

        if max_score == min_score:
            for r in results:
                r.similarity_score = 1.0
            return results

        for r in results:
            r.similarity_score = (r.similarity_score - min_score) / (
                max_score - min_score
            )

        return results

    def _reciprocal_rank_fusion(
        self,
        rag_results: list[RetrievalResult],
        graphrag_results: list[RetrievalResult],
        k: int = 60,
    ) -> dict[str, float]:
        """
        Fuse two ranked lists using reciprocal rank fusion.

        The RRF score for a document is the sum of ``1 / (k + rank)``
        across all lists in which it appears.

        Args:
            rag_results: Results from the RAG retriever.
            graphrag_results: Results from the GraphRAG retriever.
            k: RRF constant (default 60).

        Returns:
            Dictionary mapping ``chunk_id`` to fused score.
        """
        fused_scores: dict[str, float] = {}

        for result in rag_results:
            rank = result.rank
            chunk_id = result.chunk.chunk_id
            score = 1.0 / (k + rank)
            fused_scores[chunk_id] = fused_scores.get(chunk_id, 0.0) + score

        for result in graphrag_results:
            rank = result.rank
            chunk_id = result.chunk.chunk_id
            score = 1.0 / (k + rank)
            fused_scores[chunk_id] = fused_scores.get(chunk_id, 0.0) + score

        return fused_scores

    def _get_chunk_by_id(
        self,
        results: list[RetrievalResult],
        chunk_id: str,
    ) -> DocumentChunk | None:
        """
        Find a ``DocumentChunk`` by its ID in a list of results.

        Args:
            results: List of retrieval results to search.
            chunk_id: The chunk ID to look up.

        Returns:
            The matching ``DocumentChunk`` or ``None``.
        """
        for r in results:
            if r.chunk.chunk_id == chunk_id:
                return r.chunk
        return None

    def _get_score_for_chunk(
        self,
        results: list[RetrievalResult],
        chunk_id: str,
    ) -> float | None:
        """
        Retrieve the similarity score for a specific chunk from a result list.

        Args:
            results: List of retrieval results.
            chunk_id: The chunk ID to look up.

        Returns:
            The similarity score if found, otherwise ``None``.
        """
        for r in results:
            if r.chunk.chunk_id == chunk_id:
                return r.similarity_score
        return None
