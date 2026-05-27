"""Neo4j knowledge graph integration

Provides graph database operations for knowledge graph and entity relationships.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from neo4j import AsyncDriver, AsyncSession as Neo4jAsyncSession
from neo4j import asyncio_driver, auth

logger = logging.getLogger(__name__)


class Neo4jClient:
    """Neo4j client for knowledge graph operations"""
    
    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        username: str = "neo4j",
        password: str = "neo4j",
        database: str = "neo4j",
    ):
        """
        Initialize Neo4j client
        
        Args:
            uri: Neo4j server URI
            username: Authentication username
            password: Authentication password
            database: Database name
        """
        self.uri = uri
        self.username = username
        self.password = password
        self.database = database
        self.driver: Optional[AsyncDriver] = None
    
    async def init(self) -> None:
        """
        Initialize connection to Neo4j
        
        Raises:
            Exception: If connection fails
        """
        try:
            self.driver = asyncio_driver(
                self.uri,
                auth=(self.username, self.password),
                encrypted=False,
            )
            
            # Test connection
            async with self.driver.session(database=self.database) as session:
                await session.run("RETURN 1 as test")
            
            logger.info(f"✓ Neo4j client initialized (uri={self.uri}, db={self.database})")
        except Exception as e:
            logger.error(f"✗ Failed to initialize Neo4j: {e}")
            raise
    
    async def create_entity(
        self,
        entity_id: str,
        label: str,
        properties: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Create entity node
        
        Args:
            entity_id: Unique entity identifier
            label: Node label (Entity, Concept, Person, Organization, Event, Paper, Document)
            properties: Node properties
            
        Returns:
            Created node data
        """
        query = f"""
        CREATE (n:{label} {{id: $id, created_at: datetime()}})
        SET n += $properties
        RETURN n
        """
        
        try:
            async with self.driver.session(database=self.database) as session:
                result = await session.run(
                    query,
                    id=entity_id,
                    properties=properties,
                )
                record = await result.single()
                logger.debug(f"✓ Created entity: {entity_id}")
                return dict(record["n"])
        except Exception as e:
            logger.error(f"✗ Failed to create entity: {e}")
            raise
    
    async def create_relationship(
        self,
        source_id: str,
        target_id: str,
        relationship_type: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create relationship between entities
        
        Args:
            source_id: Source entity ID
            target_id: Target entity ID
            relationship_type: Relationship type (MENTIONS, SIMILAR_TO, CONTRADICTS, SUPPORTS, IS_A, PART_OF, CITES)
            properties: Relationship properties
            
        Returns:
            Created relationship data
        """
        query = f"""
        MATCH (source {{id: $source_id}})
        MATCH (target {{id: $target_id}})
        CREATE (source)-[r:{relationship_type} {{created_at: datetime()}}]->(target)
        SET r += $properties
        RETURN r
        """
        
        try:
            async with self.driver.session(database=self.database) as session:
                result = await session.run(
                    query,
                    source_id=source_id,
                    target_id=target_id,
                    properties=properties or {},
                )
                record = await result.single()
                logger.debug(f"✓ Created relationship: {source_id} -[{relationship_type}]-> {target_id}")
                return dict(record["r"])
        except Exception as e:
            logger.error(f"✗ Failed to create relationship: {e}")
            raise
    
    async def get_entity(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """
        Get entity by ID
        
        Args:
            entity_id: Entity ID
            
        Returns:
            Entity data or None
        """
        query = """
        MATCH (n {id: $id})
        RETURN n, labels(n) as labels
        """
        
        try:
            async with self.driver.session(database=self.database) as session:
                result = await session.run(query, id=entity_id)
                record = await result.single()
                if record:
                    return {
                        "id": entity_id,
                        "labels": record["labels"],
                        "properties": dict(record["n"]),
                    }
                return None
        except Exception as e:
            logger.error(f"✗ Failed to get entity: {e}")
            raise
    
    async def search_entities(
        self,
        query_text: str,
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Search entities by text
        
        Args:
            query_text: Search text
            top_k: Number of results
            
        Returns:
            List of matching entities
        """
        cypher_query = """
        MATCH (n)
        WHERE n.name CONTAINS $query OR n.title CONTAINS $query
        RETURN n, labels(n) as labels
        LIMIT $limit
        """
        
        try:
            async with self.driver.session(database=self.database) as session:
                result = await session.run(
                    cypher_query,
                    query=query_text,
                    limit=top_k,
                )
                records = await result.fetch(top_k)
                entities = []
                for record in records:
                    entities.append({
                        "id": record["n"].get("id"),
                        "labels": record["labels"],
                        "properties": dict(record["n"]),
                    })
                logger.debug(f"✓ Found {len(entities)} entities for '{query_text}'")
                return entities
        except Exception as e:
            logger.error(f"✗ Failed to search entities: {e}")
            raise
    
    async def get_relationships(
        self,
        entity_id: str,
        hops: int = 1,
    ) -> List[Dict[str, Any]]:
        """
        Get related entities (multi-hop traversal)
        
        Args:
            entity_id: Starting entity ID
            hops: Number of hops to traverse (1-3)
            
        Returns:
            List of relationships and related entities
        """
        if hops < 1 or hops > 3:
            raise ValueError("hops must be between 1 and 3")
        
        relationship_pattern = "-[*1.." + str(hops) + "]-"
        query = f"""
        MATCH (source {{id: $id}}){relationship_pattern}(target)
        RETURN source, relationships, target
        LIMIT 100
        """
        
        try:
            async with self.driver.session(database=self.database) as session:
                result = await session.run(query, id=entity_id)
                records = await result.fetch(100)
                relationships = []
                for record in records:
                    relationships.append({
                        "source": dict(record["source"]),
                        "target": dict(record["target"]),
                    })
                logger.debug(f"✓ Found {len(relationships)} relationships for entity {entity_id}")
                return relationships
        except Exception as e:
            logger.error(f"✗ Failed to get relationships: {e}")
            raise
    
    async def get_graph_stats(self) -> Dict[str, Any]:
        """
        Get graph database statistics
        
        Returns:
            Statistics about nodes and relationships
        """
        query = """
        MATCH (n)
        RETURN count(n) as node_count,
               count(DISTINCT labels(n)[0]) as label_count
        """
        
        rel_query = """
        MATCH ()-[r]-()
        RETURN count(r) as relationship_count,
               count(DISTINCT type(r)) as rel_type_count
        """
        
        try:
            async with self.driver.session(database=self.database) as session:
                # Get node stats
                result = await session.run(query)
                node_record = await result.single()
                
                # Get relationship stats
                result = await session.run(rel_query)
                rel_record = await result.single()
                
                stats = {
                    "node_count": node_record["node_count"],
                    "relationship_count": rel_record["relationship_count"],
                    "label_count": node_record["label_count"],
                    "rel_type_count": rel_record["rel_type_count"],
                }
                
                logger.debug(f"✓ Graph stats: {stats}")
                return stats
        except Exception as e:
            logger.error(f"✗ Failed to get graph stats: {e}")
            raise
    
    async def delete_entity(self, entity_id: str) -> bool:
        """
        Delete entity and its relationships
        
        Args:
            entity_id: Entity ID to delete
            
        Returns:
            Success flag
        """
        query = """
        MATCH (n {id: $id})
        DETACH DELETE n
        RETURN TRUE
        """
        
        try:
            async with self.driver.session(database=self.database) as session:
                result = await session.run(query, id=entity_id)
                record = await result.single()
                logger.debug(f"✓ Deleted entity: {entity_id}")
                return record is not None
        except Exception as e:
            logger.error(f"✗ Failed to delete entity: {e}")
            raise
    
    async def close(self) -> None:
        """Close Neo4j connection"""
        try:
            if self.driver:
                await self.driver.close()
                self.driver = None
                logger.info("✓ Neo4j connection closed")
        except Exception as e:
            logger.error(f"✗ Failed to close Neo4j connection: {e}")
            raise


# Global Neo4j client instance
_neo4j_client: Optional[Neo4jClient] = None


async def init_neo4j(
    uri: str = "bolt://localhost:7687",
    username: str = "neo4j",
    password: str = "neo4j",
    database: str = "neo4j",
) -> None:
    """
    Initialize global Neo4j client
    
    Args:
        uri: Neo4j server URI
        username: Authentication username
        password: Authentication password
        database: Database name
    """
    global _neo4j_client
    _neo4j_client = Neo4jClient(uri, username, password, database)
    await _neo4j_client.init()


async def close_neo4j() -> None:
    """Close global Neo4j client"""
    global _neo4j_client
    if _neo4j_client:
        await _neo4j_client.close()
        _neo4j_client = None


def get_neo4j_client() -> Neo4jClient:
    """Get global Neo4j client"""
    if _neo4j_client is None:
        raise RuntimeError("Neo4j client not initialized. Call init_neo4j() first.")
    return _neo4j_client
