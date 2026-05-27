"""
REST API endpoints for the Deep Research Agent.
"""

from fastapi import APIRouter, HTTPException, status
from src.api.schemas import (
    ResearchRequest,
    ResearchSessionResponse,
    ResearchReportResponse,
    HealthResponse,
)
from src.core.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["research"])


@router.post(
    "/research",
    response_model=ResearchSessionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start a new research session",
    description="Initiate a new research session with the given query",
)
async def start_research(request: ResearchRequest):
    """
    Start a new research session.

    Args:
        request: Research request with query and parameters

    Returns:
        Research session information
    """
    try:
        logger.info(f"Starting research session for: {request.query}")

        # TODO: Implement research session creation
        session_id = "research_session_001"

        return ResearchSessionResponse(
            session_id=session_id,
            status="initialized",
            query=request.query,
            research_depth=request.depth.value,
        )

    except Exception as e:
        logger.error(f"Failed to start research: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/research/{session_id}",
    response_model=ResearchSessionResponse,
    summary="Get research session status",
    description="Get the current status and progress of a research session",
)
async def get_research_status(session_id: str):
    """
    Get research session status.

    Args:
        session_id: Session ID

    Returns:
        Current session status and progress
    """
    try:
        logger.info(f"Fetching research status for session: {session_id}")

        # TODO: Implement session status retrieval
        return ResearchSessionResponse(
            session_id=session_id,
            status="researching",
            query="Sample query",
            research_depth="moderate",
            progress=0.5,
        )

    except Exception as e:
        logger.error(f"Failed to get research status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/research/{session_id}/report",
    response_model=ResearchReportResponse,
    summary="Get research report",
    description="Get the final research report for a completed session",
)
async def get_research_report(session_id: str):
    """
    Get research report.

    Args:
        session_id: Session ID

    Returns:
        Final research report
    """
    try:
        logger.info(f"Fetching research report for session: {session_id}")

        # TODO: Implement report retrieval
        return ResearchReportResponse(
            report_id="report_001",
            session_id=session_id,
            title="Sample Report",
            content="# Research Report\n\nSample content.",
            citations=[],
            sources=[],
            word_count=100,
        )

    except Exception as e:
        logger.error(f"Failed to get research report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.delete(
    "/research/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel research session",
    description="Cancel an ongoing research session",
)
async def cancel_research(session_id: str):
    """
    Cancel research session.

    Args:
        session_id: Session ID
    """
    try:
        logger.info(f"Cancelling research session: {session_id}")

        # TODO: Implement session cancellation

    except Exception as e:
        logger.error(f"Failed to cancel research: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check the health status of the API and services",
)
async def health_check():
    """
    Health check endpoint.

    Returns:
        Health status
    """
    try:
        logger.debug("Health check requested")

        services = {
            "api": "healthy",
            "ollama": "checking...",  # TODO: Implement actual checks
        }

        return HealthResponse(services=services)

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Health check failed",
        )
