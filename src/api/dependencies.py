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
        # Pre-populate with AI ecosystem demo data
        self.entities: list[dict] = [
            {"node_id": "openai", "label": "OpenAI", "node_type": "Company", "properties": {"founded": "2015", "valuation": "$80B+"}},
            {"node_id": "microsoft", "label": "Microsoft", "node_type": "Company", "properties": {"market_cap": "$3T+", "ceo": "Satya Nadella"}},
            {"node_id": "nvidia", "label": "NVIDIA", "node_type": "Company", "properties": {"market_cap": "$3T+", "key_product": "H100, B200 GPUs"}},
            {"node_id": "anthropic", "label": "Anthropic", "node_type": "Company", "properties": {"founded": "2021", "valuation": "$18B+"}},
            {"node_id": "google", "label": "Google", "node_type": "Company", "properties": {"parent": "Alphabet", "key_products": "Gemini 1.5, DeepMind"}},
            {"node_id": "gpt-4o", "label": "GPT-4o", "node_type": "Model", "properties": {"release": "May 2024", "modality": "Text, Image, Audio"}},
            {"node_id": "gemini-1.5", "label": "Gemini 1.5", "node_type": "Model", "properties": {"release": "Feb 2024", "context": "2M tokens"}},
            {"node_id": "claude-3.5", "label": "Claude 3.5 Sonnet", "node_type": "Model", "properties": {"release": "June 2024", "strength": "Reasoning, Coding"}},
            {"node_id": "copilot", "label": "Microsoft Copilot", "node_type": "Product", "properties": {"launch": "2023", "users": "400M+"}},
            {"node_id": "deepmind", "label": "DeepMind", "node_type": "Organization", "properties": {"founded": "2010", "key_work": "AlphaFold, Gemini"}},
            {"node_id": "amazon", "label": "Amazon", "node_type": "Company", "properties": {"ai_platform": "Bedrock", "investment": "$4B in Anthropic"}},
        ]
        self.relationships: list[dict] = [
            {"edge_id": "e1", "source_node_id": "microsoft", "target_node_id": "openai", "relationship_type": "invests_in", "weight": 3.0, "properties": {"amount": "$13B"}},
            {"edge_id": "e2", "source_node_id": "openai", "target_node_id": "nvidia", "relationship_type": "uses_chips_from", "weight": 2.5, "properties": {}},
            {"edge_id": "e3", "source_node_id": "anthropic", "target_node_id": "google", "relationship_type": "funded_by", "weight": 2.0, "properties": {}},
            {"edge_id": "e4", "source_node_id": "openai", "target_node_id": "anthropic", "relationship_type": "competes_with", "weight": 2.5, "properties": {}},
            {"edge_id": "e5", "source_node_id": "google", "target_node_id": "openai", "relationship_type": "competes_with", "weight": 2.5, "properties": {}},
            {"edge_id": "e6", "source_node_id": "microsoft", "target_node_id": "google", "relationship_type": "competes_with", "weight": 2.0, "properties": {}},
            {"edge_id": "e7", "source_node_id": "nvidia", "target_node_id": "microsoft", "relationship_type": "supplies_chips_to", "weight": 2.5, "properties": {}},
            {"edge_id": "e8", "source_node_id": "nvidia", "target_node_id": "google", "relationship_type": "supplies_chips_to", "weight": 2.5, "properties": {}},
            {"edge_id": "e9", "source_node_id": "openai", "target_node_id": "gpt-4o", "relationship_type": "creates", "weight": 3.0, "properties": {}},
            {"edge_id": "e10", "source_node_id": "google", "target_node_id": "gemini-1.5", "relationship_type": "creates", "weight": 3.0, "properties": {}},
            {"edge_id": "e11", "source_node_id": "anthropic", "target_node_id": "claude-3.5", "relationship_type": "creates", "weight": 3.0, "properties": {}},
            {"edge_id": "e12", "source_node_id": "gpt-4o", "target_node_id": "gemini-1.5", "relationship_type": "competes_with", "weight": 2.0, "properties": {}},
            {"edge_id": "e13", "source_node_id": "gpt-4o", "target_node_id": "claude-3.5", "relationship_type": "competes_with", "weight": 2.0, "properties": {}},
            {"edge_id": "e14", "source_node_id": "gemini-1.5", "target_node_id": "claude-3.5", "relationship_type": "competes_with", "weight": 2.0, "properties": {}},
            {"edge_id": "e15", "source_node_id": "microsoft", "target_node_id": "copilot", "relationship_type": "integrates", "weight": 2.5, "properties": {}},
            {"edge_id": "e16", "source_node_id": "copilot", "target_node_id": "openai", "relationship_type": "powered_by", "weight": 2.5, "properties": {}},
            {"edge_id": "e17", "source_node_id": "google", "target_node_id": "deepmind", "relationship_type": "owns", "weight": 2.5, "properties": {}},
            {"edge_id": "e18", "source_node_id": "amazon", "target_node_id": "anthropic", "relationship_type": "partners_with", "weight": 2.0, "properties": {}},
        ]


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
