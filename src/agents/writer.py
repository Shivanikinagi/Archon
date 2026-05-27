"""
Writer Agent - Synthesizes research findings into structured reports.
"""

from typing import Any
from src.core.base import BaseAgent, ExecutionResult
from src.core.types import AgentRole
from src.core.logger import get_logger
from src.services.llm_service import LLMService


class WriterAgent(BaseAgent):
    """Agent responsible for writing research reports."""

    def __init__(self, llm_service: LLMService | None = None):
        """
        Initialize Writer Agent.

        Args:
            llm_service: LLMService instance. If None, a new one is created.
        """
        super().__init__(role=AgentRole.WRITER, name="Report Writer")
        self.llm_service = llm_service or LLMService()

    def validate_inputs(self, **kwargs: Any) -> bool:
        """Validate writer inputs."""
        query = kwargs.get("query")
        if not isinstance(query, str) or not query.strip():
            self.logger.warning("Invalid query: must be a non-empty string")
            return False

        sources = kwargs.get("sources")
        if not isinstance(sources, list):
            self.logger.warning("Invalid sources: must be a list")
            return False

        outline = kwargs.get("outline")
        if not isinstance(outline, dict):
            self.logger.warning("Invalid outline: must be a dict")
            return False

        return True

    async def execute(self, **kwargs: Any) -> ExecutionResult:
        """
        Synthesize sources into a structured research report.

        Args:
            query: The research query or topic.
            sources: List of source data (search results, retrieval results, etc.).
            outline: Dictionary outlining the report structure.

        Returns:
            ExecutionResult containing the generated report text.
        """
        query: str = kwargs["query"]
        sources: list = kwargs["sources"]
        outline: dict = kwargs["outline"]

        try:
            self.logger.info(f"Writing report for query: {query!r}")

            # Build a comprehensive prompt from sources and outline
            prompt = self._build_prompt(query, sources, outline)

            report = await self.llm_service.generate(
                prompt=prompt,
                system=self.llm_service.SYSTEM_PROMPTS.get("report_writer"),
                temperature=0.5,
            )

            self.logger.info(f"Report generated ({len(report)} characters)")

            return ExecutionResult(
                success=True,
                data=report,
                metadata={
                    "query": query,
                    "num_sources": len(sources),
                    "report_length": len(report),
                },
            )

        except Exception as e:
            self.logger.error(f"Report writing failed: {e}")
            return ExecutionResult(
                success=False,
                error=str(e),
                metadata={"query": query},
            )

    def _build_prompt(self, query: str, sources: list, outline: dict) -> str:
        """Build the prompt for report generation."""
        sections = []
        sections.append(f"Research Topic: {query}\n")
        sections.append("Report Outline:")
        for key, value in outline.items():
            sections.append(f"  {key}: {value}")
        sections.append("\nSources:")
        for i, source in enumerate(sources, start=1):
            # Handle different source types gracefully
            if hasattr(source, "content"):
                content = source.content
            elif hasattr(source, "snippet"):
                content = source.snippet
            elif isinstance(source, dict):
                content = source.get("content") or source.get("snippet") or str(source)
            else:
                content = str(source)
            sections.append(f"[{i}] {content}")
        sections.append(
            "\nPlease synthesize the above sources into a comprehensive, well-structured "
            "research report following the provided outline. Cite sources where appropriate."
        )
        return "\n".join(sections)
