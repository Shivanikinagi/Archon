"""Embedding service for generating document embeddings

Provides high-level embedding operations for RAG system.
"""

import logging
from typing import List, Optional
from integration.ollama_client import get_ollama_client
from integration.chromadb_client import get_chromadb_client

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating and managing embeddings"""
    
    def __init__(
        self,
        embedding_model: str = "nomic-embed-text",
        batch_size: int = 10,
    ):
        """
        Initialize embedding service
        
        Args:
            embedding_model: Model to use for embeddings
            batch_size: Batch size for processing chunks
        """
        self.embedding_model = embedding_model
        self.batch_size = batch_size
    
    async def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for single text
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector (384-dimensional)
            
        Raises:
            Exception: If embedding fails
        """
        try:
            ollama = get_ollama_client()
            embedding = await ollama.embeddings(text, self.embedding_model)
            logger.debug(f"✓ Embedded text with {len(embedding)} dimensions")
            return embedding
        except Exception as e:
            logger.error(f"✗ Failed to embed text: {e}")
            raise
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
            
        Raises:
            Exception: If embedding fails
        """
        try:
            embeddings = []
            
            # Process in batches
            for i in range(0, len(texts), self.batch_size):
                batch = texts[i : i + self.batch_size]
                batch_embeddings = []
                
                for text in batch:
                    embedding = await self.embed_text(text)
                    batch_embeddings.append(embedding)
                
                embeddings.extend(batch_embeddings)
                logger.debug(f"✓ Embedded batch {i // self.batch_size + 1} of {(len(texts) - 1) // self.batch_size + 1}")
            
            logger.info(f"✓ Embedded {len(texts)} texts")
            return embeddings
        
        except Exception as e:
            logger.error(f"✗ Failed to embed texts: {e}")
            raise
    
    async def index_documents(
        self,
        documents: List[str],
        ids: List[str],
        metadatas: Optional[List[dict]] = None,
    ) -> bool:
        """
        Generate embeddings and index documents in ChromaDB
        
        Args:
            documents: List of document texts
            ids: List of document IDs
            metadatas: Optional metadata for documents
            
        Returns:
            Success flag
            
        Raises:
            Exception: If indexing fails
        """
        try:
            if len(documents) != len(ids):
                raise ValueError("documents and ids must have same length")
            
            # Generate embeddings
            logger.info(f"Generating embeddings for {len(documents)} documents...")
            embeddings = await self.embed_texts(documents)
            
            # Index in ChromaDB
            logger.info(f"Indexing documents in ChromaDB...")
            chromadb = get_chromadb_client()
            await chromadb.add_documents(
                documents=documents,
                embeddings=embeddings,
                ids=ids,
                metadatas=metadatas,
            )
            
            logger.info(f"✓ Successfully indexed {len(documents)} documents")
            return True
        
        except Exception as e:
            logger.error(f"✗ Failed to index documents: {e}")
            raise
    
    async def index_chunks(
        self,
        chunks: List[str],
        chunk_ids: List[str],
        document_id: str,
        metadatas: Optional[List[dict]] = None,
    ) -> bool:
        """
        Generate embeddings and index document chunks for RAG
        
        Args:
            chunks: List of text chunks
            chunk_ids: List of chunk IDs
            document_id: ID of parent document
            metadatas: Optional metadata for chunks
            
        Returns:
            Success flag
            
        Raises:
            Exception: If indexing fails
        """
        try:
            if len(chunks) != len(chunk_ids):
                raise ValueError("chunks and chunk_ids must have same length")
            
            # Add document_id to metadata
            if metadatas is None:
                metadatas = []
            
            for i, meta in enumerate(metadatas if metadatas else [{}] * len(chunks)):
                if not meta:
                    meta = {}
                meta["document_id"] = document_id
                if i < len(metadatas):
                    metadatas[i] = meta
                else:
                    metadatas.append(meta)
            
            # Generate embeddings
            logger.info(f"Generating embeddings for {len(chunks)} chunks from document {document_id}...")
            embeddings = await self.embed_texts(chunks)
            
            # Index in ChromaDB
            logger.info(f"Indexing chunks in ChromaDB...")
            chromadb = get_chromadb_client()
            await chromadb.add_documents(
                documents=chunks,
                embeddings=embeddings,
                ids=chunk_ids,
                metadatas=metadatas,
            )
            
            logger.info(f"✓ Successfully indexed {len(chunks)} chunks from document {document_id}")
            return True
        
        except Exception as e:
            logger.error(f"✗ Failed to index chunks: {e}")
            raise
    
    async def search_similar(
        self,
        query: str,
        top_k: int = 5,
    ) -> dict:
        """
        Search for similar documents using semantic search
        
        Args:
            query: Query text
            top_k: Number of results to return
            
        Returns:
            Search results with documents, metadata, and similarity scores
            
        Raises:
            Exception: If search fails
        """
        try:
            # Generate query embedding
            logger.debug(f"Generating embedding for query: {query[:50]}...")
            query_embedding = await self.embed_text(query)
            
            # Search in ChromaDB
            logger.debug(f"Searching for top {top_k} similar documents...")
            chromadb = get_chromadb_client()
            results = await chromadb.search(query_embedding, top_k=top_k)
            
            # Format results
            formatted_results = {
                "query": query,
                "results": []
            }
            
            if results and results.get("ids") and len(results["ids"]) > 0:
                ids = results["ids"][0]
                documents = results.get("documents", [[]])[0] if results.get("documents") else []
                distances = results.get("distances", [[]])[0] if results.get("distances") else []
                metadatas = results.get("metadatas", [[]])[0] if results.get("metadatas") else []
                
                for i, doc_id in enumerate(ids):
                    formatted_results["results"].append({
                        "id": doc_id,
                        "document": documents[i] if i < len(documents) else "",
                        "similarity": 1 - (distances[i] if i < len(distances) else 0),  # Convert distance to similarity
                        "metadata": metadatas[i] if i < len(metadatas) else {},
                    })
            
            logger.info(f"✓ Found {len(formatted_results['results'])} similar documents")
            return formatted_results
        
        except Exception as e:
            logger.error(f"✗ Search failed: {e}")
            raise
    
    async def rerank_results(
        self,
        query: str,
        documents: List[str],
        top_k: Optional[int] = None,
    ) -> List[tuple]:
        """
        Rerank search results by semantic relevance
        
        Args:
            query: Query text
            documents: List of documents to rerank
            top_k: Optional limit on results
            
        Returns:
            List of (document, similarity_score) tuples, sorted by relevance
            
        Raises:
            Exception: If reranking fails
        """
        try:
            # Generate embeddings
            query_embedding = await self.embed_text(query)
            doc_embeddings = await self.embed_texts(documents)
            
            # Calculate cosine similarity
            import numpy as np
            
            similarities = []
            query_vec = np.array(query_embedding)
            
            for i, doc_embedding in enumerate(doc_embeddings):
                doc_vec = np.array(doc_embedding)
                
                # Cosine similarity
                similarity = np.dot(query_vec, doc_vec) / (
                    np.linalg.norm(query_vec) * np.linalg.norm(doc_vec)
                )
                similarities.append((documents[i], float(similarity)))
            
            # Sort by similarity descending
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            # Apply top_k if specified
            if top_k:
                similarities = similarities[:top_k]
            
            logger.info(f"✓ Reranked {len(documents)} documents, top result: {similarities[0][1]:.3f}")
            return similarities
        
        except Exception as e:
            logger.error(f"✗ Reranking failed: {e}")
            raise
