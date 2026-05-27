"""
Fact Checker Agent - Verifies factual claims against provided sources.
"""

from typing import Any
from src.core.base import BaseAgent, ExecutionResult
from src.core.types import AgentRole
from src.core.logger import get_logger
from src.services.llm_service import LLMService


class FactCheckerAgent(BaseAgent):
    """Agent responsible for fact-checking claims against sources."""

    def __init__(self, llm_service: LLMService | None = None):
        """
        Initialize Fact Checker Agent.

        Args:
            llm_service: LLMService instance. If None, a new one is created.
        """
        super().__init__(role=AgentRole.FACT_CHECKER, name="Fact Checker")
        self.llm_service = llm_service or LLMService()

    def validate_inputs(self, **kwargs: Any) -> bool:
        """Validate fact-checker inputs."""
        claims = kwargs.get("claims")
        if not isinstance(claims, list) or not claims:
            self.logger.warning("Invalid claims: must be a non-empty list")
            return False

        sources = kwargs.get("sources")
        if not isinstance(sources, list) or not sources:
            self.logger.warning("Invalid sources: must be a non-empty list")
            return False

        return True

    async def execute(self, **kwargs: Any) -> ExecutionResult:
        """
        Verify a list of claims against provided sources.

        Args:
            claims: List of claim strings to verify.
            sources: List of source text strings to check against.

        Returns:
            ExecutionResult containing a list of verification result dictionaries.
        """
        claims: list[str] = kwargs["claims"]
        sources: list[str] = kwargs["sources"]

        try:
            self.logger.info(f"Fact-checking {len(claims)} claim(s) against {len(sources)} source(s)")

            verification_results = []
            for claim in claims:
                try:
                    result = await self.llm_service.verify_claim(
                        claim=claim,
                        sources=sources,
                    )
                    verification_results.append(result)
                    self.logger.debug(f"Verified claim: {claim!r} -> confidence={result.get('confidence_score', 0):.2f}")
                except Exception as inner_e:
                    self.logger.warning(f"Failed to verify claim {claim!r}: {inner_e}")
                    verification_results.append({
                        "claim": claim,
                        "is_verified": False,
                        "confidence_score": 0.0,
                        "reasoning": f"Verification error: {inner_e}",
                    })

            # Compute aggregate statistics
            verified_count = sum(1 for r in verification_results if r.get("is_verified", False))
            avg_confidence = (
                sum(r.get("confidence_score", 0.0) for r in verification_results) / max(1, len(verification_results))
            )

            self.logger.info(
                f"Fact-checking complete: {verified_count}/{len(claims)} verified, "
                f"average confidence={avg_confidence:.2f}"
            )

            return ExecutionResult(
                success=True,
                data=verification_results,
                metadata={
                    "num_claims": len(claims),
                    "num_sources": len(sources),
                    "verified_count": verified_count,
                    "average_confidence": avg_confidence,
                },
            )

        except Exception as e:
            self.logger.error(f"Fact-checking failed: {e}")
            return ExecutionResult(
                success=False,
                error=str(e),
                metadata={"num_claims": len(claims), "num_sources": len(sources)},
            )
