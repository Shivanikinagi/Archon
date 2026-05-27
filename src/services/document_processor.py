"""Document processing and chunking for RAG

Handles document splitting, token counting, and chunk management.
"""

import logging
from typing import List, Optional, Dict, Any
import re

logger = logging.getLogger(__name__)


class DocumentChunk:
    """Represents a chunk of a document"""
    
    def __init__(
        self,
        content: str,
        chunk_id: str,
        document_id: str,
        chunk_index: int,
        token_count: int,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize document chunk
        
        Args:
            content: Chunk text content
            chunk_id: Unique chunk identifier
            document_id: Parent document ID
            chunk_index: Index in document
            token_count: Estimated tokens in chunk
            metadata: Optional metadata
        """
        self.content = content
        self.chunk_id = chunk_id
        self.document_id = document_id
        self.chunk_index = chunk_index
        self.token_count = token_count
        self.metadata = metadata or {}
    
    def __repr__(self) -> str:
        return f"DocumentChunk(id={self.chunk_id}, tokens={self.token_count})"


class DocumentProcessor:
    """Process documents into chunks for RAG"""
    
    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 128,
        separator: str = "\n\n",
    ):
        """
        Initialize document processor
        
        Args:
            chunk_size: Target chunk size in characters
            chunk_overlap: Character overlap between chunks
            separator: Primary separator for splitting (paragraph break)
        """
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")
        
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separator = separator
        
        logger.debug(
            f"✓ DocumentProcessor initialized (size={chunk_size}, overlap={chunk_overlap})"
        )
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text
        
        Args:
            text: Text to estimate tokens for
            
        Returns:
            Estimated token count
        """
        # Rough approximation: 1 token ≈ 4 characters
        # More accurate: use actual tokenizer
        return len(text) // 4
    
    def split_text(self, text: str, separator: str = None) -> List[str]:
        """
        Split text using configurable separator
        
        Args:
            text: Text to split
            separator: Separator string (uses default if None)
            
        Returns:
            List of text chunks
        """
        separator = separator or self.separator
        
        if separator not in text:
            # Fall back to simpler splitting if separator not found
            logger.debug(f"Separator '{separator}' not found, using character-based splitting")
            return self._split_by_characters(text)
        
        splits = text.split(separator)
        return [s for s in splits if s.strip()]
    
    def _split_by_characters(self, text: str) -> List[str]:
        """
        Split text by character limit when separator not found
        
        Args:
            text: Text to split
            
        Returns:
            List of text chunks
        """
        chunks = []
        for i in range(0, len(text), self.chunk_size):
            chunks.append(text[i : i + self.chunk_size])
        
        return [c for c in chunks if c.strip()]
    
    def process_document(
        self,
        document_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[DocumentChunk]:
        """
        Process document into chunks
        
        Args:
            document_id: Document identifier
            content: Document text content
            metadata: Optional document metadata
            
        Returns:
            List of DocumentChunk objects
        """
        try:
            if not content or not content.strip():
                logger.warning(f"Empty document: {document_id}")
                return []
            
            chunks = []
            
            # Split by separator first
            splits = self.split_text(content)
            logger.debug(f"Split document into {len(splits)} parts")
            
            # Merge splits into appropriately-sized chunks
            good_splits = []
            for split in splits:
                if len(split) < self.chunk_size:
                    good_splits.append(split)
                else:
                    # Split large section by characters
                    subsplits = self._split_by_characters(split)
                    good_splits.extend(subsplits)
            
            # Create chunks with overlap
            for i in range(len(good_splits)):
                chunk_content = good_splits[i]
                
                # Add overlap from previous chunk if not first
                if i > 0 and self.chunk_overlap > 0:
                    prev_content = good_splits[i - 1]
                    overlap_start = max(0, len(prev_content) - self.chunk_overlap)
                    overlap_text = prev_content[overlap_start:]
                    chunk_content = overlap_text + "\n" + chunk_content
                
                # Skip if too small (except last chunk)
                if len(chunk_content.strip()) < 50 and i < len(good_splits) - 1:
                    continue
                
                token_count = self.estimate_tokens(chunk_content)
                chunk_metadata = metadata.copy() if metadata else {}
                chunk_metadata["document_id"] = document_id
                
                chunk = DocumentChunk(
                    content=chunk_content,
                    chunk_id=f"{document_id}_chunk_{len(chunks)}",
                    document_id=document_id,
                    chunk_index=len(chunks),
                    token_count=token_count,
                    metadata=chunk_metadata,
                )
                chunks.append(chunk)
            
            logger.info(f"✓ Processed document {document_id} into {len(chunks)} chunks")
            return chunks
        
        except Exception as e:
            logger.error(f"✗ Document processing failed: {e}")
            raise
    
    def process_documents(
        self,
        documents: List[tuple],  # (document_id, content, metadata?)
    ) -> List[DocumentChunk]:
        """
        Process multiple documents
        
        Args:
            documents: List of (document_id, content) or (document_id, content, metadata) tuples
            
        Returns:
            Flattened list of all chunks
        """
        all_chunks = []
        
        for doc_tuple in documents:
            document_id = doc_tuple[0]
            content = doc_tuple[1]
            metadata = doc_tuple[2] if len(doc_tuple) > 2 else None
            
            chunks = self.process_document(document_id, content, metadata)
            all_chunks.extend(chunks)
        
        logger.info(f"✓ Processed {len(documents)} documents into {len(all_chunks)} chunks")
        return all_chunks
    
    def merge_chunks(
        self,
        chunks: List[DocumentChunk],
        target_size: int = None,
    ) -> List[DocumentChunk]:
        """
        Merge small chunks with neighbors
        
        Args:
            chunks: List of chunks to merge
            target_size: Target chunk size (uses self.chunk_size if None)
            
        Returns:
            Merged chunks
        """
        target_size = target_size or self.chunk_size
        merged = []
        current_chunk = None
        
        for chunk in chunks:
            if current_chunk is None:
                current_chunk = chunk
            elif len(current_chunk.content) + len(chunk.content) < target_size:
                # Merge with current
                current_chunk.content += "\n" + chunk.content
                current_chunk.token_count += chunk.token_count
            else:
                # Finalize current and start new
                merged.append(current_chunk)
                current_chunk = chunk
        
        if current_chunk is not None:
            merged.append(current_chunk)
        
        logger.debug(f"Merged {len(chunks)} chunks into {len(merged)}")
        return merged
    
    def extract_summary(
        self,
        content: str,
        max_length: int = 200,
    ) -> str:
        """
        Extract summary from document (first sentences/paragraphs)
        
        Args:
            content: Document content
            max_length: Maximum summary length
            
        Returns:
            Summary text
        """
        # Get first paragraph
        paragraphs = content.split("\n\n")
        summary = ""
        
        for para in paragraphs:
            if len(summary) >= max_length:
                break
            summary += para + " "
        
        # Truncate to max length
        if len(summary) > max_length:
            summary = summary[:max_length].rsplit(" ", 1)[0] + "..."
        
        return summary.strip()


class TextCleaner:
    """Clean and normalize text for processing"""
    
    @staticmethod
    def clean(text: str) -> str:
        """
        Clean text by removing extra whitespace and special characters
        
        Args:
            text: Text to clean
            
        Returns:
            Cleaned text
        """
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove control characters
        text = ''.join(char for char in text if not (ord(char) < 32 and char not in '\n\t'))
        
        return text.strip()
    
    @staticmethod
    def remove_headers_footers(text: str) -> str:
        """
        Remove common headers/footers from text
        
        Args:
            text: Text to process
            
        Returns:
            Text with headers/footers removed
        """
        lines = text.split('\n')
        
        # Filter out lines that look like headers/footers
        filtered = []
        for line in lines:
            # Skip page numbers, document names in headers
            if line.strip() and not re.match(r'^(Page|Chapter|Copyright|\d+)', line):
                filtered.append(line)
        
        return '\n'.join(filtered)
    
    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """
        Normalize different types of whitespace
        
        Args:
            text: Text to normalize
            
        Returns:
            Normalized text
        """
        # Replace tabs with spaces
        text = text.replace('\t', '    ')
        
        # Remove multiple spaces
        text = re.sub(r' +', ' ', text)
        
        return text
