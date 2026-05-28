"""
Analytical Writer Agent - Synthesizes research into structured, analytical reports.

Key improvements over generic writer:
- Analytical tone (comparisons, architectures, limitations, trends)
- Comparison table generation
- Section-level confidence scores
- Focus on recent advancements rather than generic descriptions
"""

import json
from typing import Any
from core.base import BaseAgent, ExecutionResult
from core.types import AgentRole
from core.logger import get_logger
from services.llm_service import LLMService

logger = get_logger(__name__)


ANALYTICAL_SYSTEM_PROMPT = """You are an elite research analyst and technical writer. Your reports are known for:

1. ANALYTICAL DEPTH: Never just describe "what" something is. Analyze "how" it works, "why" it matters, and "what" the implications are.
2. COMPARATIVE ANALYSIS: Always compare approaches, models, architectures, or companies side-by-side when multiple exist.
3. TECHNICAL SPECIFICITY: Name specific models (GPT-4o, Gemini 1.5 Pro, Claude 3.5 Sonnet), architectures (Transformer, MoE, Diffusion), benchmarks (MMLU, HumanEval, MMMU), and quantitative results.
4. CRITICAL EVALUATION: Highlight limitations, failure modes, trade-offs, and open problems. No technology is perfect.
5. TEMPORAL AWARENESS: Focus on RECENT developments (2023-2025). Cite release dates, version numbers, and timeline of improvements.
6. ECOSYSTEM MAPPING: Show how entities (companies, models, standards) relate to each other — partnerships, competition, dependencies.

AVOID:
- Generic statements like "X has many applications" or "Y is widely used"
- Wikipedia-style definitional paragraphs
- Unqualified superlatives without evidence

STRUCTURE:
- Executive Summary with key findings
- Comparative Analysis Tables (markdown tables)
- Technical Architecture Deep-Dives
- Limitations & Trade-offs
- Recent Advancements Timeline
- Future Outlook & Open Problems
- Confidence Assessment per section
"""


class WriterAgent(BaseAgent):
    """Agent responsible for writing analytical research reports."""

    def __init__(self, llm_service: LLMService | None = None):
        super().__init__(role=AgentRole.WRITER, name="Analytical Report Writer")
        self.llm_service = llm_service or LLMService()

    def validate_inputs(self, **kwargs: Any) -> bool:
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
        query: str = kwargs["query"]
        sources: list = kwargs["sources"]
        outline: dict = kwargs["outline"]
        confidence_data: dict = kwargs.get("confidence_data", {})

        try:
            self.logger.info(f"Writing analytical report for query: {query!r}")

            # Step 1: Generate comparison table if multiple entities detected
            comparison_table = await self._generate_comparison_table(query, sources)

            # Step 2: Build analytical prompt
            prompt = self._build_analytical_prompt(query, sources, outline, comparison_table)

            # Step 3: Generate report
            report = await self.llm_service.generate(
                prompt=prompt,
                system=ANALYTICAL_SYSTEM_PROMPT,
                temperature=0.4,
            )

            # Step 4: Post-process: add confidence annotations
            report_with_confidence = self._inject_confidence_scores(report, confidence_data)

            self.logger.info(f"Analytical report generated ({len(report_with_confidence)} characters)")

            return ExecutionResult(
                success=True,
                data=report_with_confidence,
                metadata={
                    "query": query,
                    "num_sources": len(sources),
                    "report_length": len(report_with_confidence),
                    "has_comparison_table": comparison_table is not None,
                    "confidence_data": confidence_data,
                },
            )

        except Exception as e:
            self.logger.error(f"Report writing failed: {e}")
            return ExecutionResult(
                success=False,
                error=str(e),
                metadata={"query": query},
            )

    async def _generate_comparison_table(self, query: str, sources: list) -> str | None:
        """Generate a comparison table if the query involves multiple entities."""
        # Detect if query is comparison-friendly
        comparison_keywords = [
            "compare", "versus", "vs", "difference", "between",
            "openai", "google", "microsoft", "nvidia", "anthropic",
            "meta", "amazon", "apple", "tesla", "deepmind",
            "gpt", "claude", "gemini", "llama", "mistral",
            "architecture", "model", "framework", "platform",
        ]
        is_comparison = any(kw in query.lower() for kw in comparison_keywords)

        if not is_comparison or len(sources) < 3:
            return None

        self.logger.info("Generating comparison table")

        table_prompt = f"""Based on the research topic "{query}" and the provided sources, create a detailed comparison table in markdown format.

Requirements:
1. Include at least 4-6 columns covering: Name/Entity, Key Capability, Architecture/Approach, Strengths, Limitations, Recent Milestone
2. Focus on SPECIFIC, QUANTITATIVE comparisons (not generic descriptions)
3. Include actual numbers, dates, and version numbers where possible
4. The table should be directly usable in a technical report

Format as a markdown table with proper headers.
"""
        try:
            table = await self.llm_service.generate(
                prompt=table_prompt,
                system=ANALYTICAL_SYSTEM_PROMPT,
                temperature=0.3,
            )
            if "|" in table:
                return table
        except Exception as e:
            self.logger.warning(f"Comparison table generation failed: {e}")
        return None

    def _build_analytical_prompt(self, query: str, sources: list, outline: dict, comparison_table: str | None) -> str:
        sections = []
        sections.append(f"# Research Topic: {query}\n")
        sections.append("## Report Structure Requirements:\n")
        sections.append("""
1. Executive Summary (3-4 sentences with key quantitative findings)
2. Comparative Analysis (use the comparison table or create one)
3. Technical Architecture Deep-Dive (specific models, methods, benchmarks)
4. Recent Advancements (2023-2025 timeline with dates)
5. Limitations & Trade-offs (critical evaluation, not generic)
6. Ecosystem & Relationships (how key players connect)
7. Future Outlook & Open Problems
8. Confidence Assessment (score each section 0.0-1.0)
""")

        if comparison_table:
            sections.append(f"\n## Pre-generated Comparison Table:\n{comparison_table}\n")
            sections.append("Incorporate and expand on this table in your report.\n")

        sections.append("\n## Source Materials:\n")
        for i, source in enumerate(sources[:15], start=1):  # Cap at 15 sources
            content = self._extract_source_text(source)
            sections.append(f"### Source [{i}]\n{content[:800]}\n")  # Truncate long sources

        sections.append(f"""
## Writing Instructions:

- TONE: Analytical and critical. Avoid encyclopedic descriptions.
- FOCUS: Recent advancements, quantitative comparisons, architectural details.
- TABLES: Include at least one markdown comparison table.
- CONFIDENCE: After each major section, add: `**Confidence Score: X.XX**` based on source quality and consensus.
- ENTITIES: If the query involves companies/products/models, map their relationships explicitly.

Begin the report now.
""")
        return "\n".join(sections)

    def _extract_source_text(self, source: Any) -> str:
        if hasattr(source, "content"):
            return str(source.content)
        elif hasattr(source, "snippet"):
            return str(source.snippet)
        elif hasattr(source, "title") and hasattr(source, "url"):
            title = getattr(source, "title", "")
            snippet = getattr(source, "snippet", "")
            return f"{title}\n{snippet}"
        elif isinstance(source, dict):
            return str(source.get("content") or source.get("snippet") or source.get("title", str(source)))
        return str(source)

    def _inject_confidence_scores(self, report: str, confidence_data: dict) -> str:
        """Add overall confidence summary to the report."""
        if not confidence_data:
            return report

        overall = confidence_data.get("overall", 0.0)
        by_section = confidence_data.get("by_section", {})

        summary = "\n\n---\n\n## Confidence Assessment\n\n"
        summary += f"**Overall Report Confidence: {overall:.2f}/1.00**\n\n"
        if by_section:
            summary += "| Section | Confidence |\n"
            summary += "|---------|------------|\n"
            for section, score in by_section.items():
                bar = "█" * int(score * 10) + "░" * (10 - int(score * 10))
                summary += f"| {section} | {bar} {score:.2f} |\n"

        return report + summary
