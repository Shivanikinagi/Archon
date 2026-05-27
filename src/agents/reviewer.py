"""
Reviewer Agent - Reviews research reports for quality, completeness, and tone.
"""

from typing import Any
from src.core.base import BaseAgent, ExecutionResult
from src.core.types import AgentRole
from src.core.logger import get_logger
from src.services.llm_service import LLMService


class ReviewerAgent(BaseAgent):
    """Agent responsible for reviewing report quality."""

    def __init__(self, llm_service: LLMService | None = None):
        """
        Initialize Reviewer Agent.

        Args:
            llm_service: LLMService instance. If None, a new one is created.
        """
        super().__init__(role=AgentRole.REVIEWER, name="Quality Reviewer")
        self.llm_service = llm_service or LLMService()

    def validate_inputs(self, **kwargs: Any) -> bool:
        """Validate reviewer inputs."""
        report = kwargs.get("report")
        if not isinstance(report, str) or not report.strip():
            self.logger.warning("Invalid report: must be a non-empty string")
            return False

        criteria = kwargs.get("criteria")
        if not isinstance(criteria, list) or not criteria:
            self.logger.warning("Invalid criteria: must be a non-empty list")
            return False

        return True

    async def execute(self, **kwargs: Any) -> ExecutionResult:
        """
        Review a research report against specified criteria.

        Args:
            report: The research report text to review.
            criteria: List of review criteria (e.g., "completeness", "tone", "accuracy").

        Returns:
            ExecutionResult containing structured review feedback.
        """
        report: str = kwargs["report"]
        criteria: list[str] = kwargs["criteria"]

        try:
            self.logger.info(f"Reviewing report ({len(report)} chars) against {len(criteria)} criteria")

            prompt = self._build_prompt(report, criteria)

            review_feedback = await self.llm_service.generate(
                prompt=prompt,
                temperature=0.3,
            )

            # Parse simple structured feedback
            scores = self._extract_scores(review_feedback)

            self.logger.info(f"Review complete with scores: {scores}")

            return ExecutionResult(
                success=True,
                data={
                    "feedback": review_feedback,
                    "scores": scores,
                },
                metadata={
                    "report_length": len(report),
                    "num_criteria": len(criteria),
                    "criteria": criteria,
                },
            )

        except Exception as e:
            self.logger.error(f"Review failed: {e}")
            return ExecutionResult(
                success=False,
                error=str(e),
                metadata={"report_length": len(report), "num_criteria": len(criteria)},
            )

    def _build_prompt(self, report: str, criteria: list[str]) -> str:
        """Build the review prompt."""
        criteria_text = "\n".join(f"- {c}" for c in criteria)
        return (
            "You are a quality reviewer for research reports. "
            "Please review the following report and provide structured feedback.\n\n"
            f"Review Criteria:\n{criteria_text}\n\n"
            f"Report:\n{report}\n\n"
            "Provide your review including: (1) an overall assessment, "
            "(2) strengths, (3) areas for improvement, and "
            "(4) a numeric score (0-10) for each criterion."
        )

    def _extract_scores(self, feedback: str) -> dict[str, float]:
        """Attempt to extract criterion scores from the feedback text."""
        import re

        scores = {}
        # Look for patterns like "Criterion: 8/10" or "Criterion: 8"
        for match in re.finditer(r"([\w\s]+)[\s:]*(\d+(?:\.\d+)?)\s*/?\s*10?", feedback):
            key = match.group(1).strip().lower()
            try:
                scores[key] = float(match.group(2))
            except ValueError:
                continue
        return scores
