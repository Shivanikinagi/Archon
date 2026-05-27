"""
Knowledge graph routes.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends, Query

from src.api.schemas import EntityResponse, RelationshipResponse, GraphSearchResponse, PathResponse
from src.api.dependencies import get_current_user, get_db, MockDBSession
from src.core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get(
    "/entities",
    response_model=List[EntityResponse],
    summary="List entities",
    description="List all entities in the knowledge graph.",
)
async def list_entities(
    current_user: dict = Depends(get_current_user),
    db: MockDBSession = Depends(get_db),
    node_type: Optional[str] = Query(None, description="Filter by node type"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    try:
        entities = db.entities
        if node_type:
            entities = [e for e in entities if e.get("node_type") == node_type]
        return [
            EntityResponse(
                node_id=e.get("node_id", ""),
                label=e.get("label", ""),
                node_type=e.get("node_type", ""),
                properties=e.get("properties", {}),
            )
            for e in entities[offset:offset + limit]
        ]
    except Exception as e:
        logger.error(f"Failed to list entities: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/relationships",
    response_model=List[RelationshipResponse],
    summary="List relationships",
    description="List all relationships in the knowledge graph.",
)
async def list_relationships(
    current_user: dict = Depends(get_current_user),
    db: MockDBSession = Depends(get_db),
    relationship_type: Optional[str] = Query(None, description="Filter by relationship type"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    try:
        rels = db.relationships
        if relationship_type:
            rels = [r for r in rels if r.get("relationship_type") == relationship_type]
        return [
            RelationshipResponse(
                edge_id=r.get("edge_id", ""),
                source_node_id=r.get("source_node_id", ""),
                target_node_id=r.get("target_node_id", ""),
                relationship_type=r.get("relationship_type", ""),
                properties=r.get("properties", {}),
                weight=r.get("weight", 1.0),
            )
            for r in rels[offset:offset + limit]
        ]
    except Exception as e:
        logger.error(f"Failed to list relationships: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/search",
    response_model=GraphSearchResponse,
    summary="Search graph",
    description="Search the knowledge graph for entities and relationships.",
)
async def search_graph(
    q: str = Query(..., description="Search query"),
    current_user: dict = Depends(get_current_user),
    db: MockDBSession = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
):
    try:
        q_lower = q.lower()
        matched_entities = [
            e for e in db.entities
            if q_lower in e.get("label", "").lower()
            or q_lower in str(e.get("properties", {})).lower()
        ]
        matched_rel_ids = {e.get("node_id") for e in matched_entities}
        matched_rels = [
            r for r in db.relationships
            if r.get("source_node_id") in matched_rel_ids or r.get("target_node_id") in matched_rel_ids
        ]
        return GraphSearchResponse(
            entities=[
                EntityResponse(
                    node_id=e.get("node_id", ""),
                    label=e.get("label", ""),
                    node_type=e.get("node_type", ""),
                    properties=e.get("properties", {}),
                )
                for e in matched_entities[:limit]
            ],
            relationships=[
                RelationshipResponse(
                    edge_id=r.get("edge_id", ""),
                    source_node_id=r.get("source_node_id", ""),
                    target_node_id=r.get("target_node_id", ""),
                    relationship_type=r.get("relationship_type", ""),
                    properties=r.get("properties", {}),
                    weight=r.get("weight", 1.0),
                )
                for r in matched_rels[:limit]
            ],
        )
    except Exception as e:
        logger.error(f"Failed to search graph: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/paths",
    response_model=List[PathResponse],
    summary="Find paths",
    description="Find paths between two entities in the knowledge graph.",
)
async def find_paths(
    from_entity: str = Query(..., description="Source entity ID"),
    to_entity: str = Query(..., description="Target entity ID"),
    current_user: dict = Depends(get_current_user),
    db: MockDBSession = Depends(get_db),
    max_length: int = Query(4, ge=1, le=10),
):
    try:
        source = next((e for e in db.entities if e.get("node_id") == from_entity), None)
        target = next((e for e in db.entities if e.get("node_id") == to_entity), None)
        if not source or not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Source or target entity not found",
            )
        path = [source, target]
        return [
            PathResponse(
                path=[
                    EntityResponse(
                        node_id=p.get("node_id", ""),
                        label=p.get("label", ""),
                        node_type=p.get("node_type", ""),
                        properties=p.get("properties", {}),
                    )
                    for p in path
                ],
                length=len(path) - 1,
                total_weight=1.0,
            )
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to find paths: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
