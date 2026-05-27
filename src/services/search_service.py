"""Search service for multi-source research

Combines web search, academic search, and result aggregation.
"""

import logging
from typing import List, Optional, Dict, Any
from integration.search_clients import (
    SearchResult,
    get_serper_client,
    get_google_search_client,
    get_semantic_scholar_client,
    get_core_client,
)

logger = logging.getLogger(__name__)


class SearchService:
    """High-level search service combining multiple sources"""
    
    def __init__(self):
        """Initialize search service"""
        self.default_num_results = 10
    
    async def web_search(
        self,
        query: str,
        num_results: int = 10,
        provider: str = "serper",
    ) -> List[SearchResult]:
        """
        Perform web search
        
        Args:
            query: Search query
            num_results: Number of results
            provider: Search provider ("serper" or "google")
            
        Returns:
            List of search results
        """
        try:
            if provider == "serper":
                client = get_serper_client()
                if not client:
                    logger.warning("Serper client not initialized")
                    return []
                return await client.search(query, num_results)
            
            elif provider == "google":
                client = get_google_search_client()
                if not client:
                    logger.warning("Google Search client not initialized")
                    return []
                return await client.search(query, num_results)
            
            else:
                raise ValueError(f"Unknown web search provider: {provider}")
        
        except Exception as e:
            logger.error(f"✗ Web search failed: {e}")
            raise
    
    async def academic_search(
        self,
        query: str,
        num_results: int = 10,
        provider: str = "semantic_scholar",
    ) -> List[SearchResult]:
        """
        Perform academic search
        
        Args:
            query: Search query
            num_results: Number of results
            provider: Search provider ("semantic_scholar" or "core")
            
        Returns:
            List of academic search results
        """
        try:
            if provider == "semantic_scholar":
                client = get_semantic_scholar_client()
                if not client:
                    logger.warning("Semantic Scholar client not initialized")
                    return []
                return await client.search(query, num_results)
            
            elif provider == "core":
                client = get_core_client()
                if not client:
                    logger.warning("CORE client not initialized")
                    return []
                return await client.search(query, num_results)
            
            else:
                raise ValueError(f"Unknown academic search provider: {provider}")
        
        except Exception as e:
            logger.error(f"✗ Academic search failed: {e}")
            raise
    
    async def multi_source_search(
        self,
        query: str,
        web_providers: Optional[List[str]] = None,
        academic_providers: Optional[List[str]] = None,
        num_results: int = 10,
    ) -> Dict[str, List[SearchResult]]:
        """
        Search across multiple sources
        
        Args:
            query: Search query
            web_providers: Web search providers ("serper", "google")
            academic_providers: Academic search providers ("semantic_scholar", "core")
            num_results: Results per provider
            
        Returns:
            Dictionary with results by source type
        """
        web_providers = web_providers or ["serper"]
        academic_providers = academic_providers or ["semantic_scholar"]
        
        results = {
            "web": [],
            "academic": [],
        }
        
        try:
            # Web search
            for provider in web_providers:
                try:
                    web_results = await self.web_search(query, num_results, provider)
                    results["web"].extend(web_results)
                except Exception as e:
                    logger.warning(f"Web search ({provider}) failed: {e}")
            
            # Academic search
            for provider in academic_providers:
                try:
                    academic_results = await self.academic_search(query, num_results, provider)
                    results["academic"].extend(academic_results)
                except Exception as e:
                    logger.warning(f"Academic search ({provider}) failed: {e}")
            
            # Deduplicate by URL
            results["web"] = self._deduplicate_results(results["web"])
            results["academic"] = self._deduplicate_results(results["academic"])
            
            logger.info(
                f"✓ Multi-source search complete: {len(results['web'])} web + "
                f"{len(results['academic'])} academic results"
            )
            return results
        
        except Exception as e:
            logger.error(f"✗ Multi-source search failed: {e}")
            raise
    
    def _deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """
        Deduplicate search results by URL
        
        Args:
            results: List of search results
            
        Returns:
            Deduplicated results
        """
        seen_urls = set()
        deduplicated = []
        
        for result in results:
            if result.url and result.url not in seen_urls:
                seen_urls.add(result.url)
                deduplicated.append(result)
            elif not result.url:
                # Include results without URL (can't deduplicate)
                deduplicated.append(result)
        
        return deduplicated
    
    def rank_results(
        self,
        results: List[SearchResult],
        query: str,
        boost_academic: bool = False,
    ) -> List[SearchResult]:
        """
        Rank search results by relevance
        
        Args:
            results: Search results to rank
            query: Original query for relevance calculation
            boost_academic: Boost academic papers in ranking
            
        Returns:
            Ranked results
        """
        try:
            ranked = results.copy()
            
            # Score based on:
            # 1. Title relevance
            # 2. Existing relevance score
            # 3. Source type (if boost_academic)
            
            query_words = set(query.lower().split())
            
            for result in ranked:
                # Title word match score
                title_words = set(result.title.lower().split())
                title_match = len(query_words & title_words) / len(query_words)
                
                # Combined relevance
                relevance = result.relevance_score
                relevance += title_match * 0.3  # Boost for title match
                
                if boost_academic and result.source == "academic":
                    relevance *= 1.2  # 20% boost for academic sources
                
                # Normalize to 0-1
                result.relevance_score = min(1.0, relevance)
            
            # Sort by relevance descending
            ranked.sort(key=lambda r: r.relevance_score, reverse=True)
            
            logger.debug(f"Ranked {len(ranked)} results for query: {query}")
            return ranked
        
        except Exception as e:
            logger.error(f"✗ Result ranking failed: {e}")
            raise
    
    def merge_and_rank(
        self,
        web_results: List[SearchResult],
        academic_results: List[SearchResult],
        total_limit: int = 20,
        academic_weight: float = 0.6,
    ) -> List[SearchResult]:
        """
        Merge and rank web and academic results
        
        Args:
            web_results: Web search results
            academic_results: Academic search results
            total_limit: Maximum results to return
            academic_weight: Weight for academic results (0.0-1.0)
            
        Returns:
            Merged and ranked results
        """
        try:
            # Merge all results
            all_results = web_results + academic_results
            
            # Adjust scores based on weight
            for result in all_results:
                if result.source == "academic":
                    result.relevance_score *= academic_weight
                else:
                    result.relevance_score *= (1.0 - academic_weight)
            
            # Sort by relevance
            all_results.sort(key=lambda r: r.relevance_score, reverse=True)
            
            # Return top results
            merged = all_results[:total_limit]
            
            logger.info(
                f"✓ Merged {len(web_results)} web + {len(academic_results)} academic "
                f"results, returned top {len(merged)}"
            )
            return merged
        
        except Exception as e:
            logger.error(f"✗ Merge and rank failed: {e}")
            raise
    
    async def search_with_fallback(
        self,
        query: str,
        primary_sources: Optional[List[str]] = None,
        fallback_sources: Optional[List[str]] = None,
        num_results: int = 10,
    ) -> List[SearchResult]:
        """
        Search with fallback to other sources if primary fails
        
        Args:
            query: Search query
            primary_sources: Primary search sources to try first
            fallback_sources: Fallback sources if primary fails
            num_results: Number of results
            
        Returns:
            Search results
        """
        primary_sources = primary_sources or ["serper"]
        fallback_sources = fallback_sources or ["google"]
        
        all_sources = primary_sources + fallback_sources
        results = []
        
        try:
            # Try each source until we get results
            for source in all_sources:
                try:
                    if source in ["serper", "google"]:
                        results = await self.web_search(query, num_results, source)
                    elif source in ["semantic_scholar", "core"]:
                        results = await self.academic_search(query, num_results, source)
                    
                    if results:
                        logger.info(f"✓ Search succeeded with {source}")
                        return results
                
                except Exception as e:
                    logger.warning(f"Search with {source} failed: {e}, trying next source")
                    continue
            
            logger.warning(f"✗ Search failed for all sources")
            return []
        
        except Exception as e:
            logger.error(f"✗ Search with fallback failed: {e}")
            raise
