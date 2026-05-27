"""
Route submodules for the Deep Research Agent API.

If api/routes.py is removed, this package can be imported directly as
`from src.api.routes import auth_router`.
"""

from .auth import router as auth_router
from .research import router as research_router
from .reports import router as reports_router
from .documents import router as documents_router
from .graphs import router as graphs_router
from .admin import router as admin_router

__all__ = [
    "auth_router",
    "research_router",
    "reports_router",
    "documents_router",
    "graphs_router",
    "admin_router",
]
