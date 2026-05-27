"""
Core package - Contains foundational abstractions, types, and base classes.
"""

from .types import (
    ResearchDepth,
    SourceType,
    ReportFormat,
    CitationStyle,
    AgentRole,
    ResearchStatus,
)
from .base import BaseAgent, BaseRetriever
from .config import Config, get_config
from .logger import get_logger, setup_logging
from .exceptions import (
    ResearchAgentError,
    ConfigurationError,
    DataStorageError,
    RetrievalError,
    AgentError,
)

__all__ = [
    # Types
    "ResearchDepth",
    "SourceType",
    "ReportFormat",
    "CitationStyle",
    "AgentRole",
    "ResearchStatus",
    # Base Classes
    "BaseAgent",
    "BaseRetriever",
    # Config
    "Config",
    "get_config",
    # Logging
    "get_logger",
    "setup_logging",
    # Exceptions
    "ResearchAgentError",
    "ConfigurationError",
    "DataStorageError",
    "RetrievalError",
    "AgentError",
]
