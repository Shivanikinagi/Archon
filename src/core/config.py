"""
Configuration management using Pydantic.
"""

from pathlib import Path
from typing import Optional
from functools import lru_cache

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class LLMConfig(BaseSettings):
    """LLM provider configuration."""
    provider: str = Field(default="openai", description="LLM provider (openai, anthropic, google, cohere, ollama)")
    api_key: Optional[str] = Field(default=None, description="API key for the provider")
    model: str = Field(default="gpt-4-turbo-preview", description="Model name")
    embedding_model: str = Field(default="text-embedding-3-large", description="Embedding model")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Temperature for generation")
    max_tokens: int = Field(default=4096, ge=1, description="Maximum tokens to generate")
    timeout: int = Field(default=60, ge=1, description="API timeout in seconds")

    class Config:
        env_prefix = "OPENAI_"


class OllamaConfig(BaseSettings):
    """Ollama local LLM configuration."""
    enabled: bool = Field(default=False, description="Enable Ollama")
    base_url: str = Field(default="http://localhost:11434", description="Ollama base URL")
    model: str = Field(default="mistral", description="Model name (mistral, llama2, neural-chat, etc.)")
    embedding_model: str = Field(default="nomic-embed-text", description="Embedding model for Ollama")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Temperature for generation")
    top_k: int = Field(default=40, ge=1, description="Top K sampling")
    top_p: float = Field(default=0.9, ge=0.0, le=1.0, description="Top P (nucleus) sampling")
    timeout: int = Field(default=300, ge=1, description="Request timeout in seconds")
    num_predict: int = Field(default=2048, ge=1, description="Max tokens to generate")

    class Config:
        env_prefix = "OLLAMA_"


class VectorStoreConfig(BaseSettings):
    """Vector database configuration."""
    backend: str = Field(default="chromadb", description="Backend (chromadb, pinecone, weaviate)")
    collection_name: str = Field(default="research_documents", description="Collection name")
    dimension: int = Field(default=1536, description="Embedding dimension")
    similarity_metric: str = Field(default="cosine", description="Similarity metric")

    # ChromaDB
    chroma_persist_dir: Optional[str] = None
    chroma_collection_name: str = "research_documents"

    # Pinecone
    pinecone_api_key: Optional[str] = None
    pinecone_index_name: Optional[str] = None
    pinecone_environment: Optional[str] = None

    # Weaviate
    weaviate_url: Optional[str] = None
    weaviate_api_key: Optional[str] = None

    class Config:
        env_prefix = ""


class KnowledgeGraphConfig(BaseSettings):
    """Knowledge graph database configuration."""
    backend: str = Field(default="neo4j", description="Backend (neo4j, postgres)")
    uri: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    database: Optional[str] = None

    # Neo4j specific
    neo4j_uri: Optional[str] = Field(None, description="Neo4j connection URI")
    neo4j_username: Optional[str] = None
    neo4j_password: Optional[str] = None

    # PostgreSQL specific
    postgres_url: Optional[str] = None
    postgres_pool_size: int = 20

    class Config:
        env_prefix = ""


class SearchConfig(BaseSettings):
    """Web search configuration."""
    providers: list[str] = Field(default=["serper", "google"], description="Search providers")
    serper_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    google_search_engine_id: Optional[str] = None
    brave_api_key: Optional[str] = None
    max_results_per_query: int = Field(default=10, ge=1, description="Max results per query")

    class Config:
        env_prefix = ""


class ResearchConfig(BaseSettings):
    """Research execution configuration."""
    temp_dir: str = Field(default="./research_output", description="Temp directory for research")
    cache_dir: str = Field(default="./cache", description="Cache directory")
    timeout_seconds: int = Field(default=3600, ge=60, description="Research timeout")
    parallel_tasks: int = Field(default=5, ge=1, description="Parallel research tasks")
    chunk_size: int = Field(default=512, ge=256, description="Document chunk size")
    chunk_overlap: int = Field(default=128, ge=0, description="Chunk overlap")

    class Config:
        env_prefix = "RESEARCH_"


class RAGConfig(BaseSettings):
    """RAG configuration."""
    top_k: int = Field(default=10, ge=1, description="Top K results to retrieve")
    similarity_threshold: float = Field(default=0.6, ge=0.0, le=1.0, description="Similarity threshold")
    rerank_top_k: int = Field(default=5, ge=1, description="Rerank top K")

    class Config:
        env_prefix = "RAG_"


class GraphRAGConfig(BaseSettings):
    """GraphRAG configuration."""
    graph_size_limit: int = Field(default=5000, ge=100, description="Knowledge graph size limit")
    max_hops: int = Field(default=3, ge=1, description="Max hops in graph traversal")
    similarity_cutoff: float = Field(default=0.5, ge=0.0, le=1.0, description="Similarity cutoff")

    class Config:
        env_prefix = "GRAPHRAG_"


class FactCheckConfig(BaseSettings):
    """Fact checking configuration."""
    enabled: bool = True
    confidence_threshold: float = Field(default=0.75, ge=0.0, le=1.0, description="Confidence threshold")

    class Config:
        env_prefix = "FACT_CHECK_"


class APIConfig(BaseSettings):
    """API server configuration."""
    host: str = Field(default="0.0.0.0", description="API host")
    port: int = Field(default=8000, ge=1, le=65535, description="API port")
    reload: bool = False
    workers: int = Field(default=4, ge=1, description="Number of workers")
    timeout: int = Field(default=300, ge=60, description="Request timeout")

    class Config:
        env_prefix = "API_"


class LoggingConfig(BaseSettings):
    """Logging configuration."""
    level: str = Field(default="INFO", description="Log level")
    file: Optional[str] = None
    max_bytes: int = Field(default=10485760, ge=1024, description="Max log file size")
    backup_count: int = Field(default=5, ge=1, description="Number of backup files")

    class Config:
        env_prefix = "LOG_"


class Config(BaseSettings):
    """Main configuration class."""
    # Environment
    environment: str = Field(default="development", description="Environment (development, staging, production)")
    debug: bool = False

    # Components
    llm: LLMConfig = Field(default_factory=LLMConfig)
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    vector_store: VectorStoreConfig = Field(default_factory=VectorStoreConfig)
    knowledge_graph: KnowledgeGraphConfig = Field(default_factory=KnowledgeGraphConfig)
    search: SearchConfig = Field(default_factory=SearchConfig)
    research: ResearchConfig = Field(default_factory=ResearchConfig)
    rag: RAGConfig = Field(default_factory=RAGConfig)
    graphrag: GraphRAGConfig = Field(default_factory=GraphRAGConfig)
    fact_check: FactCheckConfig = Field(default_factory=FactCheckConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    class Config:
        env_file = ".env"
        case_sensitive = False

    @validator("research")
    def validate_research_dirs(cls, v: ResearchConfig) -> ResearchConfig:
        """Ensure research directories exist."""
        Path(v.temp_dir).mkdir(parents=True, exist_ok=True)
        Path(v.cache_dir).mkdir(parents=True, exist_ok=True)
        return v


@lru_cache(maxsize=1)
def get_config() -> Config:
    """
    Get the configuration instance (cached).

    Returns:
        Configuration object
    """
    return Config()
