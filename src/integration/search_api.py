"""
Web search integrations for research data gathering.
"""

from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass
from datetime import datetime

from src.core.types import Source, SourceType
from src.core.logger import get_logger
from src.core.exceptions import SearchError

logger = get_logger(__name__)


@dataclass
class SearchResult:
    """Result from a web search."""
    title: str
    url: str
    snippet: str
    source_type: SourceType = SourceType.WEB
    published_date: Optional[datetime] = None
    author: Optional[str] = None

    def to_source(self) -> Source:
        """Convert to Source object."""
        return Source(
            url=self.url,
            title=self.title,
            source_type=self.source_type,
            retrieved_at=datetime.now(),
            publication_date=self.published_date,
            author=self.author,
        )


class SearchProvider(ABC):
    """Base class for search providers."""

    @abstractmethod
    async def search(self, query: str, max_results: int = 10) -> list[SearchResult]:
        """Execute a search query."""
        pass


class SerperSearchProvider(SearchProvider):
    """Search provider using Serper API."""

    def __init__(self, api_key: str):
        """Initialize Serper search provider."""
        self.api_key = api_key
        self.base_url = "https://google.serper.dev"

    async def search(self, query: str, max_results: int = 10) -> list[SearchResult]:
        """Search using Serper API."""
        try:
            import httpx

            headers = {
                "X-API-KEY": self.api_key,
                "Content-Type": "application/json",
            }

            params = {
                "q": query,
                "num": max_results,
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/search",
                    json=params,
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()

            results = []
            for item in data.get("organic", []):
                result = SearchResult(
                    title=item.get("title", ""),
                    url=item.get("link", ""),
                    snippet=item.get("snippet", ""),
                    source_type=SourceType.WEB,
                )
                results.append(result)

            return results

        except Exception as e:
            logger.error(f"Serper search failed: {str(e)}")
            raise SearchError(f"Search failed: {str(e)}")


class GoogleSearchProvider(SearchProvider):
    """Search provider using Google Custom Search API."""

    def __init__(self, api_key: str, search_engine_id: str):
        """Initialize Google search provider."""
        self.api_key = api_key
        self.search_engine_id = search_engine_id
        self.base_url = "https://www.googleapis.com/customsearch/v1"

    async def search(self, query: str, max_results: int = 10) -> list[SearchResult]:
        """Search using Google Custom Search API."""
        try:
            import httpx

            params = {
                "q": query,
                "key": self.api_key,
                "cx": self.search_engine_id,
                "num": min(max_results, 10),  # Google limits to 10
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                data = response.json()

            results = []
            for item in data.get("items", []):
                result = SearchResult(
                    title=item.get("title", ""),
                    url=item.get("link", ""),
                    snippet=item.get("snippet", ""),
                    source_type=SourceType.WEB,
                )
                results.append(result)

            return results

        except Exception as e:
            logger.error(f"Google search failed: {str(e)}")
            raise SearchError(f"Search failed: {str(e)}")


class SearchProviderFactory:
    """Factory for creating search providers."""

    @staticmethod
    def create_provider(
        provider_type: str,
        **kwargs,
    ) -> SearchProvider:
        """Create a search provider."""
        if provider_type.lower() == "serper":
            return SerperSearchProvider(kwargs.get("api_key"))
        elif provider_type.lower() == "google":
            return GoogleSearchProvider(
                kwargs.get("api_key"),
                kwargs.get("search_engine_id"),
            )
        else:
            raise SearchError(f"Unknown search provider: {provider_type}")
