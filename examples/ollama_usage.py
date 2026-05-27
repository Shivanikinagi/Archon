"""
Example: Using Deep Research Agent with Ollama

This example demonstrates how to use the Deep Research Agent with Ollama
for local LLM inference, vector embeddings, and research planning.
"""

import asyncio
from src.core.config import get_config, OllamaConfig
from src.core.types import ResearchQuery, ResearchDepth, SourceType
from src.agents.planner import PlannerAgent
from src.data.embeddings import EmbeddingService
from src.data.chroma_store import ChromaVectorStore
from src.retrieval.rag import RAGRetriever
from src.integration.ollama import OllamaClient
from src.core.logger import setup_logging, get_logger

logger = get_logger(__name__)


async def example_1_check_ollama_connection():
    """Example 1: Check if Ollama is running and list models."""
    print("\n" + "=" * 60)
    print("EXAMPLE 1: Check Ollama Connection")
    print("=" * 60)

    config = get_config()
    client = OllamaClient(config.ollama)

    # Check if running
    is_running = await client.is_running()
    print(f"✓ Ollama running: {is_running}")

    if is_running:
        # List available models
        models = await client.list_models()
        print(f"✓ Available models ({len(models)}):")
        for model in models:
            print(f"  • {model['name']}")


async def example_2_generate_embeddings():
    """Example 2: Generate text embeddings using Ollama."""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Generate Embeddings with Ollama")
    print("=" * 60)

    config = get_config()
    embedding_service = EmbeddingService(
        provider="ollama",
        base_url=config.ollama.base_url,
        model=config.ollama.embedding_model,
    )

    # Generate embeddings for sample texts
    texts = [
        "Artificial intelligence in healthcare",
        "Machine learning for medical diagnosis",
        "Neural networks in drug discovery",
    ]

    embeddings = await embedding_service.embed_texts(texts)

    print(f"✓ Generated {len(embeddings)} embeddings")
    print(f"✓ Embedding dimension: {len(embeddings[0])}")

    for i, text in enumerate(texts):
        print(f"  {i + 1}. '{text}' -> embedding[{len(embeddings[i])}]")


async def example_3_create_research_plan():
    """Example 3: Create a research plan using Planner Agent."""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Create Research Plan")
    print("=" * 60)

    # Create planner agent with Ollama
    planner = PlannerAgent(llm_provider="ollama")

    # Create research query
    query = ResearchQuery(
        query_text="Impact of artificial intelligence in healthcare",
        depth=ResearchDepth.MODERATE,
    )

    print(f"Query: {query.query_text}")
    print(f"Depth: {query.depth.value}")
    print("\nGenerating research plan...\n")

    # Execute planner
    result = await planner.run(query=query)

    if result.success:
        plan = result.data
        print(f"✓ Main Query: {plan.main_query}")
        print(f"✓ Subtopics ({len(plan.subtopics)}):")
        for i, subtopic in enumerate(plan.subtopics, 1):
            print(f"  {i}. {subtopic}")
        print(f"✓ Search Queries ({len(plan.search_queries)}):")
        for i, search_query in enumerate(plan.search_queries, 1):
            print(f"  {i}. {search_query}")
        print(f"✓ Estimated Sources: {plan.estimated_sources}")
        print(f"✓ Estimated Time: {plan.timeline_minutes} minutes")
    else:
        print(f"✗ Error: {result.error}")


async def example_4_setup_rag_retrieval():
    """Example 4: Set up RAG retrieval with ChromaDB and Ollama embeddings."""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Setup RAG Retrieval")
    print("=" * 60)

    config = get_config()

    # Create embedding service
    embedding_service = EmbeddingService(
        provider="ollama",
        base_url=config.ollama.base_url,
        model=config.ollama.embedding_model,
    )

    # Create vector store
    vector_store = ChromaVectorStore(
        persist_dir="./data/chroma_db",
        collection_name="research_documents",
    )

    # Create RAG retriever
    retriever = RAGRetriever(
        vector_store=vector_store,
        embedding_service=embedding_service,
        config=config,
    )

    print("✓ Embedding Service initialized (Ollama)")
    print("✓ Vector Store initialized (ChromaDB)")
    print("✓ RAG Retriever initialized")

    # Example: Retrieve documents
    query = ResearchQuery(
        query_text="AI applications in diagnostics",
        depth=ResearchDepth.MODERATE,
    )

    print(f"\nRetrieving documents for: {query.query_text}")
    results = await retriever.retrieve(query, top_k=5)

    print(f"✓ Retrieved {len(results)} documents")
    for i, result in enumerate(results, 1):
        print(
            f"  {i}. [{result.similarity_score:.3f}] "
            f"{result.chunk.source.title[:50]}..."
        )


async def example_5_llm_generation():
    """Example 5: Generate text using Ollama."""
    print("\n" + "=" * 60)
    print("EXAMPLE 5: Text Generation with Ollama")
    print("=" * 60)

    config = get_config()
    client = OllamaClient(config.ollama)

    # Create a research question
    prompt = """You are a research expert. 
    
Based on this query, create a brief summary of what an effective research plan should cover:

Query: Impact of artificial intelligence in healthcare

Response:"""

    print("Generating response from Ollama...\n")

    try:
        response = await client.generate(prompt, stream=False)
        print(f"✓ Response:\n{response}")
    except Exception as e:
        print(f"✗ Error: {str(e)}")


async def example_6_streaming_generation():
    """Example 6: Streaming text generation from Ollama."""
    print("\n" + "=" * 60)
    print("EXAMPLE 6: Streaming Generation")
    print("=" * 60)

    config = get_config()
    client = OllamaClient(config.ollama)

    prompt = """Write a short research abstract about AI in healthcare:
    
"""

    print("Generating response (streaming)...\n")

    try:
        stream = await client.generate(prompt, stream=True)
        async for chunk in stream:
            print(chunk, end="", flush=True)
        print("\n")
    except Exception as e:
        print(f"✗ Error: {str(e)}")


async def main():
    """Run all examples."""
    setup_logging(log_level="INFO")

    print("\n🚀 Deep Research Agent + Ollama Examples\n")

    try:
        # Example 1: Check Ollama connection
        await example_1_check_ollama_connection()

        # Example 2: Generate embeddings
        await example_2_generate_embeddings()

        # Example 3: Create research plan
        await example_3_create_research_plan()

        # Example 4: Setup RAG retrieval
        # await example_4_setup_rag_retrieval()  # Commented: requires documents in DB

        # Example 5: Text generation
        await example_5_llm_generation()

        # Example 6: Streaming generation
        await example_6_streaming_generation()

        print("\n" + "=" * 60)
        print("✓ All examples completed successfully!")
        print("=" * 60 + "\n")

    except Exception as e:
        logger.error(f"Example failed: {str(e)}")
        print(f"\n✗ Error: {str(e)}\n")


if __name__ == "__main__":
    asyncio.run(main())
