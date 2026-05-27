# Quick Reference Guide

## Installation

```bash
# 1. Start Ollama
ollama serve

# 2. Pull models (in another terminal)
ollama pull mistral
ollama pull nomic-embed-text

# 3. Install Deep Research Agent
git clone <repo>
cd deep_research_agent
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"

# 4. Configure
cp .env.example .env
# Edit .env and set OLLAMA_ENABLED=true

# 5. Verify setup
python -m src.cli ollama-status
```

## CLI Commands

### Research

```bash
# Basic research
python -m src.cli research "Your query"

# With options
python -m src.cli research "Your query" \
  --depth deep \
  --sources web,academic \
  --max-results 50 \
  --output report.md
```

### Ollama

```bash
# Check status
python -m src.cli ollama-status

# Show configuration
python -m src.cli config-show
```

### API

```bash
# Run API server
python -m src.cli api-run

# With options
python -m src.cli api-run \
  --host 0.0.0.0 \
  --port 8000 \
  --reload
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/research` | Start research session |
| GET | `/api/v1/research/{id}` | Get session status |
| GET | `/api/v1/research/{id}/report` | Get research report |
| DELETE | `/api/v1/research/{id}` | Cancel session |
| GET | `/api/v1/health` | Health check |

## Python API

### Research Plan

```python
from src.agents.planner import PlannerAgent
from src.core.types import ResearchDepth

planner = PlannerAgent(llm_provider="ollama")
result = await planner.run(
    query="Your query",
    depth=ResearchDepth.MODERATE
)
```

### Embeddings

```python
from src.data.embeddings import EmbeddingService

service = EmbeddingService(provider="ollama")
embedding = await service.embed_text("Your text")
```

### RAG Retrieval

```python
from src.retrieval.rag import RAGRetriever

retriever = RAGRetriever(vector_store, embedding_service)
results = await retriever.retrieve(query, top_k=10)
```

## Docker

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f api

# Stop
docker-compose down

# Pull Ollama models
docker exec ollama ollama pull mistral
```

## Configuration

### Ollama Settings

```env
OLLAMA_ENABLED=true
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
OLLAMA_TEMPERATURE=0.7
OLLAMA_TIMEOUT=300
```

### Vector Store

```env
# ChromaDB (local)
CHROMA_PERSIST_DIR=./data/chroma_db

# Or Pinecone (cloud)
PINECONE_API_KEY=<key>
PINECONE_INDEX_NAME=research-documents
```

### Knowledge Graph

```env
# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password
```

## Troubleshooting

### Ollama Connection Error

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Check configuration
python -m src.cli config-show

# Restart Ollama
ollama serve
```

### Model Not Found

```bash
# List available models
ollama list

# Pull missing model
ollama pull mistral

# Verify in config
OLLAMA_MODEL=mistral
```

### High Memory Usage

- Use smaller model: `neural-chat` instead of `mistral`
- Reduce chunk size in `.env`
- Enable GPU acceleration

## Performance Tips

1. Use Mistral model - good balance of speed/quality
2. Enable GPU in Ollama
3. Adjust top_k and similarity_threshold in config
4. Use caching for repeated queries
5. Monitor resource usage: `docker stats`

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test
pytest tests/unit/test_planner.py -v

# Run only fast tests
pytest -m "not slow"
```

## Debugging

```bash
# Enable debug logging
LOG_LEVEL=DEBUG python -m src.cli api-run

# Check Ollama logs
docker logs -f ollama

# Monitor resources
docker stats
```

## Database

### ChromaDB

```python
from src.data.chroma_store import ChromaVectorStore

store = ChromaVectorStore(
    persist_dir="./data/chroma_db",
    collection_name="research_documents"
)
```

### Neo4j

```python
from src.data.neo4j_store import Neo4jGraphStore

store = Neo4jGraphStore(
    uri="bolt://localhost:7687",
    username="neo4j",
    password="password"
)
```

## Examples

See `examples/` directory:
- `ollama_usage.py` - Ollama integration examples
- `research_session.py` - Full research workflow
- `rag_retrieval.py` - RAG setup and usage

## Documentation

- [OLLAMA_GUIDE.md](docs/OLLAMA_GUIDE.md) - Ollama setup guide
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - System architecture
- [DEPLOYMENT.md](docs/DEPLOYMENT.md) - Deployment guide
- [README.md](README.md) - Project overview

## Common Tasks

### Add Document to Vector Store

```python
from src.data.embeddings import EmbeddingService
from src.integration.doc_processor import DocumentProcessorFactory

# Process document
processor = DocumentProcessorFactory.create_processor("path/to/file.pdf")
chunks = await processor.extract_chunks("path/to/file.pdf")

# Add embeddings
embedding_service = EmbeddingService("ollama")
for chunk in chunks:
    chunk.embedding = await embedding_service.embed_text(chunk.content)

# Store
await vector_store.add_documents(chunks)
```

### Generate Report

```python
from src.integration.citation_engine import CitationGenerator
from src.core.types import CitationStyle

# Generate citations
citations = [
    CitationGenerator.generate(source, CitationStyle.APA)
    for source in sources
]

# Create report
report = f"""# Research Report

{content}

## References

{chr(10).join(c.formatted_text for c in citations)}
"""
```

## Support

- GitHub Issues: Report bugs
- GitHub Discussions: Ask questions
- Docs: Check documentation first
- Email: team@example.com

---

**Happy researching!** 🚀
