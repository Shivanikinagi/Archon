"""
Citation Agent - Generates formatted citations in various academic styles.
"""

from typing import Any
from src.core.base import BaseAgent, ExecutionResult
from src.core.types import AgentRole, CitationStyle, Source, Citation
from src.core.logger import get_logger
from src.integration.citation_engine import CitationGenerator


class CitationAgent(BaseAgent):
    """Agent responsible for generating formatted citations."""

    def __init__(self):
        """Initialize Citation Agent."""
        super().__init__(role=AgentRole.WRITER, name="Citation Manager")
        self.generator = CitationGenerator()

    def validate_inputs(self, **kwargs: Any) -> bool:
        """Validate citation inputs."""
        sources = kwargs.get("sources")
        if not isinstance(sources, list) or not sources:
            self.logger.warning("Invalid sources: must be a non-empty list")
            return False

        style = kwargs.get("style")
        if not isinstance(style, CitationStyle):
            self.logger.warning(f"Invalid style: expected CitationStyle, got {type(style)}")
            return False

        return True

    async def execute(self, **kwargs: Any) -> ExecutionResult:
        """
        Generate formatted citations for the given sources.

        Args:
            sources: List of Source objects or dictionaries convertible to Source.
            style: Citation style (APA, MLA, Chicago, Harvard, IEEE).

        Returns:
            ExecutionResult containing a list of formatted Citation objects.
        """
        raw_sources: list = kwargs["sources"]
        style: CitationStyle = kwargs["style"]

        try:
            self.logger.info(f"Generating {style.value.upper()} citations for {len(raw_sources)} source(s)")

            citations = []
            for raw in raw_sources:
                source = self._coerce_source(raw)
                citation = self.generator.generate(source, style)
                citations.append(citation)

            self.logger.info(f"Generated {len(citations)} citation(s)")

            return ExecutionResult(
                success=True,
                data=citations,
                metadata={
                    "style": style.value,
                    "num_sources": len(raw_sources),
                    "num_citations": len(citations),
                },
            )

        except Exception as e:
            self.logger.error(f"Citation generation failed: {e}")
            return ExecutionResult(
                success=False,
                error=str(e),
                metadata={"style": style.value, "num_sources": len(raw_sources)},
            )

    def _coerce_source(self, raw: Any) -> Source:
        """Coerce a raw source into a Source dataclass instance."""
        if isinstance(raw, Source):
            return raw

        if isinstance(raw, dict):
            from datetime import datetime
            from src.core.types import SourceType

            pub_date = raw.get("publication_date")
            if isinstance(pub_date, str):
                try:
                    pub_date = datetime.fromisoformat(pub_date)
                except ValueError:
                    pub_date = None

            source_type = raw.get("source_type", "web")
            if isinstance(source_type, str):
                try:
                    source_type = SourceType(source_type)
                except ValueError:
                    source_type = SourceType.WEB

            return Source(
                url=raw.get("url", ""),
                title=raw.get("title", "Unknown Title"),
                source_type=source_type,
                retrieved_at=raw.get("retrieved_at") or datetime.now(),
                author=raw.get("author"),
                publication_date=pub_date,
                content_type=raw.get("content_type"),
                confidence=raw.get("confidence", 1.0),
            )

        # Fallback for objects with attributes
        from datetime import datetime
        from src.core.types import SourceType

        return Source(
            url=getattr(raw, "url", ""),
            title=getattr(raw, "title", "Unknown Title"),
            source_type=SourceType(getattr(raw, "source", "web")),
            retrieved_at=datetime.now(),
            author=getattr(raw, "author", None),
            publication_date=getattr(raw, "published_date", None),
            content_type=getattr(raw, "content_type", None),
            confidence=getattr(raw, "relevance_score", 1.0),
        )
