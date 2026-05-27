"""
Custom exceptions for the research agent system.
"""


class ResearchAgentError(Exception):
    """Base exception for all research agent errors."""
    pass


class ConfigurationError(ResearchAgentError):
    """Raised when configuration is invalid or missing."""
    pass


class DataStorageError(ResearchAgentError):
    """Raised when data storage operations fail."""
    pass


class RetrievalError(ResearchAgentError):
    """Raised when retrieval operations fail."""
    pass


class AgentError(ResearchAgentError):
    """Raised when agent operations fail."""
    pass


class LLMError(ResearchAgentError):
    """Raised when LLM API calls fail."""
    pass


class DocumentProcessingError(ResearchAgentError):
    """Raised when document processing fails."""
    pass


class SearchError(ResearchAgentError):
    """Raised when search operations fail."""
    pass


class ValidationError(ResearchAgentError):
    """Raised when validation fails."""
    pass


class TimeoutError(ResearchAgentError):
    """Raised when operations exceed time limits."""
    pass
