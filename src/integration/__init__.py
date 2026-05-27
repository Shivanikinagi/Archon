"""
Integration layer for external services and APIs.
"""

from typing import Union
from src.core.config import LLMConfig, OllamaConfig, get_config
from src.core.logger import get_logger
from src.core.exceptions import ConfigurationError
from .ollama import OllamaLLMProvider

logger = get_logger(__name__)


class LLMProviderFactory:
    """Factory for creating LLM provider instances."""

    @staticmethod
    def create_provider(
        provider: str = "openai",
        llm_config: LLMConfig | None = None,
        ollama_config: OllamaConfig | None = None,
    ):
        """
        Create an LLM provider instance.

        Args:
            provider: Provider name (openai, ollama, anthropic, google, cohere)
            llm_config: LLM configuration
            ollama_config: Ollama configuration

        Returns:
            LLM provider instance

        Raises:
            ConfigurationError: If provider is not supported
        """
        config = get_config()
        llm_config = llm_config or config.llm
        ollama_config = ollama_config or config.ollama

        if provider.lower() == "ollama":
            logger.info("Creating Ollama LLM provider")
            return OllamaLLMProvider(ollama_config)

        elif provider.lower() == "openai":
            logger.info("Creating OpenAI LLM provider")
            try:
                from langchain_openai import ChatOpenAI, OpenAIEmbeddings
                return {
                    "chat": ChatOpenAI(
                        api_key=llm_config.api_key,
                        model_name=llm_config.model,
                        temperature=llm_config.temperature,
                        max_tokens=llm_config.max_tokens,
                        request_timeout=llm_config.timeout,
                    ),
                    "embeddings": OpenAIEmbeddings(
                        api_key=llm_config.api_key,
                        model=llm_config.embedding_model,
                    ),
                }
            except ImportError:
                raise ConfigurationError(
                    "langchain-openai not installed. Install with: pip install langchain-openai"
                )

        elif provider.lower() == "anthropic":
            logger.info("Creating Anthropic LLM provider")
            try:
                from langchain_anthropic import ChatAnthropic
                return ChatAnthropic(
                    api_key=llm_config.api_key,
                    model_name=llm_config.model,
                    temperature=llm_config.temperature,
                    max_tokens=llm_config.max_tokens,
                )
            except ImportError:
                raise ConfigurationError(
                    "langchain-anthropic not installed. Install with: pip install langchain-anthropic"
                )

        else:
            raise ConfigurationError(
                f"Unsupported LLM provider: {provider}. "
                f"Supported providers: ollama, openai, anthropic, google, cohere"
            )

    @staticmethod
    def get_default_provider():
        """Get the default LLM provider based on configuration."""
        config = get_config()

        if config.ollama.enabled:
            logger.info("Using Ollama as default LLM provider")
            return LLMProviderFactory.create_provider("ollama")

        logger.info("Using OpenAI as default LLM provider")
        return LLMProviderFactory.create_provider("openai")


__all__ = [
    "LLMProviderFactory",
    "OllamaLLMProvider",
]
