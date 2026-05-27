"""
Citation generation and management.
"""

from datetime import datetime
from src.core.types import Source, Citation, CitationStyle
from src.core.logger import get_logger

logger = get_logger(__name__)


class CitationGenerator:
    """Generate citations in various styles."""

    @staticmethod
    def generate(source: Source, style: CitationStyle) -> Citation:
        """
        Generate citation for a source.

        Args:
            source: Source to cite
            style: Citation style

        Returns:
            Citation object
        """
        formatted_text = CitationGenerator._format_citation(source, style)

        return Citation(
            source=source,
            style=style,
            formatted_text=formatted_text,
        )

    @staticmethod
    def _format_citation(source: Source, style: CitationStyle) -> str:
        """Format citation text based on style."""
        if style == CitationStyle.APA:
            return CitationGenerator._format_apa(source)
        elif style == CitationStyle.MLA:
            return CitationGenerator._format_mla(source)
        elif style == CitationStyle.CHICAGO:
            return CitationGenerator._format_chicago(source)
        elif style == CitationStyle.HARVARD:
            return CitationGenerator._format_harvard(source)
        elif style == CitationStyle.IEEE:
            return CitationGenerator._format_ieee(source)
        else:
            return CitationGenerator._format_apa(source)

    @staticmethod
    def _format_apa(source: Source) -> str:
        """Format APA citation."""
        author = source.author or "Unknown"
        title = source.title or "Unknown Title"
        year = source.publication_date.year if source.publication_date else "n.d."

        if source.source_type.value == "web":
            return (
                f"{author}. ({year}). {title}. Retrieved from {source.url}"
            )
        else:
            return f"{author}. ({year}). {title}."

    @staticmethod
    def _format_mla(source: Source) -> str:
        """Format MLA citation."""
        author = source.author or "Unknown"
        title = source.title or "Unknown Title"
        date = (
            source.publication_date.strftime("%d %b. %Y")
            if source.publication_date
            else "n.d."
        )

        if source.source_type.value == "web":
            return f"{author}. \"{title}.\" Accessed on {date}. {source.url}"
        else:
            return f"{author}. \"{title}.\""

    @staticmethod
    def _format_chicago(source: Source) -> str:
        """Format Chicago citation."""
        author = source.author or "Unknown"
        title = source.title or "Unknown Title"
        year = source.publication_date.year if source.publication_date else "n.d."

        if source.source_type.value == "web":
            return f"{author}. \"{title}.\" Accessed {year}. {source.url}."
        else:
            return f"{author}. {title}. {year}."

    @staticmethod
    def _format_harvard(source: Source) -> str:
        """Format Harvard citation."""
        author = source.author or "Unknown"
        title = source.title or "Unknown Title"
        year = source.publication_date.year if source.publication_date else "n.d."

        if source.source_type.value == "web":
            return f"{author} {year}. {title}. Available at: {source.url}"
        else:
            return f"{author}, {year}. {title}."

    @staticmethod
    def _format_ieee(source: Source) -> str:
        """Format IEEE citation."""
        author = source.author or "Unknown"
        title = source.title or "Unknown Title"
        year = source.publication_date.year if source.publication_date else "n.d."

        if source.source_type.value == "web":
            return f"[Online] {author}, \"{title},\" {year}. Available: {source.url}"
        else:
            return f"{author}, \"{title},\" {year}."


class BibliographyGenerator:
    """Generate formatted bibliographies."""

    @staticmethod
    def generate(citations: list[Citation], style: CitationStyle) -> str:
        """
        Generate formatted bibliography.

        Args:
            citations: List of citations
            style: Citation style

        Returns:
            Formatted bibliography text
        """
        # Sort by author
        sorted_citations = sorted(
            citations,
            key=lambda c: c.source.author or "Unknown",
        )

        lines = []
        for citation in sorted_citations:
            lines.append(citation.formatted_text)

        return "\n".join(lines)
