"""
Document upload routes.
"""

import uuid
from datetime import datetime
from typing import List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Depends

from src.api.schemas import DocumentResponse, DocumentChunkResponse, SourceResponse
from src.api.dependencies import get_current_user, get_db, MockDBSession
from src.core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload document",
    description="Upload a PDF or Markdown file for research.",
)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    current_user: dict = Depends(get_current_user),
    db: MockDBSession = Depends(get_db),
):
    try:
        content_type = file.content_type or ""
        filename = file.filename or ""
        allowed_ext = (".pdf", ".md", ".markdown")
        if not (
            content_type.endswith(("pdf", "markdown", "md"))
            or filename.lower().endswith(allowed_ext)
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF and Markdown files are supported",
            )

        doc_id = str(uuid.uuid4())
        content = await file.read()
        size = len(content)

        db.documents[doc_id] = {
            "doc_id": doc_id,
            "title": title,
            "filename": filename,
            "content_type": content_type,
            "size": size,
            "uploaded_at": datetime.now(),
            "status": "processed",
            "user_id": current_user["user_id"],
            "content": content.decode("utf-8", errors="ignore") if not content_type.endswith("pdf") else None,
        }

        db.chunks[doc_id] = [
            {
                "chunk_id": f"{doc_id}_chunk_0",
                "document_id": doc_id,
                "content": "Mock chunk content",
                "source": SourceResponse(
                    url=f"/documents/{doc_id}",
                    title=title,
                    source_type="uploaded",
                    confidence=1.0,
                ),
            }
        ]

        return DocumentResponse(
            doc_id=doc_id,
            title=title,
            filename=filename,
            content_type=content_type,
            size=size,
            uploaded_at=db.documents[doc_id]["uploaded_at"],
            status="processed",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/",
    response_model=List[DocumentResponse],
    summary="List documents",
    description="List all uploaded documents for the current user.",
)
async def list_documents(
    current_user: dict = Depends(get_current_user),
    db: MockDBSession = Depends(get_db),
):
    try:
        docs = [
            DocumentResponse(
                doc_id=d["doc_id"],
                title=d["title"],
                filename=d["filename"],
                content_type=d["content_type"],
                size=d["size"],
                uploaded_at=d["uploaded_at"],
                status=d.get("status", "processed"),
            )
            for d in db.documents.values()
            if d.get("user_id") == current_user["user_id"] or current_user.get("role") == "admin"
        ]
        return docs
    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.delete(
    "/{doc_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete document",
    description="Delete an uploaded document by ID.",
)
async def delete_document(
    doc_id: str,
    current_user: dict = Depends(get_current_user),
    db: MockDBSession = Depends(get_db),
):
    try:
        doc = db.documents.get(doc_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )
        if doc.get("user_id") != current_user["user_id"] and current_user.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )
        del db.documents[doc_id]
        db.chunks.pop(doc_id, None)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/{doc_id}/chunks",
    response_model=List[DocumentChunkResponse],
    summary="Get document chunks",
    description="Get processed chunks for a specific document.",
)
async def get_chunks(
    doc_id: str,
    current_user: dict = Depends(get_current_user),
    db: MockDBSession = Depends(get_db),
):
    try:
        doc = db.documents.get(doc_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )
        if doc.get("user_id") != current_user["user_id"] and current_user.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )
        chunks = db.chunks.get(doc_id, [])
        return [
            DocumentChunkResponse(
                chunk_id=c["chunk_id"],
                document_id=c["document_id"],
                content=c["content"],
                source=c["source"],
            )
            for c in chunks
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get chunks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
