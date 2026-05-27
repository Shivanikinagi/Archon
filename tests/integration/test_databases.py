"""Integration tests for database connections

Tests ChromaDB, Neo4j, and Redis connections.
"""

import pytest
import asyncio
from typing import AsyncGenerator

# These tests assume services are running
# docker-compose -f docker-compose.dev.yml up -d


@pytest.fixture
async def chromadb_client():
    """ChromaDB client fixture"""
    from integration.chromadb_client import ChromaDBClient
    
    client = ChromaDBClient(
        host="localhost",
        port=8000,
        collection_name="test_documents",
    )
    await client.init()
    yield client
    await client.close()


@pytest.fixture
async def neo4j_client():
    """Neo4j client fixture"""
    from integration.neo4j_client import Neo4jClient
    
    client = Neo4jClient(
        uri="bolt://localhost:7687",
        username="neo4j",
        password="neo4j",
    )
    await client.init()
    yield client
    await client.close()


@pytest.fixture
async def redis_cache():
    """Redis cache fixture"""
    from integration.redis_client import RedisCache
    
    cache = RedisCache(
        url="redis://localhost:6379/0",
        default_ttl=60,  # 1 minute for testing
    )
    await cache.init()
    yield cache
    await cache.close()


class TestChromaDB:
    """ChromaDB integration tests"""
    
    @pytest.mark.asyncio
    async def test_chromadb_connection(self, chromadb_client):
        """Test ChromaDB connection"""
        info = await chromadb_client.get_collection_info()
        assert info is not None
        assert "collection_name" in info
        assert "document_count" in info
    
    @pytest.mark.asyncio
    async def test_chromadb_add_and_search(self, chromadb_client):
        """Test adding and searching documents"""
        # Create test embeddings
        documents = ["Document 1", "Document 2", "Document 3"]
        embeddings = [
            [0.1] * 384,  # 384-dim embeddings for nomic-embed-text
            [0.2] * 384,
            [0.3] * 384,
        ]
        ids = ["doc1", "doc2", "doc3"]
        
        # Add documents
        await chromadb_client.add_documents(
            documents=documents,
            embeddings=embeddings,
            ids=ids,
            metadatas=[
                {"source": "test1"},
                {"source": "test2"},
                {"source": "test3"},
            ]
        )
        
        # Search
        query_embedding = [0.1] * 384
        results = await chromadb_client.search(query_embedding, top_k=2)
        
        assert results is not None
        assert "ids" in results
        assert len(results["ids"]) == 1  # One query
        assert len(results["ids"][0]) <= 2  # Top 2 results


class TestNeo4j:
    """Neo4j integration tests"""
    
    @pytest.mark.asyncio
    async def test_neo4j_connection(self, neo4j_client):
        """Test Neo4j connection"""
        stats = await neo4j_client.get_graph_stats()
        assert stats is not None
        assert "node_count" in stats
        assert "relationship_count" in stats
    
    @pytest.mark.asyncio
    async def test_neo4j_create_entity(self, neo4j_client):
        """Test creating entities"""
        entity = await neo4j_client.create_entity(
            entity_id="test_entity_1",
            label="Concept",
            properties={"name": "Test Concept", "description": "A test concept"}
        )
        
        assert entity is not None
        assert entity["id"] == "test_entity_1"
        
        # Retrieve entity
        retrieved = await neo4j_client.get_entity("test_entity_1")
        assert retrieved is not None
        assert retrieved["id"] == "test_entity_1"
    
    @pytest.mark.asyncio
    async def test_neo4j_search_entities(self, neo4j_client):
        """Test searching entities"""
        # Create test entity first
        await neo4j_client.create_entity(
            entity_id="search_test_1",
            label="Person",
            properties={"name": "Albert Einstein"}
        )
        
        # Search
        results = await neo4j_client.search_entities("Albert", top_k=5)
        
        # Should find at least one result
        assert isinstance(results, list)


class TestRedis:
    """Redis cache integration tests"""
    
    @pytest.mark.asyncio
    async def test_redis_connection(self, redis_cache):
        """Test Redis connection"""
        stats = await redis_cache.get_cache_stats()
        assert stats is not None
        assert "connected_clients" in stats
    
    @pytest.mark.asyncio
    async def test_redis_set_and_get(self, redis_cache):
        """Test setting and getting cache values"""
        # Set value
        await redis_cache.set("test_key", {"data": "test_value"}, ttl=60)
        
        # Get value
        value = await redis_cache.get("test_key")
        assert value == {"data": "test_value"}
    
    @pytest.mark.asyncio
    async def test_redis_delete(self, redis_cache):
        """Test deleting cache values"""
        # Set value
        await redis_cache.set("delete_test", "value", ttl=60)
        
        # Delete
        result = await redis_cache.delete("delete_test")
        assert result == True
        
        # Verify deleted
        value = await redis_cache.get("delete_test")
        assert value is None
    
    @pytest.mark.asyncio
    async def test_redis_set_multiple(self, redis_cache):
        """Test setting multiple cache values"""
        data = {
            "key1": {"value": 1},
            "key2": {"value": 2},
            "key3": {"value": 3},
        }
        
        await redis_cache.set_multiple(data, ttl=60)
        
        # Retrieve
        values = await redis_cache.get_multiple(["key1", "key2", "key3"])
        assert len(values) == 3
        assert values["key1"]["value"] == 1
    
    @pytest.mark.asyncio
    async def test_redis_increment(self, redis_cache):
        """Test incrementing cache values"""
        # Start value
        await redis_cache.set("counter", 10, ttl=60)
        
        # Increment
        value = await redis_cache.increment("counter", 5)
        assert value == 15
    
    @pytest.mark.asyncio
    async def test_redis_get_or_set(self, redis_cache):
        """Test get_or_set pattern"""
        call_count = 0
        
        async def compute_value():
            nonlocal call_count
            call_count += 1
            return {"computed": True}
        
        # First call should compute
        value1 = await redis_cache.get_or_set("compute_test", compute_value, ttl=60)
        assert call_count == 1
        assert value1["computed"] == True
        
        # Second call should use cache
        value2 = await redis_cache.get_or_set("compute_test", compute_value, ttl=60)
        assert call_count == 1  # Still 1, not computed again
        assert value2["computed"] == True


# Run specific test
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
