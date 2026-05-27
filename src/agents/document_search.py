"""
Document Search Agent - Searches indexed documents using the RetrievalService.
"""

from typing import Any
from src.core.base import BaseAgent, ExecutionResult
from src.core.types import AgentRole
from src.core.logger import get_logger
from src.services.retrieval_service import RetrievalService, RetrievalResult


class DocumentSearchAgent(BaseAgent):
    """Agent responsible for searching indexed documents."""

    def __init__(self, retrieval_service: RetrievalService | None = None):
        """
        Initialize Document Search Agent.

        Args:
            retrieval_service: RetrievalService instance. If None, a new one is created.
        """
        super().__init__(role=AgentRole.SEARCHER, name="Document Searcher")
        self.retrieval_service = retrieval_service or RetrievalService()

    def validate_inputs(self, **kwargs: Any) -> bool:
        """Validate document search inputs."""
        query = kwargs.get("query")
        if not isinstance(query, str) or not query.strip():
            self.logger.warning("Invalid query: must be a non-empty string")
            return False

        top_k = kwargs.get("top_k", 10)
        if not isinstance(top_k, int) or top_k < 1:
            self.logger.warning("Invalid top_k: must be a positive integer")
            return False

        return True

    async def execute(self, **kwargs: Any) -> ExecutionResult:
        """
        Execute a document search against indexed documents.

        Args:
            query: Search query string.
            top_k: Number of top results to retrieve (default: 10).

        Returns:
            ExecutionResult containing a list of RetrievalResult objects.
        """
        query: str = kwargs["query"]
        top_k: int = kwargs.get("top_k", 10)

        try:
            self.logger.info(f"Executing document search for query: {query!r}")

            results = await self.retrieval_service.retrieve(
                query=query,
                top_k=top_k,
            )

            self.logger.info(f"Document search returned {len(results)} results")

            return ExecutionResult(
                success=True,
                data=results,
                metadata={
                    "query": query,
                    "top_k": top_k,
                    "num_results_returned": len(results),
                },
            )

        except Exception as e:
            self.logger.error(f"Document search failed: {e}")
            return ExecutionResult(
                success=False,
                error=str(e),
                metadata={"query": query},
            )
