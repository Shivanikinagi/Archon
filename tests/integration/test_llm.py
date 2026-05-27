"""Integration tests for LLM operations

Tests Ollama client, embedding service, and LLM service.
"""

import pytest
import asyncio
from typing import AsyncGenerator

# These tests assume Ollama is running with necessary models
# docker-compose -f docker-compose.dev.yml up -d
# ollama pull mistral
# ollama pull nomic-embed-text


@pytest.fixture
async def ollama_client():
    """Ollama client fixture"""
    from integration.ollama_client import OllamaClient
    
    client = OllamaClient(
        base_url="http://localhost:11434",
        model="mistral",
        timeout=300,
    )
    await client.init()
    yield client
    await client.close()


@pytest.fixture
async def embedding_service():
    """Embedding service fixture"""
    from services.embedding_service import EmbeddingService
    
    return EmbeddingService(embedding_model="nomic-embed-text")


@pytest.fixture
async def llm_service():
    """LLM service fixture"""
    from services.llm_service import LLMService
    
    return LLMService(model="mistral")


class TestOllamaClient:
    """Ollama client integration tests"""
    
    @pytest.mark.asyncio
    async def test_ollama_connection(self, ollama_client):
        """Test Ollama connection"""
        models = await ollama_client.list_models()
        assert models is not None
        assert len(models) > 0
    
    @pytest.mark.asyncio
    async def test_text_generation(self, ollama_client):
        """Test text generation"""
        prompt = "Write a short haiku about AI."
        response = await ollama_client.generate(prompt, temperature=0.5)
        
        assert response is not None
        assert len(response) > 0
        assert "AI" in response or "ai" in response.lower()
    
    @pytest.mark.asyncio
    async def test_embedding_generation(self, ollama_client):
        """Test embedding generation"""
        text = "This is a test sentence for embedding."
        embedding = await ollama_client.embeddings(text)
        
        assert embedding is not None
        assert len(embedding) == 384  # nomic-embed-text dimension
        assert all(isinstance(x, (int, float)) for x in embedding)
    
    @pytest.mark.asyncio
    async def test_model_info(self, ollama_client):
        """Test getting model information"""
        info = await ollama_client.model_info()
        
        assert info is not None
        assert "name" in info or "model" in info


class TestEmbeddingService:
    """Embedding service integration tests"""
    
    @pytest.mark.asyncio
    async def test_embed_single_text(self, embedding_service):
        """Test embedding single text"""
        text = "This is a test document for embedding."
        embedding = await embedding_service.embed_text(text)
        
        assert embedding is not None
        assert len(embedding) == 384
    
    @pytest.mark.asyncio
    async def test_embed_multiple_texts(self, embedding_service):
        """Test embedding multiple texts"""
        texts = [
            "First document about machine learning.",
            "Second document about natural language processing.",
            "Third document about computer vision.",
        ]
        embeddings = await embedding_service.embed_texts(texts)
        
        assert len(embeddings) == 3
        assert all(len(emb) == 384 for emb in embeddings)
    
    @pytest.mark.asyncio
    async def test_semantic_search(self, embedding_service):
        """Test semantic search functionality"""
        query = "machine learning algorithms"
        
        # Note: This requires documents to be indexed first in ChromaDB
        # For this test, we just verify the method works
        try:
            results = await embedding_service.search_similar(query, top_k=3)
            
            assert results is not None
            assert "query" in results
            assert "results" in results
        except Exception as e:
            # Expected if no documents indexed yet
            assert "ChromaDB" in str(e) or "client not initialized" in str(e)


class TestLLMService:
    """LLM service integration tests"""
    
    @pytest.mark.asyncio
    async def test_text_generation(self, llm_service):
        """Test text generation with LLM service"""
        prompt = "Explain what machine learning is in one sentence."
        response = await llm_service.generate(prompt, temperature=0.5)
        
        assert response is not None
        assert len(response) > 0
        assert "machine learning" in response.lower() or "learning" in response.lower()
    
    @pytest.mark.asyncio
    async def test_research_query(self, llm_service):
        """Test research query generation"""
        query = "artificial intelligence"
        response = await llm_service.research_query(query)
        
        assert response is not None
        assert len(response) > 0
    
    @pytest.mark.asyncio
    async def test_extract_claims(self, llm_service):
        """Test claim extraction"""
        text = """
        Machine learning is a subset of artificial intelligence.
        Deep learning uses neural networks with multiple layers.
        Python is the most popular language for machine learning.
        """
        
        claims = await llm_service.extract_claims(text)
        
        assert isinstance(claims, list)
        assert len(claims) >= 2
    
    @pytest.mark.asyncio
    async def test_summarization(self, llm_service):
        """Test text summarization"""
        content = """
        Artificial intelligence (AI) is intelligence demonstrated by machines, 
        as opposed to the natural intelligence displayed by humans and animals. 
        AI has applications in various fields including healthcare, finance, 
        transportation, and entertainment.
        """
        
        summary = await llm_service.summarize(content)
        
        assert summary is not None
        assert len(summary) > 0
        assert len(summary) < len(content)  # Summary should be shorter
    
    @pytest.mark.asyncio
    async def test_prompt_templates(self, llm_service):
        """Test prompt template registration and usage"""
        # Register custom template
        llm_service.register_template(
            "test_template",
            "This is a test template with {variable} placeholder."
        )
        
        # Verify it was registered
        assert "test_template" in llm_service.templates
        
        # Format template
        formatted = llm_service.templates["test_template"].format(variable="value")
        assert formatted == "This is a test template with value placeholder."
    
    @pytest.mark.asyncio
    async def test_token_counting(self, llm_service):
        """Test token counting"""
        text = "This is a sample text to count tokens."
        count = await llm_service.count_tokens(text)
        
        assert count is not None
        assert count > 0
        # Rough check: ~4 chars per token
        assert count <= len(text) // 3


class TestStreamingGeneration:
    """Test streaming text generation"""
    
    @pytest.mark.asyncio
    async def test_streaming_response(self, ollama_client):
        """Test streaming text generation"""
        prompt = "List 3 machine learning algorithms:"
        
        chunks = []
        async for chunk in ollama_client.generate_stream(prompt):
            chunks.append(chunk)
        
        full_response = "".join(chunks)
        assert len(full_response) > 0
        assert len(chunks) > 1  # Should have multiple chunks


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
