"""Integration tests for RAG system (Phase 4)

Tests document processing, search clients, and retrieval.
"""

import pytest
from typing import List

# Document Processing Tests


class TestDocumentProcessor:
    """Document processor integration tests"""
    
    @pytest.mark.asyncio
    async def test_document_chunking(self):
        """Test basic document chunking"""
        from services.document_processor import DocumentProcessor
        
        processor = DocumentProcessor(chunk_size=200, chunk_overlap=50)
        
        content = "This is a test document.\n\nIt has multiple paragraphs.\n\nAnd this is the third paragraph."
        chunks = processor.process_document("doc1", content)
        
        assert len(chunks) > 0
        assert all(chunk.document_id == "doc1" for chunk in chunks)
        assert all(len(chunk.content) > 0 for chunk in chunks)
    
    @pytest.mark.asyncio
    async def test_token_estimation(self):
        """Test token count estimation"""
        from services.document_processor import DocumentProcessor
        
        processor = DocumentProcessor()
        
        text = "This is a sample text to count tokens."
        tokens = processor.estimate_tokens(text)
        
        assert tokens > 0
        assert tokens <= len(text)  # Should be less than character count
    
    @pytest.mark.asyncio
    async def test_chunk_overlap(self):
        """Test chunk overlap functionality"""
        from services.document_processor import DocumentProcessor
        
        processor = DocumentProcessor(chunk_size=100, chunk_overlap=25)
        
        content = (
            "First paragraph with much more content here to ensure it spans multiple chunks. "
            "We need enough text to force the processor to create more than one chunk.\n\n"
            "Second paragraph also with substantial content to test overlap between chunks. "
            "The overlap should include text from the previous chunk boundary.\n\n"
            "Third paragraph continues the pattern with even more words and sentences. "
            "This ensures that chunking and overlap logic is properly exercised.\n\n"
            "Fourth paragraph finalizes the test document with enough characters."
        )
        chunks = processor.process_document("doc2", content)
        
        assert len(chunks) > 1
        # Verify metadata includes document_id
        assert all("document_id" in chunk.metadata for chunk in chunks)
    
    @pytest.mark.asyncio
    async def test_multiple_documents(self):
        """Test processing multiple documents"""
        from services.document_processor import DocumentProcessor
        
        processor = DocumentProcessor()
        
        documents = [
            ("doc1", "First document content here."),
            ("doc2", "Second document content here."),
            ("doc3", "Third document content here."),
        ]
        
        all_chunks = processor.process_documents(documents)
        
        assert len(all_chunks) == 3
        assert all_chunks[0].document_id == "doc1"
        assert all_chunks[1].document_id == "doc2"
        assert all_chunks[2].document_id == "doc3"
    
    @pytest.mark.asyncio
    async def test_text_cleaning(self):
        """Test text cleaning utilities"""
        from services.document_processor import TextCleaner
        
        dirty_text = "This   has   multiple     spaces.\n\n\n\nAnd many newlines."
        clean_text = TextCleaner.clean(dirty_text)
        
        assert "   " not in clean_text
        assert "\n\n\n" not in clean_text
    
    @pytest.mark.asyncio
    async def test_summary_extraction(self):
        """Test extracting summary from document"""
        from services.document_processor import DocumentProcessor
        
        processor = DocumentProcessor()
        
        long_text = "First paragraph with key information.\n\nSecond paragraph with more details.\n\nThird paragraph with additional context."
        summary = processor.extract_summary(long_text, max_length=100)
        
        assert len(summary) <= 110  # Some tolerance for word boundary
        assert "First" in summary or "key" in summary


class TestSearchClients:
    """Search client integration tests"""
    
    @pytest.mark.asyncio
    async def test_search_result_dataclass(self):
        """Test SearchResult dataclass"""
        from integration.search_clients import SearchResult
        
        result = SearchResult(
            title="Test Article",
            url="https://example.com",
            snippet="This is a test snippet.",
            source="web",
            relevance_score=0.85,
            authors=["Author 1", "Author 2"],
            published_date="2024-05-27",
        )
        
        assert result.title == "Test Article"
        assert result.relevance_score == 0.85
        assert len(result.authors) == 2
    
    @pytest.mark.asyncio
    async def test_serper_client_initialization(self):
        """Test Serper client (mocked)"""
        from integration.search_clients import SerperClient
        
        # Note: Requires API key to actually test
        client = SerperClient(api_key="test_key")
        
        assert client.api_key == "test_key"
        assert client.base_url == "https://google.serper.dev"
    
    @pytest.mark.asyncio
    async def test_google_search_client_initialization(self):
        """Test Google Search client"""
        from integration.search_clients import GoogleSearchClient
        
        client = GoogleSearchClient(api_key="test_key", search_engine_id="test_id")
        
        assert client.api_key == "test_key"
        assert client.search_engine_id == "test_id"
    
    @pytest.mark.asyncio
    async def test_semantic_scholar_client_initialization(self):
        """Test Semantic Scholar client"""
        from integration.search_clients import SemanticScholarClient
        
        client = SemanticScholarClient(api_key="optional_key")
        
        assert client.api_key == "optional_key"
        assert "semanticscholar" in client.base_url


class TestSearchService:
    """Search service integration tests"""
    
    @pytest.mark.asyncio
    async def test_search_service_initialization(self):
        """Test search service creation"""
        from services.search_service import SearchService
        
        service = SearchService()
        
        assert service.default_num_results == 10
    
    @pytest.mark.asyncio
    async def test_result_deduplication(self):
        """Test deduplication logic"""
        from services.search_service import SearchService
        from integration.search_clients import SearchResult
        
        service = SearchService()
        
        results = [
            SearchResult("Title 1", "https://example.com", "snippet 1", "web"),
            SearchResult("Title 2", "https://example.com", "snippet 2", "web"),  # Duplicate URL
            SearchResult("Title 3", "https://other.com", "snippet 3", "web"),
        ]
        
        deduplicated = service._deduplicate_results(results)
        
        assert len(deduplicated) == 2
        assert deduplicated[0].url == "https://example.com"
    
    @pytest.mark.asyncio
    async def test_result_ranking(self):
        """Test result ranking by relevance"""
        from services.search_service import SearchService
        from integration.search_clients import SearchResult
        
        service = SearchService()
        
        results = [
            SearchResult("Machine Learning Guide", "https://example.com", "ML guide", "web", 0.5),
            SearchResult("Python Tutorial", "https://other.com", "Python tutorial", "web", 0.3),
            SearchResult("Machine Learning Book", "https://book.com", "ML book", "web", 0.4),
        ]
        
        query = "machine learning"
        ranked = service.rank_results(results, query)
        
        assert ranked[0].title.lower().count("machine") > 0
        assert ranked[0].relevance_score >= ranked[-1].relevance_score


class TestBM25:
    """BM25 retrieval tests"""
    
    @pytest.mark.asyncio
    async def test_bm25_scoring(self):
        """Test BM25 scoring"""
        from services.retrieval_service import BM25Scorer
        
        scorer = BM25Scorer()
        
        documents = [
            "The cat sat on the mat.",
            "The dog ran in the park.",
            "A cat and dog played together.",
        ]
        
        scorer.add_documents(documents)
        
        # Score documents for query
        scores = scorer.rank_documents("cat")
        
        assert len(scores) > 0
        assert scores[0][1] > 0  # Has positive score
    
    @pytest.mark.asyncio
    async def test_bm25_ranking(self):
        """Test BM25 document ranking"""
        from services.retrieval_service import BM25Scorer
        
        scorer = BM25Scorer()
        
        documents = [
            "apple banana cherry",
            "apple apple apple",
            "banana cherry date",
        ]
        
        scorer.add_documents(documents)
        ranked = scorer.rank_documents("apple")
        
        # Document with most "apple" mentions should rank highest
        assert ranked[0][0] == 1  # Index of "apple apple apple"


class TestRetrievalService:
    """Multi-stage retrieval tests"""
    
    @pytest.mark.asyncio
    async def test_retrieval_service_initialization(self):
        """Test retrieval service creation"""
        from services.retrieval_service import RetrievalService
        
        service = RetrievalService(use_bm25=True, use_semantic=True)
        
        assert service.use_bm25
        assert service.use_semantic
    
    @pytest.mark.asyncio
    async def test_bm25_retrieval(self):
        """Test BM25 retrieval"""
        from services.retrieval_service import RetrievalService
        
        service = RetrievalService(use_bm25=True, use_semantic=False)
        
        documents = [
            "The quick brown fox jumps.",
            "A lazy dog sleeps all day.",
            "Foxes are clever animals.",
        ]
        
        results = await service.retrieve(
            query="fox",
            indexed_documents=documents,
            top_k=2,
            use_bm25=True,
            use_semantic=False,
        )
        
        assert len(results) > 0
        assert all(r.relevance_score >= 0 for r in results)
    
    @pytest.mark.asyncio
    async def test_context_formatting(self):
        """Test formatting retrieval results as context"""
        from services.retrieval_service import RetrievalService, RetrievalResult
        
        service = RetrievalService()
        
        results = [
            RetrievalResult(
                content="First source content",
                source="indexed",
                relevance_score=0.95,
                metadata={"title": "Source 1", "url": "https://example.com"},
            ),
            RetrievalResult(
                content="Second source content",
                source="web",
                relevance_score=0.85,
                metadata={"title": "Source 2", "url": "https://other.com"},
            ),
        ]
        
        context = service.format_context(results, max_length=1000)
        
        assert "Retrieved Context" in context
        assert "Source 1" in context or "indexed" in context.lower()
        assert "First source content" in context


class TestDocumentProcessingPipeline:
    """End-to-end document processing pipeline tests"""
    
    @pytest.mark.asyncio
    async def test_full_pipeline(self):
        """Test complete pipeline: document → chunks → retrieval"""
        from services.document_processor import DocumentProcessor
        from services.retrieval_service import RetrievalService
        
        # Process documents
        processor = DocumentProcessor(chunk_size=150, chunk_overlap=30)
        content = "Machine learning is a subset of artificial intelligence. " * 10
        chunks = processor.process_document("doc1", content)
        
        # Create retrieval service
        retriever = RetrievalService(use_bm25=True, use_semantic=False)
        chunk_texts = [chunk.content for chunk in chunks]
        
        # Retrieve
        results = await retriever.retrieve(
            query="machine learning",
            indexed_documents=chunk_texts,
            top_k=3,
            use_bm25=True,
            use_semantic=False,
        )
        
        assert len(results) > 0
        assert all("machine" in r.content.lower() for r in results)


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
