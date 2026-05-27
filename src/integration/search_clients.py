"""Search clients for web and academic search integration

Provides interfaces to Serper, Google Search, Semantic Scholar, and CORE APIs.
"""

import logging
from typing import Optional, List, Dict, Any
import httpx
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Represents a search result"""
    title: str
    url: str
    snippet: str
    source: str  # "web", "academic", "scholar", "core"
    relevance_score: float = 0.0  # 0.0-1.0
    authors: Optional[List[str]] = None
    published_date: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SerperClient:
    """Serper web search client"""
    
    def __init__(self, api_key: str):
        """
        Initialize Serper client
        
        Args:
            api_key: Serper API key
        """
        self.api_key = api_key
        self.base_url = "https://google.serper.dev"
        self.client: Optional[httpx.AsyncClient] = None
    
    async def init(self) -> None:
        """Initialize HTTP client"""
        try:
            self.client = httpx.AsyncClient(
                headers={"X-API-KEY": self.api_key},
                timeout=30,
            )
            logger.info("✓ Serper client initialized")
        except Exception as e:
            logger.error(f"✗ Failed to initialize Serper client: {e}")
            raise
    
    async def search(
        self,
        query: str,
        num_results: int = 10,
    ) -> List[SearchResult]:
        """
        Search using Serper API
        
        Args:
            query: Search query
            num_results: Number of results to return
            
        Returns:
            List of SearchResult objects
        """
        if not self.client:
            raise RuntimeError("Serper client not initialized")
        
        try:
            response = await self.client.post(
                f"{self.base_url}/search",
                json={
                    "q": query,
                    "num": min(num_results, 100),
                    "page": 1,
                }
            )
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            for item in data.get("organic", [])[:num_results]:
                result = SearchResult(
                    title=item.get("title", ""),
                    url=item.get("link", ""),
                    snippet=item.get("snippet", ""),
                    source="web",
                    relevance_score=0.8,  # Default score
                    metadata={"position": item.get("position")},
                )
                results.append(result)
            
            logger.info(f"✓ Serper search: {len(results)} results for '{query}'")
            return results
        
        except Exception as e:
            logger.error(f"✗ Serper search failed: {e}")
            raise
    
    async def close(self) -> None:
        """Close HTTP client"""
        if self.client:
            await self.client.aclose()


class GoogleSearchClient:
    """Google Custom Search client"""
    
    def __init__(self, api_key: str, search_engine_id: str):
        """
        Initialize Google Search client
        
        Args:
            api_key: Google API key
            search_engine_id: Custom search engine ID
        """
        self.api_key = api_key
        self.search_engine_id = search_engine_id
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        self.client: Optional[httpx.AsyncClient] = None
    
    async def init(self) -> None:
        """Initialize HTTP client"""
        try:
            self.client = httpx.AsyncClient(timeout=30)
            logger.info("✓ Google Search client initialized")
        except Exception as e:
            logger.error(f"✗ Failed to initialize Google Search client: {e}")
            raise
    
    async def search(
        self,
        query: str,
        num_results: int = 10,
    ) -> List[SearchResult]:
        """
        Search using Google Custom Search API
        
        Args:
            query: Search query
            num_results: Number of results to return
            
        Returns:
            List of SearchResult objects
        """
        if not self.client:
            raise RuntimeError("Google Search client not initialized")
        
        try:
            response = await self.client.get(
                self.base_url,
                params={
                    "key": self.api_key,
                    "cx": self.search_engine_id,
                    "q": query,
                    "num": min(num_results, 10),  # Max 10 per request
                }
            )
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            for item in data.get("items", [])[:num_results]:
                result = SearchResult(
                    title=item.get("title", ""),
                    url=item.get("link", ""),
                    snippet=item.get("snippet", ""),
                    source="web",
                    relevance_score=0.8,
                    metadata={"display_link": item.get("displayLink")},
                )
                results.append(result)
            
            logger.info(f"✓ Google Search: {len(results)} results for '{query}'")
            return results
        
        except Exception as e:
            logger.error(f"✗ Google Search failed: {e}")
            raise
    
    async def close(self) -> None:
        """Close HTTP client"""
        if self.client:
            await self.client.aclose()


class SemanticScholarClient:
    """Semantic Scholar academic search client"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Semantic Scholar client
        
        Args:
            api_key: Optional API key for higher rate limits
        """
        self.api_key = api_key
        self.base_url = "https://api.semanticscholar.org/graph/v1"
        self.client: Optional[httpx.AsyncClient] = None
    
    async def init(self) -> None:
        """Initialize HTTP client"""
        try:
            headers = {}
            if self.api_key:
                headers["x-api-key"] = self.api_key
            
            self.client = httpx.AsyncClient(
                headers=headers,
                timeout=30,
            )
            logger.info("✓ Semantic Scholar client initialized")
        except Exception as e:
            logger.error(f"✗ Failed to initialize Semantic Scholar client: {e}")
            raise
    
    async def search(
        self,
        query: str,
        num_results: int = 10,
        fields: Optional[str] = None,
    ) -> List[SearchResult]:
        """
        Search Semantic Scholar
        
        Args:
            query: Search query
            num_results: Number of results
            fields: Comma-separated fields to return
            
        Returns:
            List of SearchResult objects
        """
        if not self.client:
            raise RuntimeError("Semantic Scholar client not initialized")
        
        try:
            fields = fields or "paperId,title,abstract,year,citationCount,authors,openAccessPdf"
            
            response = await self.client.get(
                f"{self.base_url}/paper/search",
                params={
                    "query": query,
                    "limit": min(num_results, 100),
                    "fields": fields,
                }
            )
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            for paper in data.get("data", [])[:num_results]:
                # Calculate relevance based on citation count
                citations = paper.get("citationCount", 0)
                relevance_score = min(1.0, citations / 1000.0)  # Normalize by citation count
                
                authors = [
                    author.get("name", "")
                    for author in paper.get("authors", [])
                ]
                
                url = ""
                if paper.get("openAccessPdf"):
                    url = paper["openAccessPdf"].get("url", "")
                
                result = SearchResult(
                    title=paper.get("title", ""),
                    url=url,
                    snippet=paper.get("abstract", "")[:500],
                    source="academic",
                    relevance_score=relevance_score,
                    authors=authors[:3],  # Top 3 authors
                    published_date=str(paper.get("year", "")),
                    metadata={
                        "paper_id": paper.get("paperId"),
                        "citation_count": citations,
                        "venue": paper.get("venue"),
                    }
                )
                results.append(result)
            
            logger.info(f"✓ Semantic Scholar: {len(results)} results for '{query}'")
            return results
        
        except Exception as e:
            logger.error(f"✗ Semantic Scholar search failed: {e}")
            raise
    
    async def close(self) -> None:
        """Close HTTP client"""
        if self.client:
            await self.client.aclose()


class COREClient:
    """CORE academic repository client"""
    
    def __init__(self, api_key: str):
        """
        Initialize CORE client
        
        Args:
            api_key: CORE API key
        """
        self.api_key = api_key
        self.base_url = "https://core.ac.uk/api/v3"
        self.client: Optional[httpx.AsyncClient] = None
    
    async def init(self) -> None:
        """Initialize HTTP client"""
        try:
            self.client = httpx.AsyncClient(timeout=30)
            logger.info("✓ CORE client initialized")
        except Exception as e:
            logger.error(f"✗ Failed to initialize CORE client: {e}")
            raise
    
    async def search(
        self,
        query: str,
        num_results: int = 10,
    ) -> List[SearchResult]:
        """
        Search CORE repository
        
        Args:
            query: Search query
            num_results: Number of results
            
        Returns:
            List of SearchResult objects
        """
        if not self.client:
            raise RuntimeError("CORE client not initialized")
        
        try:
            # CORE API query format
            response = await self.client.post(
                f"{self.base_url}/search/works",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "query": query,
                    "limit": min(num_results, 100),
                    "sort": "-citationCount",  # Sort by citations
                }
            )
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            for work in data.get("results", [])[:num_results]:
                result = SearchResult(
                    title=work.get("title", ""),
                    url=work.get("downloadUrl") or work.get("sourceUrl", ""),
                    snippet=work.get("abstract", "")[:500],
                    source="core",
                    relevance_score=0.8,
                    authors=[
                        author.get("name", "")
                        for author in work.get("authors", [])[:3]
                    ],
                    published_date=work.get("publishedDate"),
                    metadata={
                        "core_id": work.get("id"),
                        "citation_count": work.get("citationCount"),
                        "repositories": work.get("repositories", []),
                    }
                )
                results.append(result)
            
            logger.info(f"✓ CORE search: {len(results)} results for '{query}'")
            return results
        
        except Exception as e:
            logger.error(f"✗ CORE search failed: {e}")
            raise
    
    async def close(self) -> None:
        """Close HTTP client"""
        if self.client:
            await self.client.aclose()


# Global client instances
_serper_client: Optional[SerperClient] = None
_google_search_client: Optional[GoogleSearchClient] = None
_semantic_scholar_client: Optional[SemanticScholarClient] = None
_core_client: Optional[COREClient] = None


async def init_search_clients(
    serper_api_key: Optional[str] = None,
    google_api_key: Optional[str] = None,
    google_search_engine_id: Optional[str] = None,
    semantic_scholar_api_key: Optional[str] = None,
    core_api_key: Optional[str] = None,
) -> None:
    """Initialize all search clients"""
    global _serper_client, _google_search_client, _semantic_scholar_client, _core_client
    
    if serper_api_key:
        _serper_client = SerperClient(serper_api_key)
        await _serper_client.init()
    
    if google_api_key and google_search_engine_id:
        _google_search_client = GoogleSearchClient(google_api_key, google_search_engine_id)
        await _google_search_client.init()
    
    if semantic_scholar_api_key:
        _semantic_scholar_client = SemanticScholarClient(semantic_scholar_api_key)
        await _semantic_scholar_client.init()
    
    if core_api_key:
        _core_client = COREClient(core_api_key)
        await _core_client.init()


async def close_search_clients() -> None:
    """Close all search clients"""
    global _serper_client, _google_search_client, _semantic_scholar_client, _core_client
    
    if _serper_client:
        await _serper_client.close()
        _serper_client = None
    
    if _google_search_client:
        await _google_search_client.close()
        _google_search_client = None
    
    if _semantic_scholar_client:
        await _semantic_scholar_client.close()
        _semantic_scholar_client = None
    
    if _core_client:
        await _core_client.close()
        _core_client = None


def get_serper_client() -> Optional[SerperClient]:
    """Get Serper client"""
    return _serper_client


def get_google_search_client() -> Optional[GoogleSearchClient]:
    """Get Google Search client"""
    return _google_search_client


def get_semantic_scholar_client() -> Optional[SemanticScholarClient]:
    """Get Semantic Scholar client"""
    return _semantic_scholar_client


def get_core_client() -> Optional[COREClient]:
    """Get CORE client"""
    return _core_client
