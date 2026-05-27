"""Retrieval service for multi-stage RAG

Implements BM25 + semantic search hybrid retrieval and ranking.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
from src.integration.search_clients import SearchResult
from src.services.embedding_service import EmbeddingService
import re

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """Result from RAG retrieval"""
    content: str
    source: str  # "indexed", "web", "academic"
    relevance_score: float  # 0.0-1.0
    metadata: Dict[str, Any]


class BM25Scorer:
    """BM25 scoring for document retrieval"""
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        Initialize BM25 scorer
        
        Args:
            k1: Term frequency saturation parameter
            b: Length normalization parameter
        """
        self.k1 = k1
        self.b = b
        self.documents = []
        self.doc_freqs = {}
        self.idf_cache = {}
    
    def add_documents(self, documents: List[str]) -> None:
        """
        Add documents to corpus
        
        Args:
            documents: List of document texts
        """
        self.documents = documents
        self._compute_idf()
    
    def _compute_idf(self) -> None:
        """Compute IDF scores for all terms"""
        self.doc_freqs = {}
        self.idf_cache = {}
        
        for doc in self.documents:
            terms = self._tokenize(doc)
            seen_terms = set(terms)
            
            for term in seen_terms:
                self.doc_freqs[term] = self.doc_freqs.get(term, 0) + 1
        
        # Compute IDF
        num_docs = len(self.documents)
        for term in self.doc_freqs:
            self.idf_cache[term] = self._idf(term, num_docs)
    
    def _idf(self, term: str, num_docs: int) -> float:
        """Compute IDF for a term"""
        if term not in self.doc_freqs:
            return 0.0
        
        df = self.doc_freqs[term]
        return (num_docs - df + 0.5) / (df + 0.5)
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text"""
        # Simple tokenization: split on whitespace and punctuation
        tokens = re.findall(r'\b\w+\b', text.lower())
        return tokens
    
    def score(self, query: str, doc_index: int) -> float:
        """
        Score document using BM25
        
        Args:
            query: Query text
            doc_index: Document index
            
        Returns:
            BM25 score
        """
        if doc_index >= len(self.documents):
            return 0.0
        
        doc = self.documents[doc_index]
        doc_tokens = self._tokenize(doc)
        query_tokens = self._tokenize(query)
        
        doc_length = len(doc_tokens)
        avg_length = sum(len(self._tokenize(d)) for d in self.documents) / max(1, len(self.documents))
        
        score = 0.0
        for term in query_tokens:
            term_freq = doc_tokens.count(term)
            idf = self.idf_cache.get(term, 0.0)
            
            # BM25 formula
            numerator = idf * term_freq * (self.k1 + 1)
            denominator = term_freq + self.k1 * (1 - self.b + self.b * (doc_length / avg_length))
            
            score += numerator / denominator
        
        return score
    
    def rank_documents(self, query: str) -> List[Tuple[int, float]]:
        """
        Rank documents by BM25 score
        
        Args:
            query: Query text
            
        Returns:
            List of (doc_index, score) tuples, sorted by score
        """
        scores = []
        for i in range(len(self.documents)):
            score = self.score(query, i)
            if score > 0:
                scores.append((i, score))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores


class RetrievalService:
    """Multi-stage RAG retrieval combining BM25 and semantic search"""
    
    def __init__(
        self,
        embedding_service: Optional[EmbeddingService] = None,
        use_bm25: bool = True,
        use_semantic: bool = True,
    ):
        """
        Initialize retrieval service
        
        Args:
            embedding_service: EmbeddingService for semantic search
            use_bm25: Enable BM25 retrieval
            use_semantic: Enable semantic search
        """
        self.embedding_service = embedding_service
        self.use_bm25 = use_bm25
        self.use_semantic = use_semantic
        self.bm25 = BM25Scorer()
    
    async def retrieve(
        self,
        query: str,
        indexed_documents: Optional[List[str]] = None,
        web_results: Optional[List[SearchResult]] = None,
        academic_results: Optional[List[SearchResult]] = None,
        top_k: int = 10,
        use_bm25: Optional[bool] = None,
        use_semantic: Optional[bool] = None,
    ) -> List[RetrievalResult]:
        """
        Retrieve documents using multi-stage retrieval
        
        Args:
            query: Search query
            indexed_documents: Pre-indexed documents
            web_results: Web search results
            academic_results: Academic search results
            top_k: Number of top results to return
            use_bm25: Override default BM25 setting
            use_semantic: Override default semantic setting
            
        Returns:
            List of RetrievalResult objects
        """
        use_bm25 = use_bm25 if use_bm25 is not None else self.use_bm25
        use_semantic = use_semantic if use_semantic is not None else self.use_semantic
        
        try:
            candidates = []
            
            # BM25 retrieval from indexed documents
            if use_bm25 and indexed_documents:
                candidates.extend(
                    await self._bm25_retrieve(query, indexed_documents, top_k)
                )
            
            # Semantic search from indexed documents
            if use_semantic and self.embedding_service and indexed_documents:
                candidates.extend(
                    await self._semantic_retrieve(query, indexed_documents, top_k)
                )
            
            # Add web results
            if web_results:
                for result in web_results[:top_k]:
                    candidates.append(
                        RetrievalResult(
                            content=result.snippet,
                            source="web",
                            relevance_score=result.relevance_score,
                            metadata={
                                "title": result.title,
                                "url": result.url,
                                "snippet": result.snippet,
                            }
                        )
                    )
            
            # Add academic results
            if academic_results:
                for result in academic_results[:top_k]:
                    candidates.append(
                        RetrievalResult(
                            content=result.snippet,
                            source="academic",
                            relevance_score=result.relevance_score,
                            metadata={
                                "title": result.title,
                                "url": result.url,
                                "authors": result.authors,
                                "published_date": result.published_date,
                            }
                        )
                    )
            
            # Deduplicate by content
            candidates = self._deduplicate(candidates)
            
            # Rank and return top-k
            candidates.sort(key=lambda x: x.relevance_score, reverse=True)
            result = candidates[:top_k]
            
            logger.info(f"✓ Retrieved {len(result)} results for query: {query}")
            return result
        
        except Exception as e:
            logger.error(f"✗ Retrieval failed: {e}")
            raise
    
    async def _bm25_retrieve(
        self,
        query: str,
        documents: List[str],
        top_k: int,
    ) -> List[RetrievalResult]:
        """
        BM25 retrieval
        
        Args:
            query: Query text
            documents: Documents to search
            top_k: Number of top results
            
        Returns:
            RetrievalResult list
        """
        try:
            self.bm25.add_documents(documents)
            ranked = self.bm25.rank_documents(query)
            
            results = []
            for doc_idx, score in ranked[:top_k]:
                # Normalize score to 0-1
                normalized_score = min(1.0, score / 10.0)  # Rough normalization
                
                results.append(
                    RetrievalResult(
                        content=documents[doc_idx],
                        source="indexed",
                        relevance_score=normalized_score,
                        metadata={"retrieval_method": "bm25"},
                    )
                )
            
            logger.debug(f"BM25 retrieved {len(results)} results")
            return results
        
        except Exception as e:
            logger.error(f"✗ BM25 retrieval failed: {e}")
            return []
    
    async def _semantic_retrieve(
        self,
        query: str,
        documents: List[str],
        top_k: int,
    ) -> List[RetrievalResult]:
        """
        Semantic search retrieval
        
        Args:
            query: Query text
            documents: Documents to search
            top_k: Number of top results
            
        Returns:
            RetrievalResult list
        """
        try:
            if not self.embedding_service:
                return []
            
            # Rerank documents by semantic similarity
            reranked = await self.embedding_service.rerank_results(
                query=query,
                documents=documents,
                top_k=top_k,
            )
            
            results = []
            for doc_text, score in reranked:
                results.append(
                    RetrievalResult(
                        content=doc_text,
                        source="indexed",
                        relevance_score=score,
                        metadata={"retrieval_method": "semantic"},
                    )
                )
            
            logger.debug(f"Semantic search retrieved {len(results)} results")
            return results
        
        except Exception as e:
            logger.error(f"✗ Semantic retrieval failed: {e}")
            return []
    
    def _deduplicate(self, results: List[RetrievalResult]) -> List[RetrievalResult]:
        """
        Deduplicate results by content similarity
        
        Args:
            results: Results to deduplicate
            
        Returns:
            Deduplicated results
        """
        seen_content = set()
        deduplicated = []
        
        for result in results:
            # Simple deduplication by exact content match
            content_hash = hash(result.content[:100])  # Hash first 100 chars
            
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                deduplicated.append(result)
        
        return deduplicated
    
    def format_context(
        self,
        results: List[RetrievalResult],
        max_length: int = 4000,
        include_metadata: bool = True,
    ) -> str:
        """
        Format retrieval results into context for LLM
        
        Args:
            results: RetrievalResult list
            max_length: Maximum context length
            include_metadata: Include source metadata
            
        Returns:
            Formatted context string
        """
        context = "Retrieved Context:\n\n"
        current_length = len(context)
        
        for i, result in enumerate(results, 1):
            # Add metadata header
            if include_metadata:
                header = f"[Source {i} - {result.source.upper()} (Score: {result.relevance_score:.2f})]\n"
                if result.metadata.get("title"):
                    header += f"Title: {result.metadata['title']}\n"
                if result.metadata.get("url"):
                    header += f"URL: {result.metadata['url']}\n"
                header += "\n"
            else:
                header = f"[Source {i}]\n"
            
            # Add content
            content = result.content + "\n\n"
            
            # Check length
            total_addition = len(header) + len(content)
            if current_length + total_addition > max_length:
                context += "\n[... truncated due to length limit]"
                break
            
            context += header + content
            current_length += total_addition
        
        return context
