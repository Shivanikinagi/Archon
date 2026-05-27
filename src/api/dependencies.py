"""
Common dependencies for FastAPI routes.
"""

import os
from typing import Optional, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.core.security import verify_token, verify_refresh_token
from src.core.logger import get_logger

logger = get_logger(__name__)

JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "research-agent-secret-key")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")


class MockDBSession:
    """Mock database session for demonstration and testing."""

    def __init__(self):
        self.users: dict[str, dict] = {}
        self.sessions: dict[str, dict] = {}
        self.reports: dict[str, dict] = {}
        self.documents: dict[str, dict] = {}
        self.chunks: dict[str, list] = {}
        self.entities: list[dict] = []
        self.relationships: list[dict] = []


# Shared singleton mock database
_mock_db = MockDBSession()


async def get_db() -> MockDBSession:
    """Get mock database session."""
    return _mock_db


class MockOllamaClient:
    """Mock Ollama client."""

    async def generate(self, prompt: str, model: str = "mistral"):
        return {"response": f"Mock response for: {prompt[:50]}..."}

    async def pull(self, model_name: str):
        return {"status": "pulling", "model": model_name}


async def get_ollama_client() -> MockOllamaClient:
    """Get Ollama client dependency."""
    return MockOllamaClient()


class MockSearchService:
    """Mock search service."""

    async def search(self, query: str, max_results: int = 10):
        return [
            {
                "title": f"Mock result for {query}",
                "url": "http://example.com",
                "snippet": "...",
            }
        ]


async def get_search_service() -> MockSearchService:
    """Get search service dependency."""
    return MockSearchService()


security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict[str, Any]:
    """
    Validate JWT token and return current user.

    Args:
        credentials: HTTP Authorization credentials.

    Returns:
        Current user dictionary.

    Raises:
        HTTPException: If token is missing or invalid.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        token_data = verify_token(token, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return {
            "user_id": token_data.user_id,
            "email": token_data.email,
            "role": token_data.role,
        }
    except Exception as e:
        logger.warning(f"Authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
