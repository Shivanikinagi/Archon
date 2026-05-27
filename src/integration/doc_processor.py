"""
Document processing utilities for various file formats.
"""

import io
from pathlib import Path
from typing import Optional, AsyncGenerator
from abc import ABC, abstractmethod

from src.core.types import Source, SourceType, DocumentChunk
from src.core.logger import get_logger
from src.core.exceptions import DocumentProcessingError
from datetime import datetime

logger = get_logger(__name__)


class DocumentProcessor(ABC):
    """Base class for document processors."""

    @abstractmethod
    async def extract_text(self, file_path: str) -> str:
        """Extract text from document."""
        pass

    @abstractmethod
    async def extract_chunks(
        self,
        file_path: str,
        chunk_size: int = 512,
        overlap: int = 128,
    ) -> list[DocumentChunk]:
        """Extract text chunks from document."""
        pass


class PDFProcessor(DocumentProcessor):
    """Process PDF documents."""

    async def extract_text(self, file_path: str) -> str:
        """Extract text from PDF."""
        try:
            import PyPDF2

            text = []
            with open(file_path, "rb") as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page in pdf_reader.pages:
                    text.append(page.extract_text())
            return "\n".join(text)
        except Exception as e:
            logger.error(f"Failed to extract text from PDF: {str(e)}")
            raise DocumentProcessingError(f"PDF extraction failed: {str(e)}")

    async def extract_chunks(
        self,
        file_path: str,
        chunk_size: int = 512,
        overlap: int = 128,
    ) -> list[DocumentChunk]:
        """Extract chunks from PDF."""
        text = await self.extract_text(file_path)
        return self._chunk_text(text, file_path, chunk_size, overlap)

    def _chunk_text(
        self,
        text: str,
        file_path: str,
        chunk_size: int,
        overlap: int,
    ) -> list[DocumentChunk]:
        """Split text into chunks."""
        chunks = []
        words = text.split()

        for i in range(0, len(words), chunk_size - overlap):
            chunk_words = words[i : i + chunk_size]
            chunk_text = " ".join(chunk_words)

            chunk = DocumentChunk(
                chunk_id=f"{file_path}_{len(chunks)}",
                document_id=file_path,
                content=chunk_text,
                source=Source(
                    url=f"file://{file_path}",
                    title=Path(file_path).name,
                    source_type=SourceType.UPLOADED,
                    retrieved_at=datetime.now(),
                ),
                metadata={"chunk_index": len(chunks)},
            )
            chunks.append(chunk)

        return chunks


class MarkdownProcessor(DocumentProcessor):
    """Process Markdown documents."""

    async def extract_text(self, file_path: str) -> str:
        """Extract text from Markdown."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to extract text from Markdown: {str(e)}")
            raise DocumentProcessingError(f"Markdown extraction failed: {str(e)}")

    async def extract_chunks(
        self,
        file_path: str,
        chunk_size: int = 512,
        overlap: int = 128,
    ) -> list[DocumentChunk]:
        """Extract chunks from Markdown."""
        text = await self.extract_text(file_path)
        return self._chunk_text(text, file_path, chunk_size, overlap)

    def _chunk_text(
        self,
        text: str,
        file_path: str,
        chunk_size: int,
        overlap: int,
    ) -> list[DocumentChunk]:
        """Split text into chunks."""
        chunks = []
        words = text.split()

        for i in range(0, len(words), chunk_size - overlap):
            chunk_words = words[i : i + chunk_size]
            chunk_text = " ".join(chunk_words)

            chunk = DocumentChunk(
                chunk_id=f"{file_path}_{len(chunks)}",
                document_id=file_path,
                content=chunk_text,
                source=Source(
                    url=f"file://{file_path}",
                    title=Path(file_path).name,
                    source_type=SourceType.UPLOADED,
                    retrieved_at=datetime.now(),
                ),
                metadata={"chunk_index": len(chunks)},
            )
            chunks.append(chunk)

        return chunks


class DocumentProcessorFactory:
    """Factory for creating document processors."""

    @staticmethod
    def create_processor(file_path: str) -> DocumentProcessor:
        """Create appropriate processor for file type."""
        suffix = Path(file_path).suffix.lower()

        if suffix == ".pdf":
            return PDFProcessor()
        elif suffix in [".md", ".markdown"]:
            return MarkdownProcessor()
        else:
            raise DocumentProcessingError(
                f"Unsupported file type: {suffix}. "
                f"Supported: .pdf, .md, .markdown"
            )
