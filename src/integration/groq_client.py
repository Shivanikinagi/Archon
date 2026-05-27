"""
Groq API integration for fast LLM inference.
"""

import httpx
from typing import Optional, AsyncGenerator
from src.core.logger import get_logger
from src.core.exceptions import LLMError

logger = get_logger(__name__)


class GroqClient:
    """Client for interacting with Groq API."""

    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile"):
        """
        Initialize Groq client.

        Args:
            api_key: Groq API key
            model: Model name (default: llama-3.3-70b-versatile)
        """
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.groq.com/openai/v1"
        self.timeout = httpx.Timeout(120.0)
        self.logger = get_logger(self.__class__.__name__)

    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """
        Generate text using Groq API.

        Args:
            prompt: Input prompt
            system_prompt: Optional system context
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text

        Raises:
            LLMError: If generation fails
        """
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    },
                )
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"]

        except httpx.HTTPError as e:
            self.logger.error(f"Groq API error: {str(e)}")
            raise LLMError(f"Groq generation failed: {str(e)}")

    async def health_check(self) -> bool:
        """
        Check if Groq API is accessible.

        Returns:
            True if API is accessible
        """
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                return response.status_code == 200
        except Exception as e:
            self.logger.warning(f"Groq API not accessible: {str(e)}")
            return False


class GroqLLMProvider:
    """LLM provider using Groq for fast inference."""

    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile"):
        """
        Initialize Groq LLM provider.

        Args:
            api_key: Groq API key
            model: Model name
        """
        self.client = GroqClient(api_key, model)
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
        return await self.client.generate_text(prompt, system_prompt, **kwargs)

    async def health_check(self) -> bool:
        """
        Check if Groq service is healthy.

        Returns:
            True if service is accessible
        """
        return await self.client.health_check()
