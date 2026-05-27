"""
Base classes for agents and retrievers.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Generic, TypeVar
from dataclasses import dataclass, field
from datetime import datetime

from .types import (
    ResearchQuery,
    DocumentChunk,
    RetrievalResult,
    KnowledgeGraphNode,
    KnowledgeGraphEdge,
    AgentRole,
)
from .logger import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


@dataclass
class ExecutionResult(Generic[T]):
    """Result of an execution."""
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


class BaseAgent(ABC):
    """
    Base class for all agents in the system.

    Agents are autonomous entities that perform specific tasks in the research pipeline.
    """

    def __init__(self, role: AgentRole, name: str = ""):
        """
        Initialize the agent.

        Args:
            role: The role of the agent
            name: Optional name for the agent instance
        """
        self.role = role
        self.name = name or role.value
        self.logger = get_logger(self.__class__.__name__)

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ExecutionResult:
        """
        Execute the agent's primary task.

        Args:
            **kwargs: Task-specific parameters

        Returns:
            ExecutionResult with output data or error
        """
        pass

    @abstractmethod
    def validate_inputs(self, **kwargs: Any) -> bool:
        """
        Validate input parameters.

        Args:
            **kwargs: Parameters to validate

        Returns:
            True if inputs are valid
        """
        pass

    async def run(self, **kwargs: Any) -> ExecutionResult:
        """
        Run the agent with error handling.

        Args:
            **kwargs: Task-specific parameters

        Returns:
            ExecutionResult with execution outcome
        """
        try:
            if not self.validate_inputs(**kwargs):
                return ExecutionResult(
                    success=False,
                    error="Invalid input parameters",
                )

            self.logger.info(f"Executing {self.name} agent", extra={"role": self.role})
            result = await self.execute(**kwargs)
            return result

        except Exception as e:
            self.logger.error(f"Error executing {self.name}: {str(e)}")
            return ExecutionResult(
                success=False,
                error=str(e),
            )


class BaseRetriever(ABC):
    """
    Base class for all retrieval engines.

    Retrievers are responsible for finding relevant content from storage.
    """

    def __init__(self, name: str = ""):
        """
        Initialize the retriever.

        Args:
            name: Name of the retriever
        """
        self.name = name or self.__class__.__name__
        self.logger = get_logger(self.__class__.__name__)

    @abstractmethod
    async def retrieve(
        self,
        query: ResearchQuery,
        top_k: int = 10,
    ) -> list[RetrievalResult]:
        """
        Retrieve relevant documents for a query.

        Args:
            query: The research query
            top_k: Number of top results to retrieve

        Returns:
            List of retrieval results ranked by relevance
        """
        pass

    @abstractmethod
    async def retrieve_by_similarity(
        self,
        embedding: list[float],
        top_k: int = 10,
    ) -> list[RetrievalResult]:
        """
        Retrieve documents by embedding similarity.

        Args:
            embedding: Query embedding vector
            top_k: Number of top results to retrieve

        Returns:
            List of retrieval results
        """
        pass

    async def retrieve_with_threshold(
        self,
        query: ResearchQuery,
        top_k: int = 10,
        threshold: float = 0.5,
    ) -> list[RetrievalResult]:
        """
        Retrieve results above a similarity threshold.

        Args:
            query: The research query
            top_k: Maximum number of results
            threshold: Minimum similarity threshold

        Returns:
            Filtered retrieval results
        """
        results = await self.retrieve(query, top_k=top_k)
        return [r for r in results if r.similarity_score >= threshold]


class BaseVectorStore(ABC):
    """
    Base class for vector database backends.

    Vector stores manage embeddings and similarity search.
    """

    def __init__(self, name: str = ""):
        """Initialize the vector store."""
        self.name = name or self.__class__.__name__
        self.logger = get_logger(self.__class__.__name__)

    @abstractmethod
    async def add_documents(
        self,
        chunks: list[DocumentChunk],
    ) -> list[str]:
        """
        Add document chunks to the store.

        Args:
            chunks: List of document chunks with embeddings

        Returns:
            List of document IDs
        """
        pass

    @abstractmethod
    async def search(
        self,
        embedding: list[float],
        top_k: int = 10,
    ) -> list[tuple[DocumentChunk, float]]:
        """
        Search for similar documents by embedding.

        Args:
            embedding: Query embedding
            top_k: Number of results

        Returns:
            List of (chunk, similarity_score) tuples
        """
        pass

    @abstractmethod
    async def delete_documents(self, doc_ids: list[str]) -> int:
        """
        Delete documents from the store.

        Args:
            doc_ids: List of document IDs to delete

        Returns:
            Number of deleted documents
        """
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all documents from the store."""
        pass


class BaseGraphStore(ABC):
    """
    Base class for knowledge graph backends.

    Graph stores manage semantic relationships between entities.
    """

    def __init__(self, name: str = ""):
        """Initialize the graph store."""
        self.name = name or self.__class__.__name__
        self.logger = get_logger(self.__class__.__name__)

    @abstractmethod
    async def add_nodes(self, nodes: list[KnowledgeGraphNode]) -> list[str]:
        """Add nodes to the graph."""
        pass

    @abstractmethod
    async def add_edges(self, edges: list[KnowledgeGraphEdge]) -> list[str]:
        """Add edges to the graph."""
        pass

    @abstractmethod
    async def get_neighbors(
        self,
        node_id: str,
        max_hops: int = 2,
    ) -> list[KnowledgeGraphNode]:
        """Get neighboring nodes in the graph."""
        pass

    @abstractmethod
    async def find_paths(
        self,
        source_id: str,
        target_id: str,
    ) -> list[list[KnowledgeGraphNode]]:
        """Find paths between two nodes."""
        pass

    @abstractmethod
    async def delete_nodes(self, node_ids: list[str]) -> int:
        """Delete nodes from the graph."""
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear the entire graph."""
        pass
