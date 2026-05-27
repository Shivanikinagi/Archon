"""
Workflow Orchestration - Coordinates all research agents in a state machine.

States:
    plan -> search -> retrieve -> write -> fact_check -> review -> cite -> done
"""

import asyncio
from typing import Any
from enum import Enum
from datetime import datetime

from src.core.base import ExecutionResult
from src.core.types import AgentRole, CitationStyle, ResearchQuery, ResearchDepth
from src.core.logger import get_logger

from src.agents.planner import PlannerAgent
from src.agents.web_search import WebSearchAgent
from src.agents.academic_search import AcademicSearchAgent
from src.agents.document_search import DocumentSearchAgent
from src.agents.writer import WriterAgent
from src.agents.fact_checker import FactCheckerAgent
from src.agents.reviewer import ReviewerAgent
from src.agents.citation_agent import CitationAgent

from src.services.llm_service import LLMService
from src.services.search_service import SearchService
from src.services.retrieval_service import RetrievalService


class WorkflowState(str, Enum):
    """States in the research workflow."""

    PLAN = "plan"
    SEARCH = "search"
    RETRIEVE = "retrieve"
    WRITE = "write"
    FACT_CHECK = "fact_check"
    REVIEW = "review"
    CITE = "cite"
    DONE = "done"
    FAILED = "failed"


class ResearchWorkflow:
    """Orchestrates the full research pipeline using a simple state machine."""

    def __init__(
        self,
        planner: PlannerAgent | None = None,
        web_searcher: WebSearchAgent | None = None,
        academic_searcher: AcademicSearchAgent | None = None,
        document_searcher: DocumentSearchAgent | None = None,
        writer: WriterAgent | None = None,
        fact_checker: FactCheckerAgent | None = None,
        reviewer: ReviewerAgent | None = None,
        citation_agent: CitationAgent | None = None,
    ):
        """
        Initialize the research workflow.

        Args:
            planner: PlannerAgent instance.
            web_searcher: WebSearchAgent instance.
            academic_searcher: AcademicSearchAgent instance.
            document_searcher: DocumentSearchAgent instance.
            writer: WriterAgent instance.
            fact_checker: FactCheckerAgent instance.
            reviewer: ReviewerAgent instance.
            citation_agent: CitationAgent instance.
        """
        self.planner = planner or PlannerAgent()
        self.web_searcher = web_searcher or WebSearchAgent()
        self.academic_searcher = academic_searcher or AcademicSearchAgent()
        self.document_searcher = document_searcher or DocumentSearchAgent()
        self.writer = writer or WriterAgent()
        self.fact_checker = fact_checker or FactCheckerAgent()
        self.reviewer = reviewer or ReviewerAgent()
        self.citation_agent = citation_agent or CitationAgent()

        self.logger = get_logger(self.__class__.__name__)

    async def run(self, query: str) -> dict:
        """
        Execute the full research workflow for a given query.

        Args:
            query: The research query string.

        Returns:
            Dictionary containing the final report, citations, review, and metadata.
        """
        self.logger.info(f"Starting research workflow for query: {query!r}")

        state = WorkflowState.PLAN
        context: dict[str, Any] = {
            "query": query,
            "state": state,
            "plan": None,
            "web_results": [],
            "academic_results": [],
            "document_results": [],
            "all_sources": [],
            "report": None,
            "verification_results": None,
            "review_feedback": None,
            "citations": None,
            "errors": [],
            "started_at": datetime.now(),
        }

        try:
            while state != WorkflowState.DONE and state != WorkflowState.FAILED:
                self.logger.info(f"Workflow state: {state.value}")

                if state == WorkflowState.PLAN:
                    state = await self._run_plan(context)
                elif state == WorkflowState.SEARCH:
                    state = await self._run_search(context)
                elif state == WorkflowState.RETRIEVE:
                    state = await self._run_retrieve(context)
                elif state == WorkflowState.WRITE:
                    state = await self._run_write(context)
                elif state == WorkflowState.FACT_CHECK:
                    state = await self._run_fact_check(context)
                elif state == WorkflowState.REVIEW:
                    state = await self._run_review(context)
                elif state == WorkflowState.CITE:
                    state = await self._run_cite(context)
                else:
                    self.logger.error(f"Unknown workflow state: {state}")
                    context["errors"].append(f"Unknown state: {state}")
                    state = WorkflowState.FAILED

                context["state"] = state

        except Exception as e:
            self.logger.error(f"Workflow failed with exception: {e}")
            context["errors"].append(str(e))
            context["state"] = WorkflowState.FAILED

        context["finished_at"] = datetime.now()
        context["duration_seconds"] = (
            context["finished_at"] - context["started_at"]
        ).total_seconds()

        self.logger.info(
            f"Workflow finished in state {context['state'].value} "
            f"after {context['duration_seconds']:.2f}s"
        )

        return self._build_output(context)

    async def _run_plan(self, context: dict) -> WorkflowState:
        """Run the planner agent."""
        result = await self.planner.run(query=context["query"])
        if not result.success:
            context["errors"].append(f"Planning failed: {result.error}")
            return WorkflowState.FAILED

        context["plan"] = result.data
        self.logger.info(f"Plan created with {len(result.data.search_queries)} search queries")
        return WorkflowState.SEARCH

    async def _run_search(self, context: dict) -> WorkflowState:
        """Run web and academic search agents."""
        plan = context.get("plan")
        search_queries = [context["query"]]
        if plan and hasattr(plan, "search_queries"):
            search_queries = plan.search_queries

        web_tasks = [
            self.web_searcher.run(query=q, num_results=10)
            for q in search_queries
        ]
        academic_tasks = [
            self.academic_searcher.run(query=q, num_results=10)
            for q in search_queries
        ]

        web_results_list = await asyncio.gather(*web_tasks, return_exceptions=True)
        academic_results_list = await asyncio.gather(*academic_tasks, return_exceptions=True)

        web_results = []
        for res in web_results_list:
            if isinstance(res, Exception):
                self.logger.warning(f"Web search task failed: {res}")
                context["errors"].append(f"Web search failed: {res}")
            elif res.success and res.data:
                web_results.extend(res.data)

        academic_results = []
        for res in academic_results_list:
            if isinstance(res, Exception):
                self.logger.warning(f"Academic search task failed: {res}")
                context["errors"].append(f"Academic search failed: {res}")
            elif res.success and res.data:
                academic_results.extend(res.data)

        context["web_results"] = web_results
        context["academic_results"] = academic_results
        context["all_sources"] = web_results + academic_results

        self.logger.info(
            f"Search complete: {len(web_results)} web, {len(academic_results)} academic results"
        )
        return WorkflowState.RETRIEVE

    async def _run_retrieve(self, context: dict) -> WorkflowState:
        """Run document retrieval agent."""
        result = await self.document_searcher.run(
            query=context["query"],
            top_k=10,
        )
        if result.success and result.data:
            context["document_results"] = result.data
            context["all_sources"].extend(result.data)
            self.logger.info(f"Document retrieval returned {len(result.data)} results")
        else:
            if result.error:
                self.logger.warning(f"Document retrieval failed: {result.error}")
                context["errors"].append(f"Document retrieval failed: {result.error}")
            else:
                self.logger.info("No indexed documents found; continuing without them")

        return WorkflowState.WRITE

    async def _run_write(self, context: dict) -> WorkflowState:
        """Run the writer agent."""
        sources = context.get("all_sources", [])
        outline = {"sections": ["Introduction", "Body", "Conclusion"]}
        if context.get("plan") and hasattr(context["plan"], "subtopics"):
            outline["sections"] = context["plan"].subtopics

        result = await self.writer.run(
            query=context["query"],
            sources=sources,
            outline=outline,
        )
        if not result.success:
            context["errors"].append(f"Writing failed: {result.error}")
            return WorkflowState.FAILED

        context["report"] = result.data
        self.logger.info(f"Report written ({len(result.data)} characters)")
        return WorkflowState.FACT_CHECK

    async def _run_fact_check(self, context: dict) -> WorkflowState:
        """Run the fact checker agent."""
        report = context.get("report", "")
        sources = context.get("all_sources", [])

        # Extract simple text sources for fact-checking
        source_texts = []
        for s in sources:
            if hasattr(s, "content"):
                source_texts.append(str(s.content))
            elif hasattr(s, "snippet"):
                source_texts.append(str(s.snippet))
            elif isinstance(s, dict):
                source_texts.append(str(s.get("content", s.get("snippet", ""))))

        # If no sources, skip fact-checking
        if not source_texts:
            self.logger.warning("No source texts available for fact-checking; skipping")
            return WorkflowState.REVIEW

        # Use LLM to extract claims from the report
        try:
            llm = LLMService()
            claims = await llm.extract_claims(report)
        except Exception as e:
            self.logger.warning(f"Claim extraction failed: {e}; skipping fact-checking")
            return WorkflowState.REVIEW

        if not claims:
            self.logger.info("No claims extracted; skipping fact-checking")
            return WorkflowState.REVIEW

        result = await self.fact_checker.run(
            claims=claims,
            sources=source_texts,
        )
        if result.success:
            context["verification_results"] = result.data
            self.logger.info(f"Fact-checking complete for {len(claims)} claims")
        else:
            self.logger.warning(f"Fact-checking failed: {result.error}")
            context["errors"].append(f"Fact-checking failed: {result.error}")

        return WorkflowState.REVIEW

    async def _run_review(self, context: dict) -> WorkflowState:
        """Run the reviewer agent."""
        report = context.get("report", "")
        criteria = [
            "completeness",
            "accuracy",
            "clarity",
            "tone",
            "structure",
        ]

        result = await self.reviewer.run(
            report=report,
            criteria=criteria,
        )
        if result.success:
            context["review_feedback"] = result.data
            self.logger.info("Review complete")
        else:
            self.logger.warning(f"Review failed: {result.error}")
            context["errors"].append(f"Review failed: {result.error}")

        return WorkflowState.CITE

    async def _run_cite(self, context: dict) -> WorkflowState:
        """Run the citation agent."""
        sources = context.get("all_sources", [])
        style = CitationStyle.APA

        result = await self.citation_agent.run(
            sources=sources,
            style=style,
        )
        if result.success:
            context["citations"] = result.data
            self.logger.info(f"Citations generated: {len(result.data)}")
        else:
            self.logger.warning(f"Citation generation failed: {result.error}")
            context["errors"].append(f"Citation generation failed: {result.error}")

        return WorkflowState.DONE

    def _build_output(self, context: dict) -> dict:
        """Build the final workflow output dictionary."""
        citations = context.get("citations", [])
        formatted_citations = []
        for c in citations:
            if hasattr(c, "formatted_text"):
                formatted_citations.append(c.formatted_text)
            elif isinstance(c, dict):
                formatted_citations.append(c.get("formatted_text", str(c)))

        review = context.get("review_feedback", {})
        if isinstance(review, dict):
            review_text = review.get("feedback", "")
            review_scores = review.get("scores", {})
        else:
            review_text = str(review)
            review_scores = {}

        return {
            "query": context["query"],
            "report": context.get("report"),
            "citations": formatted_citations,
            "review_feedback": review_text,
            "review_scores": review_scores,
            "verification_results": context.get("verification_results"),
            "state": context["state"].value,
            "errors": context["errors"],
            "metadata": {
                "num_web_results": len(context.get("web_results", [])),
                "num_academic_results": len(context.get("academic_results", [])),
                "num_document_results": len(context.get("document_results", [])),
                "duration_seconds": context.get("duration_seconds", 0.0),
                "started_at": context.get("started_at"),
                "finished_at": context.get("finished_at"),
            },
        }
