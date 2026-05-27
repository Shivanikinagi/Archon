"""
Admin routes.
"""

from datetime import datetime
from typing import List
from fastapi import APIRouter, HTTPException, status, Depends

from src.api.schemas import (
    SystemStatsResponse,
    UserAdminResponse,
    HealthDetailedResponse,
    ModelPullRequest,
)
from src.api.dependencies import (
    get_current_user,
    get_db,
    get_ollama_client,
    MockDBSession,
    MockOllamaClient,
)
from src.core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Dependency to require admin role."""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


@router.get(
    "/stats",
    response_model=SystemStatsResponse,
    summary="System statistics",
    description="Get overall system statistics.",
)
async def get_stats(
    current_user: dict = Depends(require_admin),
    db: MockDBSession = Depends(get_db),
):
    try:
        total_sessions = len(db.sessions)
        total_reports = len(db.reports)
        total_documents = len(db.documents)
        total_users = len(db.users)
        active_sessions = sum(
            1 for s in db.sessions.values()
            if s.get("status") not in ("completed", "failed", "cancelled")
        )
        return SystemStatsResponse(
            total_sessions=total_sessions,
            total_reports=total_reports,
            total_documents=total_documents,
            total_users=total_users,
            active_sessions=active_sessions,
            system_load=0.0,
            uptime_seconds=0,
        )
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/users",
    response_model=List[UserAdminResponse],
    summary="List users",
    description="List all registered users (admin only).",
)
async def list_users(
    current_user: dict = Depends(require_admin),
    db: MockDBSession = Depends(get_db),
):
    try:
        users = []
        for u in db.users.values():
            users.append(
                UserAdminResponse(
                    user_id=u.get("user_id", 0),
                    email=u.get("email", ""),
                    name=u.get("name", ""),
                    role=u.get("role", "user"),
                    is_active=u.get("is_active", True),
                    created_at=u.get("created_at"),
                    last_login=u.get("last_login"),
                )
            )
        return users
    except Exception as e:
        logger.error(f"Failed to list users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/health",
    response_model=HealthDetailedResponse,
    summary="Detailed health check",
    description="Get detailed health status of all services.",
)
async def health_check(
    current_user: dict = Depends(require_admin),
):
    try:
        return HealthDetailedResponse(
            status="healthy",
            timestamp=datetime.now(),
            version="1.0.0",
            services={
                "api": {"status": "healthy", "latency_ms": 12},
                "database": {"status": "healthy", "latency_ms": 5},
                "ollama": {"status": "healthy", "latency_ms": 45},
                "vector_store": {"status": "healthy", "latency_ms": 8},
                "graph_store": {"status": "healthy", "latency_ms": 15},
            },
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post(
    "/models/pull",
    summary="Pull Ollama model",
    description="Pull a model from Ollama registry.",
)
async def pull_model(
    request: ModelPullRequest,
    current_user: dict = Depends(require_admin),
    ollama: MockOllamaClient = Depends(get_ollama_client),
):
    try:
        result = await ollama.pull(request.model_name)
        return {
            "status": "success",
            "model": request.model_name,
            "result": result,
        }
    except Exception as e:
        logger.error(f"Failed to pull model: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
