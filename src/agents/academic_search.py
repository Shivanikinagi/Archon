"""
Academic Search Agent - Performs academic searches using the SearchService.
"""

from typing import Any
from src.core.base import BaseAgent, ExecutionResult
from src.core.types import AgentRole
from src.core.logger import get_logger
from src.services.search_service import SearchService
from src.integration.search_clients import SearchResult


class AcademicSearchAgent(BaseAgent):
    """Agent responsible for performing academic searches."""

    def __init__(self, search_service: SearchService | None = None):
        """
        Initialize Academic Search Agent.

        Args:
            search_service: SearchService instance. If None, a new one is created.
        """
        super().__init__(role=AgentRole.SEARCHER, name="Academic Searcher")
        self.search_service = search_service or SearchService()

    def validate_inputs(self, **kwargs: Any) -> bool:
        """Validate academic search inputs."""
        query = kwargs.get("query")
        if not isinstance(query, str) or not query.strip():
            self.logger.warning("Invalid query: must be a non-empty string")
            return False

        num_results = kwargs.get("num_results", 10)
        if not isinstance(num_results, int) or num_results < 1:
            self.logger.warning("Invalid num_results: must be a positive integer")
            return False

        return True

    async def execute(self, **kwargs: Any) -> ExecutionResult:
        """
        Execute an academic search.

        Args:
            query: Search query string.
            num_results: Number of results to retrieve (default: 10).

        Returns:
            ExecutionResult containing a list of SearchResult objects.
        """
        query: str = kwargs["query"]
        num_results: int = kwargs.get("num_results", 10)

        try:
            self.logger.info(f"Executing academic search for query: {query!r}")

            # Search semantic_scholar and core, then merge results
            ss_results = await self.search_service.academic_search(
                query=query,
                num_results=num_results,
                provider="semantic_scholar",
            )
            core_results = await self.search_service.academic_search(
                query=query,
                num_results=num_results,
                provider="core",
            )

            # Merge and deduplicate
            merged = self.search_service.merge_and_rank(
                web_results=[],
                academic_results=ss_results + core_results,
                total_limit=num_results,
                academic_weight=1.0,
            )

            self.logger.info(f"Academic search returned {len(merged)} results")

            return ExecutionResult(
                success=True,
                data=merged,
                metadata={
                    "query": query,
                    "num_results_requested": num_results,
                    "num_results_returned": len(merged),
                    "semantic_scholar_count": len(ss_results),
                    "core_count": len(core_results),
                },
            )

        except Exception as e:
            self.logger.error(f"Academic search failed: {e}")
            return ExecutionResult(
                success=False,
                error=str(e),
                metadata={"query": query},
            )
