"""
Web Search Agent - Performs web searches using the SearchService.
"""

from typing import Any
from src.core.base import BaseAgent, ExecutionResult
from src.core.types import AgentRole
from src.core.logger import get_logger
from src.services.search_service import SearchService
from src.integration.search_clients import SearchResult


class WebSearchAgent(BaseAgent):
    """Agent responsible for performing web searches."""

    def __init__(self, search_service: SearchService | None = None):
        """
        Initialize Web Search Agent.

        Args:
            search_service: SearchService instance. If None, a new one is created.
        """
        super().__init__(role=AgentRole.SEARCHER, name="Web Searcher")
        self.search_service = search_service or SearchService()

    def validate_inputs(self, **kwargs: Any) -> bool:
        """Validate web search inputs."""
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
        Execute a web search.

        Args:
            query: Search query string.
            num_results: Number of results to retrieve (default: 10).

        Returns:
            ExecutionResult containing a list of SearchResult objects.
        """
        query: str = kwargs["query"]
        num_results: int = kwargs.get("num_results", 10)

        try:
            self.logger.info(f"Executing web search for query: {query!r}")

            results = await self.search_service.web_search(
                query=query,
                num_results=num_results,
            )

            self.logger.info(f"Web search returned {len(results)} results")

            return ExecutionResult(
                success=True,
                data=results,
                metadata={
                    "query": query,
                    "num_results_requested": num_results,
                    "num_results_returned": len(results),
                },
            )

        except Exception as e:
            self.logger.error(f"Web search failed: {e}")
            return ExecutionResult(
                success=False,
                error=str(e),
                metadata={"query": query},
            )
