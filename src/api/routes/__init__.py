"""
Route submodules for the Deep Research Agent API.
"""

from fastapi import APIRouter

# Import the aggregator router from api/routes.py (module, not package)
# We build it here to avoid namespace conflicts
router = APIRouter(prefix="/api/v1")

from .auth import router as auth_router
from .research import router as research_router
from .reports import router as reports_router
from .documents import router as documents_router
from .graphs import router as graphs_router
from .admin import router as admin_router

router.include_router(auth_router, prefix="/auth")
router.include_router(research_router)
router.include_router(reports_router)
router.include_router(documents_router)
router.include_router(graphs_router)
router.include_router(admin_router)

__all__ = [
    "router",
    "auth_router",
    "research_router",
    "reports_router",
    "documents_router",
    "graphs_router",
    "admin_router",
]
