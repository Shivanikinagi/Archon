"""
Report routes.
"""

from datetime import datetime
from typing import List
from fastapi import APIRouter, HTTPException, status, Depends, Query

from src.api.schemas import ResearchReportResponse, ReportSummaryResponse
from src.api.dependencies import get_current_user, get_db, MockDBSession
from src.core.types import ReportFormat
from src.core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get(
    "/",
    response_model=List[ReportSummaryResponse],
    summary="List reports",
    description="List all research reports for the current user.",
)
async def list_reports(
    current_user: dict = Depends(get_current_user),
    db: MockDBSession = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    try:
        user_reports = [
            ReportSummaryResponse(
                report_id=r["report_id"],
                session_id=r["session_id"],
                title=r.get("title", "Untitled"),
                format=r.get("format", "markdown"),
                generated_at=r.get("generated_at", datetime.now()),
                word_count=r.get("word_count", 0),
            )
            for r in db.reports.values()
            if r.get("user_id") == current_user["user_id"] or current_user.get("role") == "admin"
        ]
        return user_reports[offset:offset + limit]
    except Exception as e:
        logger.error(f"Failed to list reports: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/{report_id}",
    response_model=ResearchReportResponse,
    summary="Get specific report",
    description="Get a specific research report by ID.",
)
async def get_report(
    report_id: str,
    current_user: dict = Depends(get_current_user),
    db: MockDBSession = Depends(get_db),
):
    try:
        report = None
        for r in db.reports.values():
            if r.get("report_id") == report_id:
                report = r
                break
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found",
            )
        if report.get("user_id") != current_user["user_id"] and current_user.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )
        return ResearchReportResponse(
            report_id=report_id,
            session_id=report["session_id"],
            title=report.get("title", "Untitled"),
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
        logger.error(f"Failed to get report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.delete(
    "/{report_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete report",
    description="Delete a research report by ID.",
)
async def delete_report(
    report_id: str,
    current_user: dict = Depends(get_current_user),
    db: MockDBSession = Depends(get_db),
):
    try:
        report_key = None
        for k, r in db.reports.items():
            if r.get("report_id") == report_id:
                report_key = k
                break
        if not report_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found",
            )
        report = db.reports[report_key]
        if report.get("user_id") != current_user["user_id"] and current_user.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )
        del db.reports[report_key]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/{report_id}/export",
    summary="Export report",
    description="Export a report in different formats (markdown, html, json).",
)
async def export_report(
    report_id: str,
    format: ReportFormat = Query(default=ReportFormat.MARKDOWN),
    current_user: dict = Depends(get_current_user),
    db: MockDBSession = Depends(get_db),
):
    try:
        report = None
        for r in db.reports.values():
            if r.get("report_id") == report_id:
                report = r
                break
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found",
            )
        if report.get("user_id") != current_user["user_id"] and current_user.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )
        content = report.get("content", "")
        if format == ReportFormat.HTML:
            content = f"<html><body><pre>{content}</pre></body></html>"
        elif format == ReportFormat.JSON:
            import json
            content = json.dumps({"title": report.get("title"), "content": content}, indent=2)
        return {
            "report_id": report_id,
            "format": format.value,
            "content": content,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
