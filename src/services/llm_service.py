"""LLM service for higher-level language model operations

Provides prompt templates, response parsing, and generation utilities.
"""

import logging
from typing import Optional, AsyncGenerator, Dict, Any, List
from src.integration.ollama_client import get_ollama_client
import re

logger = logging.getLogger(__name__)


class PromptTemplate:
    """Simple prompt template with variable substitution"""
    
    def __init__(self, template: str):
        """
        Initialize prompt template
        
        Args:
            template: Template string with {variable} placeholders
        """
        self.template = template
    
    def format(self, **kwargs) -> str:
        """
        Format template with variables
        
        Args:
            **kwargs: Variables to substitute
            
        Returns:
            Formatted prompt
        """
        return self.template.format(**kwargs)


class LLMService:
    """High-level LLM service with prompt management and response parsing"""
    
    # System prompts for different tasks
    SYSTEM_PROMPTS = {
        "research_planner": """You are a research planning expert. Your task is to create a comprehensive research plan for investigating a given topic.

For each research query, provide:
1. Key research questions
2. Main research areas to cover
3. Search strategies
4. Expected sources and resources

Be specific and actionable.""",

        "web_researcher": """You are a web research expert. Your task is to extract and summarize key information from search results.

For each search result provided:
1. Identify the main topic
2. Extract key facts and insights
3. Assess source reliability
4. Note any contradictions with other sources

Be concise and factual.""",

        "fact_checker": """You are a fact-checking expert. Your task is to verify claims against provided sources.

For each claim:
1. Check if it's supported by the sources
2. Assign a confidence score (0.0-1.0)
3. Note any contradicting information
4. Flag uncertain claims for further research

Be objective and evidence-based.""",

        "report_writer": """You are a research report writer. Your task is to synthesize information into a well-structured report.

Guidelines:
1. Use clear, professional language
2. Organize information logically
3. Support claims with citations
4. Highlight key findings and insights
5. Make recommendations where appropriate

Create a comprehensive, well-formatted report.""",

        "summary": """You are a summarization expert. Create a concise, accurate summary of the provided content.

Focus on:
1. Main ideas and key points
2. Important details and numbers
3. Conclusions and implications

Be clear and concise.""",
    }
    
    def __init__(self, model: str = "mistral"):
        """
        Initialize LLM service
        
        Args:
            model: Model name to use
        """
        self.model = model
        self.templates: Dict[str, PromptTemplate] = {}
        self._register_default_templates()
    
    def _register_default_templates(self) -> None:
        """Register default prompt templates"""
        
        self.templates["research_query"] = PromptTemplate(
            "Research the following topic and provide comprehensive information:\n\n{query}"
        )
        
        self.templates["extract_claims"] = PromptTemplate(
            "Extract all factual claims from the following text:\n\n{text}\n\nList each claim as a separate item."
        )
        
        self.templates["verify_claim"] = PromptTemplate(
            "Given the following claim and sources, determine if the claim is supported:\n\nClaim: {claim}\n\nSources:\n{sources}"
        )
        
        self.templates["summarize"] = PromptTemplate(
            "Summarize the following content in 2-3 sentences:\n\n{content}"
        )
        
        self.templates["expand"] = PromptTemplate(
            "Expand on the following idea with more details and examples:\n\n{idea}"
        )
    
    def register_template(self, name: str, template_str: str) -> None:
        """
        Register custom prompt template
        
        Args:
            name: Template name
            template_str: Template string with {variable} placeholders
        """
        self.templates[name] = PromptTemplate(template_str)
        logger.debug(f"✓ Registered template: {name}")
    
    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate response for prompt
        
        Args:
            prompt: Input prompt
            system: Optional system message
            temperature: Randomness (0.0-1.0)
            max_tokens: Optional token limit
            
        Returns:
            Generated response
            
        Raises:
            Exception: If generation fails
        """
        try:
            ollama = get_ollama_client()
            response = await ollama.generate(
                prompt=prompt,
                system=system,
                temperature=temperature,
                stream=False,
            )
            
            logger.debug(f"✓ Generated response ({len(response)} chars)")
            return response
        
        except Exception as e:
            logger.error(f"✗ Generation failed: {e}")
            raise
    
    async def generate_stream(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
    ) -> AsyncGenerator[str, None]:
        """
        Generate response with streaming
        
        Args:
            prompt: Input prompt
            system: Optional system message
            temperature: Randomness (0.0-1.0)
            
        Yields:
            Response chunks as they're generated
            
        Raises:
            Exception: If generation fails
        """
        try:
            ollama = get_ollama_client()
            async for chunk in ollama.generate_stream(
                prompt=prompt,
                system=system,
                temperature=temperature,
            ):
                yield chunk
        
        except Exception as e:
            logger.error(f"✗ Streaming generation failed: {e}")
            raise
    
    async def research_query(
        self,
        query: str,
        temperature: float = 0.5,
    ) -> str:
        """
        Generate research response for query
        
        Args:
            query: Research query
            temperature: Randomness (0.0-1.0)
            
        Returns:
            Research response
        """
        prompt = self.templates["research_query"].format(query=query)
        system = self.SYSTEM_PROMPTS["research_planner"]
        
        return await self.generate(
            prompt=prompt,
            system=system,
            temperature=temperature,
        )
    
    async def extract_claims(self, text: str) -> List[str]:
        """
        Extract factual claims from text
        
        Args:
            text: Text to extract claims from
            
        Returns:
            List of extracted claims
        """
        try:
            prompt = self.templates["extract_claims"].format(text=text)
            system = self.SYSTEM_PROMPTS["research_planner"]
            
            response = await self.generate(
                prompt=prompt,
                system=system,
                temperature=0.3,  # Low temperature for accuracy
            )
            
            # Parse response to extract claims (one per line)
            claims = [line.strip() for line in response.split("\n") if line.strip() and not line.startswith("#")]
            logger.info(f"✓ Extracted {len(claims)} claims")
            return claims
        
        except Exception as e:
            logger.error(f"✗ Claim extraction failed: {e}")
            raise
    
    async def verify_claim(
        self,
        claim: str,
        sources: List[str],
    ) -> Dict[str, Any]:
        """
        Verify claim against sources
        
        Args:
            claim: Claim to verify
            sources: List of source texts
            
        Returns:
            Verification result with confidence score
        """
        try:
            sources_text = "\n\n".join([f"Source {i+1}: {source}" for i, source in enumerate(sources)])
            
            prompt = self.templates["verify_claim"].format(
                claim=claim,
                sources=sources_text,
            )
            system = self.SYSTEM_PROMPTS["fact_checker"]
            
            response = await self.generate(
                prompt=prompt,
                system=system,
                temperature=0.3,  # Low temperature for accuracy
            )
            
            # Extract confidence score (0.0-1.0)
            confidence = self._extract_confidence(response)
            
            result = {
                "claim": claim,
                "is_verified": confidence > 0.7,
                "confidence_score": confidence,
                "reasoning": response,
            }
            
            logger.info(f"✓ Verified claim with confidence {confidence:.2f}")
            return result
        
        except Exception as e:
            logger.error(f"✗ Claim verification failed: {e}")
            raise
    
    async def summarize(self, content: str) -> str:
        """
        Summarize content
        
        Args:
            content: Content to summarize
            
        Returns:
            Summary
        """
        try:
            prompt = self.templates["summarize"].format(content=content)
            system = self.SYSTEM_PROMPTS["summary"]
            
            response = await self.generate(
                prompt=prompt,
                system=system,
                temperature=0.5,
            )
            
            logger.debug(f"✓ Generated summary ({len(response)} chars)")
            return response
        
        except Exception as e:
            logger.error(f"✗ Summarization failed: {e}")
            raise
    
    def _extract_confidence(self, text: str) -> float:
        """
        Extract confidence score from response text
        
        Args:
            text: Response text
            
        Returns:
            Confidence score (0.0-1.0)
        """
        # Look for percentage
        percentages = re.findall(r"(\d+)\s*%", text)
        if percentages:
            return float(percentages[0]) / 100.0
        
        # Look for explicit confidence score
        confidence_matches = re.findall(r"confidence[:\s]*(\d+\.?\d*)", text, re.IGNORECASE)
        if confidence_matches:
            score = float(confidence_matches[0])
            if score > 1.0:
                return score / 100.0
            return score
        
        # Default to 0.5 if not found
        return 0.5
    
    async def count_tokens(self, text: str) -> int:
        """
        Estimate token count for text
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Estimated token count
        """
        ollama = get_ollama_client()
        return await ollama.count_tokens(text)
