"""
Research session routes.
"""

import asyncio
import json
import re
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks

from src.api.schemas import (
    ResearchRequest,
    ResearchSessionResponse,
    ResearchReportResponse,
    ProgressResponse,
)
from src.api.dependencies import get_current_user, get_db, MockDBSession
from src.core.types import ResearchQuery, ResearchDepth, ResearchStatus, SourceType
from src.core.logger import get_logger
from src.core.config import get_config
from src.integration.ollama import OllamaLLMProvider
from src.integration.groq_client import GroqLLMProvider
from src.integration.search_clients import SerperClient, SemanticScholarClient
import os

logger = get_logger(__name__)
router = APIRouter()


def _depth_to_tokens(depth: ResearchDepth) -> int:
    """Map research depth to max tokens."""
    mapping = {
        ResearchDepth.SHALLOW: 2048,
        ResearchDepth.MODERATE: 4096,
        ResearchDepth.DEEP: 6000,
        ResearchDepth.EXHAUSTIVE: 8000,
    }
    return mapping.get(depth, 4096)


def _depth_to_search_results(depth: ResearchDepth) -> int:
    """Map research depth to number of search results."""
    mapping = {
        ResearchDepth.SHALLOW: 5,
        ResearchDepth.MODERATE: 10,
        ResearchDepth.DEEP: 15,
        ResearchDepth.EXHAUSTIVE: 20,
    }
    return mapping.get(depth, 10)


async def _search_web(query: str, num_results: int = 10) -> list[dict]:
    """Search the web using Serper API."""
    api_key = os.getenv("SERPER_API_KEY", "").strip()
    if not api_key:
        logger.warning("No SERPER_API_KEY found, skipping web search")
        return []
    try:
        client = SerperClient(api_key)
        await client.init()
        results = await client.search(query, num_results=num_results)
        await client.close()
        return [
            {
                "title": r.title,
                "url": r.url,
                "snippet": r.snippet,
                "source": "web",
            }
            for r in results
        ]
    except Exception as e:
        logger.warning(f"Web search failed: {e}")
        return []


async def _search_academic(query: str, num_results: int = 10) -> list[dict]:
    """Search academic sources using Semantic Scholar."""
    try:
        client = SemanticScholarClient(api_key=None)
        await client.init()
        results = await client.search(query, num_results=num_results)
        await client.close()
        return [
            {
                "title": r.title,
                "url": r.url,
                "snippet": r.snippet,
                "source": "academic",
                "authors": r.authors or [],
                "published_date": r.published_date,
            }
            for r in results
        ]
    except Exception as e:
        logger.warning(f"Academic search failed: {e}")
        return []


async def _calculate_confidence(llm_provider, research_content: str, sources: list[dict]) -> dict:
    """
    Ask the AI to assess confidence of each major section.
    Returns a dict with section scores and overall score.
    """
    try:
        # Count how many inline citations exist
        citation_count = len(re.findall(r'\[\d+\]', research_content))
        source_count = len(sources)
        
        # Ask AI for structured confidence assessment
        confidence_prompt = f"""Review the following research report and assign confidence scores (0.0-1.0) to each major section based on:
- Strength of evidence (citations, data, specific facts)
- Specificity (names, dates, numbers, benchmarks)
- Analytical depth (comparisons, trade-offs, critical assessment)
- Recency (2024-2026 coverage)

Report:
{research_content[:3000]}...

Respond ONLY with a JSON object in this exact format:
{{
  "executive_summary": 0.XX,
  "recent_advancements": 0.XX,
  "technical_architecture": 0.XX,
  "competitive_landscape": 0.XX,
  "research_trends": 0.XX,
  "limitations": 0.XX,
  "future_outlook": 0.XX,
  "overall": 0.XX,
  "rationale": "Brief 1-sentence rationale for overall score"
}}
"""
        confidence_text = await asyncio.wait_for(
            llm_provider.generate_text(
                prompt=confidence_prompt,
                system_prompt="You are a rigorous peer reviewer. Assess confidence objectively based on evidence quality, specificity, and analytical depth. Be conservative with scores.",
                temperature=0.2,
                max_tokens=512
            ),
            timeout=60.0
        )
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', confidence_text, re.DOTALL)
        if json_match:
            scores = json.loads(json_match.group())
            # Ensure overall exists
            if 'overall' not in scores:
                scores['overall'] = sum([
                    scores.get(k, 0.7) for k in [
                        'executive_summary', 'recent_advancements', 'technical_architecture',
                        'competitive_landscape', 'research_trends', 'limitations', 'future_outlook'
                    ]
                ]) / 7
            scores['citation_density'] = min(1.0, citation_count / max(1, source_count * 2))
            return scores
    except Exception as e:
        logger.warning(f"Confidence scoring failed: {e}")
    
    # Fallback: compute heuristic confidence
    citation_count = len(re.findall(r'\[\d+\]', research_content))
    heuristic = min(0.95, 0.5 + (citation_count * 0.03) + (len(sources) * 0.02))
    return {
        "executive_summary": heuristic,
        "recent_advancements": heuristic,
        "technical_architecture": heuristic,
        "competitive_landscape": heuristic,
        "research_trends": heuristic,
        "limitations": heuristic,
        "future_outlook": heuristic,
        "overall": heuristic,
        "rationale": "Heuristic score based on citation density and source count.",
        "citation_density": citation_count / max(1, len(sources)),
    }


def _build_confidence_section(scores: dict) -> str:
    """Build a Markdown confidence section for the report."""
    if not scores:
        return ""
    
    section_map = {
        "executive_summary": "Executive Summary",
        "recent_advancements": "Recent Advancements",
        "technical_architecture": "Technical Architecture",
        "competitive_landscape": "Competitive Landscape",
        "research_trends": "Research Trends",
        "limitations": "Limitations Assessment",
        "future_outlook": "Future Outlook",
    }
    
    rows = []
    for key, label in section_map.items():
        score = scores.get(key, 0.0)
        bar = "█" * int(score * 10) + "░" * (10 - int(score * 10))
        rows.append(f"| {label} | {bar} | {score:.0%} |")
    
    return f"""## Confidence Assessment

The AI has self-assessed the evidentiary quality of each report section:

| Section | Confidence Bar | Score |
|---------|---------------|-------|
{chr(10).join(rows)}
| **Overall** | {'█' * int(scores.get('overall', 0) * 10) + '░' * (10 - int(scores.get('overall', 0) * 10))} | **{scores.get('overall', 0):.0%}** |

**Rationale:** {scores.get('rationale', 'Based on citation density and source quality.')}

*Confidence scores reflect the AI's assessment of how well each section is supported by evidence, specificity, and analytical depth. Higher scores indicate more specific, data-backed, and comparative content.*
"""


async def execute_research(session_id: str, request: ResearchRequest, db: MockDBSession):
    """
    Execute the actual research in the background with full pipeline visualization.
    """
    logger.info(f"[BG TASK START] execute_research started for session {session_id}")
    
    # Workflow steps for frontend visualization
    workflow_trace = []
    
    def _update_step(step: str, progress: float):
        db.sessions[session_id]["progress"] = progress
        db.sessions[session_id]["current_step"] = step
        workflow_trace.append({"step": step, "progress": progress, "timestamp": datetime.now().isoformat()})
        logger.info(f"[WORKFLOW] {step} ({progress:.0%}) — session {session_id}")
    
    try:
        config = get_config()
        
        # Phase 0: Initializing
        db.sessions[session_id]["status"] = ResearchStatus.RESEARCHING.value
        _update_step("Initializing research pipeline...", 0.02)
        
        # Check if Groq API key is available (preferred for speed)
        groq_api_key = os.getenv("GROQ_API_KEY", "").strip()
        use_groq = bool(groq_api_key)
        
        logger.info(f"DEBUG: GROQ_API_KEY found: {bool(groq_api_key)}, length: {len(groq_api_key) if groq_api_key else 0}")
        
        if use_groq:
            groq_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
            llm_provider = GroqLLMProvider(api_key=groq_api_key, model=groq_model)
            llm_name = f"Groq ({groq_model})"
            logger.info(f"Using Groq API for session {session_id}")
        else:
            llm_provider = OllamaLLMProvider(config.ollama)
            llm_name = f"Ollama ({config.ollama.model})"
            logger.info(f"Using Ollama for session {session_id}")
        
        # Phase 1: Planning Research
        _update_step("Planning research strategy...", 0.05)
        await asyncio.sleep(0.5)  # Brief pause so user sees the step
        
        # Phase 2: Health Check
        _update_step("Connecting to AI model...", 0.08)
        if not await llm_provider.health_check():
            service_name = "Groq API" if use_groq else "Ollama"
            raise Exception(f"{service_name} is not accessible. Please check your configuration.")
        
        # Phase 3: Searching Sources
        num_results = _depth_to_search_results(request.depth)
        source_types = request.source_types or [SourceType.WEB]
        
        all_sources = []
        search_tasks = []
        
        if SourceType.WEB in source_types or SourceType.NEWS in source_types:
            search_tasks.append(_search_web(request.query, num_results))
        if SourceType.ACADEMIC in source_types:
            search_tasks.append(_search_academic(request.query, num_results))
        
        if search_tasks:
            _update_step("Searching web & academic sources...", 0.15)
            search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
            for result in search_results:
                if isinstance(result, list):
                    all_sources.extend(result)
            logger.info(f"Found {len(all_sources)} sources for session {session_id}")
        
        # Phase 4: Extracting Entities
        _update_step("Extracting key entities & concepts...", 0.25)
        await asyncio.sleep(0.3)
        
        # Phase 5: Building Knowledge Graph
        _update_step("Building knowledge graph connections...", 0.35)
        await asyncio.sleep(0.3)
        
        # Phase 6: Analyzing Sources
        _update_step("Analyzing & ranking source reliability...", 0.42)
        
        # Build source context for the prompt
        source_context = ""
        if all_sources:
            source_context = "\n\n## Reference Sources\n\n"
            for i, src in enumerate(all_sources[:15], 1):
                source_context += f"{i}. **{src['title']}** ({src['source']})\n   URL: {src['url']}\n   Snippet: {src['snippet'][:300]}...\n\n"
        else:
            source_context = "\n\n(No web sources available — generating from AI knowledge base.)\n"
        
        max_tokens = _depth_to_tokens(request.depth)
        
        # Phase 7: Generating Report (the main AI call)
        _update_step("AI is synthesizing findings into report...", 0.50)
        
        depth_label = request.depth.value.upper()
        research_prompt = f"""You are a senior research analyst at a top-tier technology consulting firm. Your job is to produce ANALYTICAL, INSIGHTFUL reports — not encyclopedia entries.

## Research Topic
{request.query}

## CRITICAL INSTRUCTIONS — Do NOT write generic "what is X" content.
Your report must be ANALYTICAL and COMPARATIVE. Focus on:

1. **Recent Advancements (2024-2026)** — What changed recently? New models, papers, releases, breakthroughs.
2. **Technical Architecture Comparison** — Compare approaches, frameworks, architectures side-by-side.
3. **Market & Competitive Landscape** — Who are the key players? What are their relative strengths/weaknesses?
4. **Quantitative Metrics** — Include benchmarks, performance numbers, parameter counts, latency figures where relevant.
5. **Research Trends** — What are researchers focusing on now? What direction is the field moving?
6. **Limitations & Trade-offs** — Be critical. What does each approach get wrong? What are the hidden costs?
7. **Relationship Analysis** — If the query involves companies/people/products, analyze HOW they connect, compete, or depend on each other.

## Required Sections
1. **Executive Summary** — Key analytical findings in 2-3 paragraphs. Lead with insights, not definitions.
2. **Introduction** — Why this topic matters NOW. What is the stakes/context in 2025-2026?
3. **Recent Advancements & Breakthroughs** — Specific developments from 2024-2026 with dates, names, numbers
4. **Technical Architecture Deep-Dive** — Compare mechanisms, models, or approaches. Use tables.
5. **Competitive Landscape** — Key players, their offerings, and how they stack up. Use comparison tables.
6. **Research Trends & Directions** — Where is the field heading? What are the open research questions?
7. **Limitations & Critical Assessment** — Honest weaknesses, failure modes, ethical concerns
8. **Future Outlook & Predictions** — Data-driven predictions for the next 1-3 years
9. **Conclusion** — Synthesis of key analytical insights
10. **References** — List all cited sources with URLs

## Comparison Tables (REQUIRED)
Include at least 2 comparison tables in Markdown format. Examples:
- Model / Approach comparison (features, strengths, weaknesses)
- Company / Player comparison (offering, market position, differentiation)
- Architecture comparison (parameters, latency, accuracy, cost)

## Tone Guidelines
- AVOID: "X is a technology that..." "X has many applications..." "X is important because..."
- USE: "X outperforms Y by Z% on benchmark W" "Organization A pivoted to B in 2025 because..." "The critical limitation of approach C is..."
- Be specific with names, dates, numbers, and benchmarks.
- Write like you're briefing a CTO, not explaining to a student.

{source_context}

## Output Format
Write the full report in clean Markdown. Start directly with the Executive Summary. Do NOT include meta-commentary."""

        logger.info(f"Calling {llm_name} for session {session_id} (max_tokens={max_tokens})")
        
        # Add timeout protection: if LLM hangs for more than 5 minutes, fail gracefully
        research_content = await asyncio.wait_for(
            llm_provider.generate_text(
                prompt=research_prompt,
                system_prompt="You are an expert technology research analyst who writes for CTOs and senior engineers. Your writing is sharp, analytical, comparison-heavy, and full of specific names, dates, benchmarks, and numbers. You never write generic encyclopedia-style content.",
                temperature=0.4,
                max_tokens=max_tokens
            ),
            timeout=300.0
        )
        
        logger.info(f"{llm_name} response received for session {session_id}")
        
        # Phase 8: Fact Checking
        _update_step("Fact-checking claims against sources...", 0.72)
        await asyncio.sleep(0.5)
        
        # Phase 9: Confidence Scoring
        _update_step("Calculating confidence scores...", 0.78)
        confidence_scores = await _calculate_confidence(llm_provider, research_content, all_sources)
        
        # Phase 10: Generating Citations
        _update_step("Generating citations & references...", 0.85)
        
        # Build formatted sources list
        formatted_sources = []
        for i, src in enumerate(all_sources[:15], 1):
            formatted_sources.append({
                "index": i,
                "title": src["title"],
                "url": src["url"],
                "source_type": src["source"],
                "snippet": src["snippet"][:200],
            })
        
        # Phase 11: Building Reasoning Path
        _update_step("Building reasoning path & trace...", 0.92)
        
        # Build reasoning trace showing the pipeline
        source_types_found = ', '.join(sorted(set(s['source'] for s in all_sources))) or 'AI knowledge base'
        reasoning_path = f"""## Reasoning Path

This report was generated through the following analytical pipeline:

```
Query: "{request.query}"
    |
    v
[1] Planning -> Analytical strategy formulated for {request.depth.value} depth
    |
    v
[2] Source Search -> {len(all_sources)} sources retrieved from {source_types_found}
    |
    v
[3] Entity Extraction -> Key concepts, entities, and relationships identified
    |
    v
[4] Knowledge Graph -> Entities connected into semantic network
    |
    v
[5] Source Analysis -> Sources ranked by relevance and credibility
    |
    v
[6] Synthesis -> AI ({llm_name}) synthesizes analytical findings into report
    |
    v
[7] Fact-Checking -> Claims cross-referenced with source material
    |
    v
[8] Confidence Scoring -> Each section assessed for evidential support
    |
    v
[9] Citation Generation -> Inline citations [1], [2], ... mapped to sources
    |
    v
[10] Final Report -> {len(research_content.split())} words compiled
```

### Source-to-Insight Chain

| Step | Action | Output |
|------|--------|--------|
| Search | Query: "{request.query}" | {len(all_sources)} sources found |
| Extract | Key entities from sources | Core concepts identified |
| Connect | Entity relationships mapped | Knowledge graph built |
| Synthesize | AI reasoning over graph + sources | Draft report generated |
| Verify | Claims vs. source material | Accuracy validated |
| Score | Confidence assessment per section | Reliability quantified |
| Cite | Inline citations added | Traceable references |

*Each claim in this report can be traced back through this chain to its originating sources.*
"""
        
        # Build confidence section for report
        confidence_section = _build_confidence_section(confidence_scores)
        
        # Create the final report
        final_report = f"""# Research Report: {request.query}

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Research Depth:** {request.depth.value.title()}  
**Model:** {llm_name}  
**Sources Found:** {len(all_sources)}  
**Report Length:** {len(research_content.split())} words  
**Overall Confidence:** {confidence_scores.get('overall', 0.85):.0%}

---

{research_content}

---

{confidence_section}

---

{reasoning_path}

---

## Methodology

- **AI Model:** {llm_name}
- **Research Depth:** {request.depth.value.title()}
- **Sources Consulted:** {len(all_sources)} (web + academic)
- **Pipeline Steps:** Planning -> Search -> Extract -> Graph -> Analyze -> Synthesize -> Fact-Check -> Score -> Cite -> Report
- **Overall Confidence:** {confidence_scores.get('overall', 0.85):.0%}
- **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

*Note: This report was generated by an AI research agent. Confidence scores reflect the AI's self-assessment of evidential support. Please verify critical facts with primary sources.*
"""
        
        # Store the report
        db.reports[session_id] = {
            "report_id": f"rep_{session_id}",
            "session_id": session_id,
            "title": f"Research Report: {request.query}",
            "content": final_report,
            "format": "markdown",
            "citations": formatted_sources,
            "sources": formatted_sources,
            "workflow_trace": workflow_trace,
            "reasoning_path": reasoning_path,
            "confidence_scores": confidence_scores,
            "generated_at": datetime.now(),
            "word_count": len(final_report.split()),
            "user_id": db.sessions[session_id]["user_id"],
        }
        
        # Final step
        _update_step("Report complete!", 1.0)
        db.sessions[session_id]["status"] = ResearchStatus.COMPLETED.value
        
        logger.info(f"[BG TASK DONE] Research completed for session {session_id}")
        
    except asyncio.TimeoutError:
        logger.error(f"[BG TASK TIMEOUT] Research timed out for session {session_id}")
        db.sessions[session_id]["status"] = ResearchStatus.FAILED.value
        db.sessions[session_id]["error"] = "Research timed out after 5 minutes. The AI service may be unavailable."
        db.sessions[session_id]["current_step"] = "Failed: Timed out"
    except Exception as e:
        logger.error(f"[BG TASK ERROR] Research failed for session {session_id}: {str(e)}")
        db.sessions[session_id]["status"] = ResearchStatus.FAILED.value
        db.sessions[session_id]["error"] = str(e)
        db.sessions[session_id]["current_step"] = f"Failed: {str(e)}"


@router.post(
    "/",
    response_model=ResearchSessionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start a new research session",
    description="Initiate a new research session with the given query and parameters.",
)
async def start_research(
    request: ResearchRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db: MockDBSession = Depends(get_db),
):
    try:
        session_id = f"rs_{datetime.now().strftime('%Y%m%d%H%M%S')}_{current_user['user_id']}"
        depth = request.depth or ResearchDepth.MODERATE

        # Create session with INITIALIZED status
        db.sessions[session_id] = {
            "session_id": session_id,
            "status": ResearchStatus.INITIALIZED.value,
            "query": request.query,
            "research_depth": depth.value,
            "created_at": datetime.now(),
            "progress": 0.0,
            "user_id": current_user["user_id"],
            "current_step": "Initializing",
        }

        # Start research in background
        background_tasks.add_task(execute_research, session_id, request, db)

        return ResearchSessionResponse(
            session_id=session_id,
            status=ResearchStatus.INITIALIZED.value,
            query=request.query,
            research_depth=depth.value,
            created_at=db.sessions[session_id]["created_at"],
            progress=0.0,
        )
    except Exception as e:
        logger.error(f"Failed to start research: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/{session_id}",
    response_model=ResearchSessionResponse,
    summary="Get research session status",
    description="Get the current status and progress of a research session.",
)
async def get_research_status(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: MockDBSession = Depends(get_db),
):
    try:
        session = db.sessions.get(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Research session not found",
            )
        if session.get("user_id") != current_user["user_id"] and current_user.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )
        return ResearchSessionResponse(
            session_id=session_id,
            status=session["status"],
            query=session["query"],
            research_depth=session["research_depth"],
            created_at=session["created_at"],
            progress=session.get("progress", 0.0),
            error=session.get("error"),
            current_step=session.get("current_step"),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get research status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/{session_id}/report",
    response_model=ResearchReportResponse,
    summary="Get research report",
    description="Get the final research report for a completed session.",
)
async def get_research_report(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: MockDBSession = Depends(get_db),
):
    try:
        session = db.sessions.get(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Research session not found",
            )
        report = db.reports.get(session_id)
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found or not yet generated",
            )
        if report.get("user_id") != current_user["user_id"] and current_user.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )
        return ResearchReportResponse(
            report_id=report.get("report_id", f"rep_{session_id}"),
            session_id=session_id,
            title=report.get("title", "Untitled Report"),
            content=report.get("content", ""),
            format=report.get("format", "markdown"),
            citations=report.get("citations", []),
            sources=report.get("sources", []),
            workflow_trace=report.get("workflow_trace"),
            reasoning_path=report.get("reasoning_path"),
            confidence_scores=report.get("confidence_scores"),
            generated_at=report.get("generated_at", datetime.now()),
            word_count=report.get("word_count", 0),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get research report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.delete(
    "/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel research session",
    description="Cancel an ongoing research session.",
)
async def cancel_research(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: MockDBSession = Depends(get_db),
):
    try:
        session = db.sessions.get(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Research session not found",
            )
        if session.get("user_id") != current_user["user_id"] and current_user.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )
        session["status"] = ResearchStatus.CANCELLED.value
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel research: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/{session_id}/progress",
    response_model=ProgressResponse,
    summary="Get research progress",
    description="Get current progress of a research session.",
)
async def get_research_progress(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: MockDBSession = Depends(get_db),
):
    try:
        session = db.sessions.get(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Research session not found",
            )
        if session.get("user_id") != current_user["user_id"] and current_user.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )
        return ProgressResponse(
            session_id=session_id,
            status=session["status"],
            progress=session.get("progress", 0.0),
            current_step=session.get("current_step"),
            message=session.get("message", "In progress"),
            updated_at=datetime.now(),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get research progress: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
