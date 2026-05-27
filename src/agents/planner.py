"""
Planner Agent - Creates research plans and identifies subtopics.
"""

import json
from typing import Any
from src.core.base import BaseAgent, ExecutionResult
from src.core.types import AgentRole, ResearchQuery, ResearchPlan, ResearchDepth
from src.core.logger import get_logger
from src.integration import LLMProviderFactory

logger = get_logger(__name__)


class PlannerAgent(BaseAgent):
    """Agent responsible for creating research plans."""

    def __init__(self, llm_provider: str = "ollama"):
        """
        Initialize Planner Agent.

        Args:
            llm_provider: LLM provider to use (ollama, openai, etc.)
        """
        super().__init__(role=AgentRole.PLANNER, name="Research Planner")
        self.llm_provider = LLMProviderFactory.create_provider(llm_provider)

    def validate_inputs(self, **kwargs: Any) -> bool:
        """Validate planner inputs."""
        query = kwargs.get("query")
        if not isinstance(query, (str, ResearchQuery)):
            return False
        return True

    async def execute(self, **kwargs: Any) -> ExecutionResult:
        """
        Create a research plan from a query.

        Args:
            query: Research query (str or ResearchQuery object)

        Returns:
            ExecutionResult containing the research plan
        """
        try:
            query = kwargs.get("query")

            if isinstance(query, str):
                query = ResearchQuery(
                    query_text=query,
                    depth=kwargs.get("depth", ResearchDepth.MODERATE),
                )

            # Generate plan using LLM
            plan = await self._generate_plan(query)

            return ExecutionResult(
                success=True,
                data=plan,
                metadata={"query": query.query_text, "depth": query.depth.value},
            )

        except Exception as e:
            self.logger.error(f"Plan generation failed: {str(e)}")
            return ExecutionResult(
                success=False,
                error=str(e),
            )

    async def _generate_plan(self, query: ResearchQuery) -> ResearchPlan:
        """Generate research plan using LLM."""
        prompt = self._build_prompt(query)

        # Call LLM based on provider
        if hasattr(self.llm_provider, "generate_text"):
            # Ollama provider
            response = await self.llm_provider.generate_text(prompt)
        else:
            # OpenAI or other provider
            response = self.llm_provider.invoke(prompt)

        # Parse response to extract plan
        plan = self._parse_plan(response, query)
        return plan

    def _build_prompt(self, query: ResearchQuery) -> str:
        """Build LLM prompt for plan generation."""
        system_prompt = """You are a research planning expert. 
        Create a detailed research plan for the given topic.
        Return a JSON object with: main_query, subtopics (list), search_queries (list), estimated_sources (int), timeline_minutes (int)"""

        user_prompt = f"""Create a research plan for: {query.query_text}
        
Research depth: {query.depth.value}
Language: {query.language}

Return a JSON object in this exact format:
{{
    "main_query": "...",
    "subtopics": ["...", "...", "..."],
    "search_queries": ["...", "...", "..."],
    "estimated_sources": 15,
    "timeline_minutes": 30
}}"""

        return f"{system_prompt}\n\n{user_prompt}"

    def _parse_plan(self, response: str, query: ResearchQuery) -> ResearchPlan:
        """Parse LLM response to extract research plan."""
        try:
            # Extract JSON from response
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1
            json_str = response[start_idx:end_idx]
            data = json.loads(json_str)

            return ResearchPlan(
                main_query=data.get("main_query", query.query_text),
                subtopics=data.get("subtopics", [query.query_text]),
                search_queries=data.get("search_queries", [query.query_text]),
                research_depth=query.depth,
                estimated_sources=data.get("estimated_sources", 10),
                timeline_minutes=data.get("timeline_minutes", 30),
            )
        except Exception as e:
            self.logger.warning(f"Failed to parse plan response: {str(e)}")
            # Return default plan
            return ResearchPlan(
                main_query=query.query_text,
                subtopics=[query.query_text],
                search_queries=[query.query_text],
                research_depth=query.depth,
                estimated_sources=10,
                timeline_minutes=30,
            )
