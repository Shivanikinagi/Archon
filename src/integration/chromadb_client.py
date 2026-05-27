"""ChromaDB vector store integration

Provides vector storage and similarity search capabilities for RAG system.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
import numpy as np

logger = logging.getLogger(__name__)


class ChromaDBClient:
    """ChromaDB client for vector storage and retrieval"""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 8000,
        collection_name: str = "research_documents",
        embedding_dim: int = 384,
    ):
        """
        Initialize ChromaDB client
        
        Args:
            host: ChromaDB server host
            port: ChromaDB server port
            collection_name: Default collection name
            embedding_dim: Embedding dimension (for nomic-embed-text: 384)
        """
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.embedding_dim = embedding_dim
        self.client = None
        self.collection = None
    
    async def init(self) -> None:
        """
        Initialize connection to ChromaDB
        
        Raises:
            Exception: If connection fails
        """
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._sync_init)
            logger.info(f"✓ ChromaDB client initialized (host={self.host}:{self.port})")
        except Exception as e:
            logger.error(f"✗ Failed to initialize ChromaDB: {e}")
            raise
    
    def _sync_init(self) -> None:
        """Synchronous initialization (runs in executor)"""
        self.client = chromadb.HttpClient(
            host=self.host,
            port=self.port,
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={
                "hnsw:space": "cosine",
                "description": "Vector storage for research documents",
            }
        )
    
    async def add_documents(
        self,
        documents: List[str],
        embeddings: List[List[float]],
        ids: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """
        Add documents with embeddings to collection
        
        Args:
            documents: List of document texts
            embeddings: List of embedding vectors
            ids: List of document IDs
            metadatas: Optional metadata dictionaries
            
        Raises:
            ValueError: If data validation fails
        """
        if len(documents) != len(embeddings) or len(documents) != len(ids):
            raise ValueError("documents, embeddings, and ids must have same length")
        
        if embeddings and len(embeddings[0]) != self.embedding_dim:
            raise ValueError(f"Embedding dimension mismatch: expected {self.embedding_dim}, got {len(embeddings[0])}")
        
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._sync_add_documents,
                documents, embeddings, ids, metadatas
            )
            logger.info(f"✓ Added {len(documents)} documents to ChromaDB")
        except Exception as e:
            logger.error(f"✗ Failed to add documents: {e}")
            raise
    
    def _sync_add_documents(
        self,
        documents: List[str],
        embeddings: List[List[float]],
        ids: List[str],
        metadatas: Optional[List[Dict[str, Any]]],
    ) -> None:
        """Synchronous add (runs in executor)"""
        self.collection.add(
            embeddings=embeddings,
            documents=documents,
            ids=ids,
            metadatas=metadatas or [{"source": "unknown"} for _ in ids],
        )
    
    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """
        Search for similar documents
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            
        Returns:
            Search results with documents, embeddings, distances, metadatas, ids
        """
        if len(query_embedding) != self.embedding_dim:
            raise ValueError(f"Query embedding dimension mismatch: expected {self.embedding_dim}, got {len(query_embedding)}")
        
        try:
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                self._sync_search,
                query_embedding, top_k
            )
            logger.debug(f"✓ Found {len(results['ids'][0]) if results['ids'] else 0} results")
            return results
        except Exception as e:
            logger.error(f"✗ Search failed: {e}")
            raise
    
    def _sync_search(
        self,
        query_embedding: List[float],
        top_k: int,
    ) -> Dict[str, Any]:
        """Synchronous search (runs in executor)"""
        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["embeddings", "documents", "distances", "metadatas"]
        )
    
    async def delete_documents(self, ids: List[str]) -> None:
        """
        Delete documents by IDs
        
        Args:
            ids: List of document IDs to delete
        """
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._sync_delete, ids)
            logger.info(f"✓ Deleted {len(ids)} documents from ChromaDB")
        except Exception as e:
            logger.error(f"✗ Failed to delete documents: {e}")
            raise
    
    def _sync_delete(self, ids: List[str]) -> None:
        """Synchronous delete (runs in executor)"""
        self.collection.delete(ids=ids)
    
    async def get_collection_info(self) -> Dict[str, Any]:
        """
        Get collection metadata and stats
        
        Returns:
            Collection information
        """
        try:
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(None, self._sync_get_info)
            return info
        except Exception as e:
            logger.error(f"✗ Failed to get collection info: {e}")
            raise
    
    def _sync_get_info(self) -> Dict[str, Any]:
        """Synchronous get info (runs in executor)"""
        count = self.collection.count()
        return {
            "collection_name": self.collection_name,
            "document_count": count,
            "embedding_dim": self.embedding_dim,
        }
    
    async def close(self) -> None:
        """Close ChromaDB connection"""
        try:
            if self.client:
                # ChromaDB HttpClient doesn't need explicit close
                self.client = None
                self.collection = None
                logger.info("✓ ChromaDB connection closed")
        except Exception as e:
            logger.error(f"✗ Failed to close ChromaDB connection: {e}")
            raise


# Global ChromaDB client instance
_chromadb_client: Optional[ChromaDBClient] = None


async def init_chromadb(
    host: str = "localhost",
    port: int = 8000,
    collection_name: str = "research_documents",
    embedding_dim: int = 384,
) -> None:
    """
    Initialize global ChromaDB client
    
    Args:
        host: ChromaDB server host
        port: ChromaDB server port
        collection_name: Collection name
        embedding_dim: Embedding dimension
    """
    global _chromadb_client
    _chromadb_client = ChromaDBClient(
        host=host,
        port=port,
        collection_name=collection_name,
        embedding_dim=embedding_dim,
    )
    await _chromadb_client.init()


async def close_chromadb() -> None:
    """Close global ChromaDB client"""
    global _chromadb_client
    if _chromadb_client:
        await _chromadb_client.close()
        _chromadb_client = None


def get_chromadb_client() -> ChromaDBClient:
    """Get global ChromaDB client"""
    if _chromadb_client is None:
        raise RuntimeError("ChromaDB client not initialized. Call init_chromadb() first.")
    return _chromadb_client
