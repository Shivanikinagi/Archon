"""Database initialization and setup script

Run migrations and initialize all databases.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.config import get_settings
from data.database import init_database, close_database
from integration.chromadb_client import init_chromadb, close_chromadb
from integration.neo4j_client import init_neo4j, close_neo4j
from integration.redis_client import init_redis_cache, close_redis_cache

logger = logging.getLogger(__name__)


async def init_all_databases():
    """Initialize all database connections"""
    
    settings = get_settings()
    
    print("\n" + "="*60)
    print("🚀 Initializing All Databases")
    print("="*60)
    
    try:
        # PostgreSQL
        print("\n📦 Initializing PostgreSQL...")
        await init_database(
            database_url=settings.database.db_url,
            pool_size=settings.database.db_pool_size,
        )
        print("✓ PostgreSQL initialized")
        
        # ChromaDB
        print("\n🔍 Initializing ChromaDB...")
        await init_chromadb(
            host=settings.vector_store.chromadb_host,
            port=settings.vector_store.chromadb_port,
            collection_name=settings.vector_store.chromadb_collection_name,
            embedding_dim=settings.vector_store.chromadb_embedding_dim,
        )
        print("✓ ChromaDB initialized")
        
        # Neo4j
        print("\n🕸️  Initializing Neo4j...")
        await init_neo4j(
            uri=settings.graph.neo4j_uri,
            username=settings.graph.neo4j_username,
            password=settings.graph.neo4j_password,
            database=settings.graph.neo4j_database,
        )
        print("✓ Neo4j initialized")
        
        # Redis
        print("\n⚡ Initializing Redis...")
        await init_redis_cache(
            url=settings.cache.redis_url,
            default_ttl=86400,  # 24 hours
        )
        print("✓ Redis initialized")
        
        print("\n" + "="*60)
        print("✅ All databases initialized successfully")
        print("="*60 + "\n")
        
        # Cleanup
        await close_database()
        await close_chromadb()
        await close_neo4j()
        await close_redis_cache()
        
    except Exception as e:
        print(f"\n❌ Initialization failed: {e}")
        logger.error(f"Database initialization error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(init_all_databases())
