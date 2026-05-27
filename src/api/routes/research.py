"""
Research session routes.
"""

import asyncio
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks

from src.api.schemas import (
    ResearchRequest,
    ResearchSessionResponse,
    ResearchReportResponse,
    ProgressResponse,
)
from src.api.dependencies import get_current_user, get_db, MockDBSession
from src.core.types import ResearchQuery, ResearchDepth, ResearchStatus
from src.core.logger import get_logger
from src.core.config import get_config
from src.integration.ollama import OllamaLLMProvider

logger = get_logger(__name__)
router = APIRouter()


async def execute_research(session_id: str, request: ResearchRequest, db: MockDBSession):
    """
    Execute the actual research in the background.
    
    Args:
        session_id: Research session ID
        request: Research request parameters
        db: Database session
    """
    try:
        config = get_config()
        ollama = OllamaLLMProvider(config.ollama)
        
        # Update progress: Starting
        db.sessions[session_id]["status"] = ResearchStatus.RUNNING.value
        db.sessions[session_id]["progress"] = 0.1
        db.sessions[session_id]["current_step"] = "Initializing research"
        
        # Check if Ollama is running
        if not await ollama.health_check():
            raise Exception("Ollama service is not running. Please start Ollama with 'ollama serve'")
        
        # Update progress: Planning
        db.sessions[session_id]["progress"] = 0.2
        db.sessions[session_id]["current_step"] = "Creating research plan"
        
        # Generate research plan
        plan_prompt = f"""You are a research assistant. Create a detailed research plan for the following query:

Query: {request.query}
Research Depth: {request.depth.value}

Provide a structured research plan with:
1. Main research questions (3-5 questions)
2. Key topics to investigate
3. Suggested approach

Keep it concise and focused."""

        plan_response = await ollama.generate_text(
            prompt=plan_prompt,
            system_prompt="You are an expert research planner. Provide clear, structured research plans."
        )
        
        # Update progress: Researching
        db.sessions[session_id]["progress"] = 0.4
        db.sessions[session_id]["current_step"] = "Conducting research"
        db.sessions[session_id]["plan"] = plan_response
        
        # Generate main research content
        research_prompt = f"""You are a research expert. Conduct comprehensive research on the following topic:

Topic: {request.query}
Research Depth: {request.depth.value}

Research Plan:
{plan_response}

Provide a detailed research report with:
1. Executive Summary
2. Background and Context
3. Key Findings (at least 5 detailed findings)
4. Analysis and Discussion
5. Implications and Applications
6. Conclusions

Make it comprehensive, well-structured, and informative. Use markdown formatting."""

        # Update progress: Generating report
        db.sessions[session_id]["progress"] = 0.6
        db.sessions[session_id]["current_step"] = "Generating research report"
        
        research_content = await ollama.generate_text(
            prompt=research_prompt,
            system_prompt="You are an expert researcher. Provide comprehensive, well-researched, and accurate information."
        )
        
        # Update progress: Finalizing
        db.sessions[session_id]["progress"] = 0.8
        db.sessions[session_id]["current_step"] = "Finalizing report"
        
        # Create the final report
        final_report = f"""# Research Report: {request.query}

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Research Depth:** {request.depth.value}
**Sources:** {', '.join([s.value for s in (request.source_types or [])])}

---

## Research Plan

{plan_response}

---

## Detailed Research

{research_content}

---

## Methodology

This research was conducted using:
- **LLM Model:** {config.ollama.model}
- **Research Depth:** {request.depth.value}
- **Analysis Type:** Comprehensive literature synthesis
- **Date:** {datetime.now().strftime('%Y-%m-%d')}

## Notes

This report was generated using AI-assisted research. For critical decisions, please verify information with primary sources.
"""
        
        # Store the report
        db.reports[session_id] = {
            "report_id": f"rep_{session_id}",
            "session_id": session_id,
            "title": f"Research Report: {request.query}",
            "content": final_report,
            "format": "markdown",
            "citations": [],
            "sources": [],
            "generated_at": datetime.now(),
            "word_count": len(final_report.split()),
            "user_id": db.sessions[session_id]["user_id"],
        }
        
        # Update session to completed
        db.sessions[session_id]["status"] = ResearchStatus.COMPLETED.value
        db.sessions[session_id]["progress"] = 1.0
        db.sessions[session_id]["current_step"] = "Completed"
        
        logger.info(f"Research completed for session {session_id}")
        
    except Exception as e:
        logger.error(f"Research failed for session {session_id}: {str(e)}")
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
