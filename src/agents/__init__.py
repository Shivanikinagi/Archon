"""
Agents for autonomous research orchestration.
"""

from src.core.logger import get_logger

from src.agents.planner import PlannerAgent
from src.agents.web_search import WebSearchAgent
from src.agents.academic_search import AcademicSearchAgent
from src.agents.document_search import DocumentSearchAgent
from src.agents.writer import WriterAgent
from src.agents.fact_checker import FactCheckerAgent
from src.agents.reviewer import ReviewerAgent
from src.agents.citation_agent import CitationAgent
from src.agents.workflow import ResearchWorkflow

logger = get_logger(__name__)

__all__ = [
    "PlannerAgent",
    "WebSearchAgent",
    "AcademicSearchAgent",
    "DocumentSearchAgent",
    "WriterAgent",
    "FactCheckerAgent",
    "ReviewerAgent",
    "CitationAgent",
    "ResearchWorkflow",
]
