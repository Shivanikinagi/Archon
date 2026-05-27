"""
Ollama integration for local LLM inference.
"""

import asyncio
from typing import AsyncGenerator, Optional
import httpx

from src.core.config import OllamaConfig
from src.core.logger import get_logger
from src.core.exceptions import LLMError

logger = get_logger(__name__)


class OllamaClient:
    """Client for interacting with Ollama local LLM runtime."""

    def __init__(self, config: OllamaConfig):
        """
        Initialize Ollama client.

        Args:
            config: Ollama configuration
        """
        self.config = config
        self.base_url = config.base_url.rstrip("/")
        self.model = config.model
        self.embedding_model = config.embedding_model
        self.timeout = httpx.Timeout(config.timeout)
        self.logger = get_logger(self.__class__.__name__)

    async def is_running(self) -> bool:
        """
        Check if Ollama service is running.

        Returns:
            True if Ollama is accessible
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception as e:
            self.logger.warning(f"Ollama service not accessible: {str(e)}")
            return False

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        stream: bool = False,
    ) -> str | AsyncGenerator[str, None]:
        """
        Generate text using Ollama.

        Args:
            prompt: Input prompt
            model: Model name (defaults to config model)
            stream: Whether to stream response

        Returns:
            Generated text or async generator if streaming

        Raises:
            LLMError: If generation fails
        """
        model = model or self.model

        if not await self.is_running():
            raise LLMError("Ollama service is not running")

        if stream:
            return self._generate_stream(prompt, model)
        else:
            return await self._generate_complete(prompt, model)

    async def _generate_complete(self, prompt: str, model: str) -> str:
        """Generate complete response (non-streaming)."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False,
                        "temperature": self.config.temperature,
                        "top_k": self.config.top_k,
                        "top_p": self.config.top_p,
                        "num_predict": self.config.num_predict,
                    },
                )
                response.raise_for_status()
                result = response.json()
                return result.get("response", "")

        except httpx.HTTPError as e:
            self.logger.error(f"Ollama API error: {str(e)}")
            raise LLMError(f"Ollama generation failed: {str(e)}")

    async def _generate_stream(
        self, prompt: str, model: str
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": True,
                        "temperature": self.config.temperature,
                        "top_k": self.config.top_k,
                        "top_p": self.config.top_p,
                        "num_predict": self.config.num_predict,
                    },
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line:
                            data = eval(line)  # Ollama returns JSON lines
                            if "response" in data:
                                yield data["response"]

        except httpx.HTTPError as e:
            self.logger.error(f"Ollama streaming error: {str(e)}")
            raise LLMError(f"Ollama streaming failed: {str(e)}")

    async def embed(self, text: str) -> list[float]:
        """
        Generate embedding using Ollama.

        Args:
            text: Text to embed

        Returns:
            Embedding vector

        Raises:
            LLMError: If embedding generation fails
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/embeddings",
                    json={
                        "model": self.embedding_model,
                        "prompt": text,
                    },
                )
                response.raise_for_status()
                result = response.json()
                return result.get("embedding", [])

        except httpx.HTTPError as e:
            self.logger.error(f"Ollama embedding error: {str(e)}")
            raise LLMError(f"Ollama embedding failed: {str(e)}")

    async def list_models(self) -> list[dict]:
        """
        List available models in Ollama.

        Returns:
            List of model information
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                result = response.json()
                return result.get("models", [])

        except httpx.HTTPError as e:
            self.logger.error(f"Failed to list models: {str(e)}")
            return []

    async def pull_model(self, model_name: str) -> bool:
        """
        Pull (download) a model from Ollama library.

        Args:
            model_name: Model name to pull

        Returns:
            True if successful

        Raises:
            LLMError: If pull fails
        """
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(None)) as client:
                response = await client.post(
                    f"{self.base_url}/api/pull",
                    json={"name": model_name},
                )
                response.raise_for_status()
                self.logger.info(f"Successfully pulled model: {model_name}")
                return True

        except httpx.HTTPError as e:
            self.logger.error(f"Failed to pull model {model_name}: {str(e)}")
            raise LLMError(f"Model pull failed: {str(e)}")

    async def delete_model(self, model_name: str) -> bool:
        """
        Delete a model from Ollama.

        Args:
            model_name: Model name to delete

        Returns:
            True if successful
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.delete(
                    f"{self.base_url}/api/show",
                    json={"name": model_name},
                )
                response.raise_for_status()
                self.logger.info(f"Successfully deleted model: {model_name}")
                return True

        except httpx.HTTPError as e:
            self.logger.error(f"Failed to delete model {model_name}: {str(e)}")
            return False


class OllamaLLMProvider:
    """LLM provider using Ollama for local inference."""

    def __init__(self, config: OllamaConfig):
        """
        Initialize Ollama LLM provider.

        Args:
            config: Ollama configuration
        """
        self.config = config
        self.client = OllamaClient(config)
        self.logger = get_logger(self.__class__.__name__)

    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> str:
        """
        Generate text completion.

        Args:
            prompt: Input prompt
            system_prompt: Optional system context
            **kwargs: Additional parameters

        Returns:
            Generated text
        """
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        return await self.client.generate(full_prompt, stream=False)

    async def generate_text_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """
        Generate streaming text completion.

        Args:
            prompt: Input prompt
            system_prompt: Optional system context
            **kwargs: Additional parameters

        Yields:
            Text chunks as they're generated
        """
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        async for chunk in await self.client.generate(full_prompt, stream=True):
            yield chunk

    async def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        embeddings = []
        for text in texts:
            embedding = await self.client.embed(text)
            embeddings.append(embedding)
        return embeddings

    async def health_check(self) -> bool:
        """
        Check if Ollama service is healthy.

        Returns:
            True if service is running
        """
        return await self.client.is_running()

    async def get_available_models(self) -> list[str]:
        """
        Get list of available models.

        Returns:
            Model names
        """
        models = await self.client.list_models()
        return [m["name"] for m in models]
