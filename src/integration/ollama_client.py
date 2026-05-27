"""Ollama LLM client integration

Provides async HTTP client for local Ollama inference.
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any, AsyncGenerator
import httpx
import json

logger = logging.getLogger(__name__)


class OllamaClient:
    """Ollama client for local LLM inference"""
    
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "mistral",
        timeout: int = 300,
    ):
        """
        Initialize Ollama client
        
        Args:
            base_url: Ollama server base URL
            model: Model name (mistral, neural-chat, etc.)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url
        self.model = model
        self.timeout = timeout
        self.client: Optional[httpx.AsyncClient] = None
    
    async def init(self) -> None:
        """
        Initialize HTTP client and verify connection
        
        Raises:
            Exception: If connection fails
        """
        try:
            self.client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
            )
            
            # Test connection
            response = await self.client.get("/api/tags")
            response.raise_for_status()
            
            logger.info(f"✓ Ollama client initialized (base_url={self.base_url}, model={self.model})")
        except Exception as e:
            logger.error(f"✗ Failed to initialize Ollama client: {e}")
            raise
    
    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        top_p: float = 0.95,
        top_k: int = 40,
        stream: bool = False,
    ) -> str:
        """
        Generate text using LLM
        
        Args:
            prompt: Input prompt
            system: Optional system message
            temperature: Randomness (0.0-1.0)
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling parameter
            stream: Whether to stream response
            
        Returns:
            Generated text
            
        Raises:
            Exception: If generation fails
        """
        if not self.client:
            raise RuntimeError("Ollama client not initialized")
        
        try:
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            
            response = await self.client.post(
                "/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": stream,
                    "options": {
                        "temperature": temperature,
                        "top_p": top_p,
                        "top_k": top_k,
                    }
                }
            )
            response.raise_for_status()
            
            if stream:
                # For streaming, collect all chunks
                full_response = ""
                async for line in response.aiter_lines():
                    if line:
                        data = json.loads(line)
                        if "message" in data and "content" in data["message"]:
                            full_response += data["message"]["content"]
                return full_response
            else:
                # Non-streaming response
                data = response.json()
                return data.get("message", {}).get("content", "")
        
        except Exception as e:
            logger.error(f"✗ Generation failed: {e}")
            raise
    
    async def generate_stream(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        top_p: float = 0.95,
        top_k: int = 40,
    ) -> AsyncGenerator[str, None]:
        """
        Generate text with streaming response
        
        Args:
            prompt: Input prompt
            system: Optional system message
            temperature: Randomness (0.0-1.0)
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling parameter
            
        Yields:
            Text chunks as they're generated
            
        Raises:
            Exception: If generation fails
        """
        if not self.client:
            raise RuntimeError("Ollama client not initialized")
        
        try:
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            
            response = await self.client.post(
                "/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": True,
                    "options": {
                        "temperature": temperature,
                        "top_p": top_p,
                        "top_k": top_k,
                    }
                }
            )
            response.raise_for_status()
            
            async for line in response.aiter_lines():
                if line:
                    data = json.loads(line)
                    if "message" in data and "content" in data["message"]:
                        yield data["message"]["content"]
        
        except Exception as e:
            logger.error(f"✗ Streaming generation failed: {e}")
            raise
    
    async def embeddings(
        self,
        text: str,
        embedding_model: str = "nomic-embed-text",
    ) -> List[float]:
        """
        Generate embeddings for text
        
        Args:
            text: Text to embed
            embedding_model: Embedding model name
            
        Returns:
            Embedding vector (384-dimensional for nomic-embed-text)
            
        Raises:
            Exception: If embedding fails
        """
        if not self.client:
            raise RuntimeError("Ollama client not initialized")
        
        try:
            response = await self.client.post(
                "/api/embeddings",
                json={
                    "model": embedding_model,
                    "prompt": text,
                }
            )
            response.raise_for_status()
            
            data = response.json()
            embedding = data.get("embedding", [])
            
            logger.debug(f"✓ Generated embedding with {len(embedding)} dimensions")
            return embedding
        
        except Exception as e:
            logger.error(f"✗ Embedding generation failed: {e}")
            raise
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """
        List available models on Ollama server
        
        Returns:
            List of model information dictionaries
        """
        if not self.client:
            raise RuntimeError("Ollama client not initialized")
        
        try:
            response = await self.client.get("/api/tags")
            response.raise_for_status()
            
            data = response.json()
            models = data.get("models", [])
            
            logger.debug(f"✓ Found {len(models)} models on Ollama server")
            return models
        
        except Exception as e:
            logger.error(f"✗ Failed to list models: {e}")
            raise
    
    async def pull_model(self, model_name: str) -> bool:
        """
        Pull a model from Ollama registry
        
        Args:
            model_name: Model name to pull
            
        Returns:
            Success flag
        """
        if not self.client:
            raise RuntimeError("Ollama client not initialized")
        
        try:
            response = await self.client.post(
                "/api/pull",
                json={"name": model_name}
            )
            response.raise_for_status()
            
            logger.info(f"✓ Successfully pulled model: {model_name}")
            return True
        
        except Exception as e:
            logger.error(f"✗ Failed to pull model: {e}")
            raise
    
    async def model_info(self) -> Dict[str, Any]:
        """
        Get information about current model
        
        Returns:
            Model information
        """
        if not self.client:
            raise RuntimeError("Ollama client not initialized")
        
        try:
            response = await self.client.post(
                "/api/show",
                json={"name": self.model}
            )
            response.raise_for_status()
            
            return response.json()
        
        except Exception as e:
            logger.error(f"✗ Failed to get model info: {e}")
            raise
    
    async def count_tokens(
        self,
        text: str,
    ) -> int:
        """
        Estimate token count for text
        
        This is an approximation based on text length.
        For accurate token counting, use the model's tokenizer.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Estimated token count
        """
        # Rough approximation: 1 token ~= 4 characters
        # More accurate: use actual tokenizer from transformers
        estimated_tokens = len(text) // 4
        
        logger.debug(f"✓ Estimated {estimated_tokens} tokens for text")
        return estimated_tokens
    
    async def close(self) -> None:
        """Close HTTP client"""
        try:
            if self.client:
                await self.client.aclose()
                self.client = None
                logger.info("✓ Ollama client connection closed")
        except Exception as e:
            logger.error(f"✗ Failed to close Ollama client: {e}")
            raise


# Global Ollama client instance
_ollama_client: Optional[OllamaClient] = None


async def init_ollama(
    base_url: str = "http://localhost:11434",
    model: str = "mistral",
    timeout: int = 300,
) -> None:
    """
    Initialize global Ollama client
    
    Args:
        base_url: Ollama server base URL
        model: Default model name
        timeout: Request timeout in seconds
    """
    global _ollama_client
    _ollama_client = OllamaClient(base_url, model, timeout)
    await _ollama_client.init()


async def close_ollama() -> None:
    """Close global Ollama client"""
    global _ollama_client
    if _ollama_client:
        await _ollama_client.close()
        _ollama_client = None


def get_ollama_client() -> OllamaClient:
    """Get global Ollama client"""
    if _ollama_client is None:
        raise RuntimeError("Ollama client not initialized. Call init_ollama() first.")
    return _ollama_client
