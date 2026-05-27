# Deep Research Agent 🔬

A production-grade autonomous research platform that combines RAG (Retrieval-Augmented Generation) and GraphRAG technologies to understand queries, create research plans, gather information from multiple sources, verify claims, and generate comprehensive research reports with citations.

## 🎯 Key Features

### Core Capabilities
- **Multi-Source Research**: Web search, research papers, uploaded documents
- **Intelligent Planning**: Automatic research plan generation with subtopic breakdown
- **Hybrid Retrieval**: RAG + GraphRAG for comprehensive information gathering
- **Knowledge Graph**: Build and query knowledge graphs for semantic relationships
- **Fact Verification**: Multi-step claim verification and validation
- **Citation Management**: Automatic citation generation with source tracking
- **Report Generation**: Professional research reports with formatting and structure

### Technical Highlights
- **Modular Architecture**: Cleanly separated layers (Core, Data, Agents, Retrieval, Integration, API)
- **Multi-Agent System**: Specialized agents (Planner, Searcher, Writer, Fact Checker, Reviewer)
- **Scalable Storage**: Support for multiple vector DBs (ChromaDB, Pinecone, Weaviate)
- **Knowledge Graphs**: Neo4j/PostgreSQL backends for graph-based reasoning
- **Production APIs**: FastAPI with async/await, comprehensive error handling
- **Enterprise Ready**: Logging, monitoring, configuration management, security

## 📋 System Architecture

```
┌─────────────────────┐
│   User Research     │
│      Query          │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Planner Agent      │ ← Creates research plan & subtopics
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│  Parallel Research Agents               │
│  ├─ Web Search Agent                    │
│  ├─ Research Papers Agent               │
│  └─ Document Search Agent               │
└──────────┬──────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│  Document Processing Pipeline           │
│  ├─ Text Extraction                     │
│  ├─ Chunking                            │
│  └─ Embedding Generation                │
└──────────┬──────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│  Storage Layer                          │
│  ├─ Vector Database (ChromaDB/Pinecone) │
│  └─ Knowledge Graph (Neo4j/Postgres)    │
└──────────┬──────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│  Hybrid Retrieval Layer                 │
│  ├─ RAG Retriever                       │
│  ├─ GraphRAG Retriever                  │
│  └─ Fusion Engine                       │
└──────────┬──────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│  Multi-Agent Report Generation          │
│  ├─ Writer Agent                        │
│  ├─ Fact Checker Agent                  │
│  └─ Reviewer Agent                      │
└──────────┬──────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────┐
│  Citation Generator & Report Formatter   │
└──────────┬───────────────────────────────┘
           │
           ▼
┌──────────────────────────────┐
│  Final Research Report       │
│  (with citations & metadata) │
└──────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- pip or Poetry
- OpenAI API key (or alternative LLM provider)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/your-org/deep-research-agent.git
cd deep_research_agent
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -e ".[dev]"
```

4. **Setup environment**
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

5. **Run migrations**
```bash
python -m src.cli migrate
```

### Basic Usage

**Via CLI:**
```bash
# Start a research session
python -m src.cli research "Impact of AI in Healthcare"

# With options
python -m src.cli research "Impact of AI in Healthcare" \
  --depth deep \
  --sources web,papers,documents \
  --max-results 50 \
  --output report.md
```

**Via Python API:**
```python
from src.core import ResearchSession
from src.agents import PlannerAgent

session = ResearchSession()
planner = PlannerAgent()

# Create research plan
plan = planner.create_plan("Impact of AI in Healthcare")

# Execute research
results = session.research(plan)

# Generate report
report = session.generate_report(results)
print(report)
```

**Via REST API:**
```bash
# Start API server
python -m src.api.server

# Make research request
curl -X POST http://localhost:8000/api/v1/research \
  -H "Content-Type: application/json" \
  -d '{"query": "Impact of AI in Healthcare", "depth": "deep"}'
```

## 📁 Project Structure

```
deep_research_agent/
├── src/
│   ├── core/                 # Core abstractions & interfaces
│   │   ├── __init__.py
│   │   ├── types.py          # Type definitions & enums
│   │   ├── base.py           # Base classes
│   │   ├── config.py         # Configuration management
│   │   ├── logger.py         # Logging setup
│   │   └── exceptions.py     # Custom exceptions
│   │
│   ├── data/                 # Data layer & storage
│   │   ├── __init__.py
│   │   ├── models.py         # Database models
│   │   ├── vector_store.py   # Vector store interface
│   │   ├── graph_store.py    # Graph database interface
│   │   ├── document_store.py # Document storage
│   │   ├── embeddings.py     # Embedding service
│   │   └── repositories.py   # Data access layer
│   │
│   ├── agents/               # Autonomous agents
│   │   ├── __init__.py
│   │   ├── base.py           # Base agent class
│   │   ├── planner.py        # Research planner agent
│   │   ├── searcher.py       # Multi-source searcher
│   │   ├── writer.py         # Report writer agent
│   │   ├── fact_checker.py   # Fact verification agent
│   │   ├── reviewer.py       # Report review agent
│   │   └── orchestrator.py   # Agent orchestration
│   │
│   ├── retrieval/            # Retrieval engines
│   │   ├── __init__.py
│   │   ├── rag.py            # RAG retriever
│   │   ├── graphrag.py       # GraphRAG retriever
│   │   ├── fusion.py         # Result fusion
│   │   └── reranker.py       # Result reranking
│   │
│   ├── integration/          # External integrations
│   │   ├── __init__.py
│   │   ├── llm_provider.py   # LLM API abstraction
│   │   ├── search_api.py     # Web search APIs
│   │   ├── doc_processor.py  # Document processing
│   │   └── citation_engine.py # Citation generation
│   │
│   ├── api/                  # REST API layer
│   │   ├── __init__.py
│   │   ├── server.py         # FastAPI app
│   │   ├── routes.py         # API endpoints
│   │   ├── schemas.py        # Pydantic models
│   │   └── middleware.py     # Custom middleware
│   │
│   ├── cli.py                # Command-line interface
│   └── main.py               # Entry point
│
├── config/
│   ├── config.yaml           # Main configuration
│   ├── logging.yaml          # Logging configuration
│   └── agents.yaml           # Agent configurations
│
├── tests/
│   ├── unit/                 # Unit tests
│   ├── integration/          # Integration tests
│   └── fixtures/             # Test data & mocks
│
├── docs/
│   ├── architecture.md       # Architecture documentation
│   ├── api.md                # API documentation
│   ├── development.md        # Development guide
│   └── deployment.md         # Deployment guide
│
├── pyproject.toml            # Project metadata & dependencies
├── .env.example              # Environment template
├── README.md                 # This file
└── CONTRIBUTING.md           # Contribution guidelines
```

## 🏗️ Architecture Overview

### Layer Breakdown

#### 1. **Core Layer** (`src/core/`)
- Type definitions and enums
- Base classes and interfaces
- Configuration management
- Logging infrastructure
- Custom exceptions

#### 2. **Data Layer** (`src/data/`)
- Vector store abstraction (ChromaDB, Pinecone, Weaviate)
- Knowledge graph backends (Neo4j, PostgreSQL)
- Document storage and retrieval
- Embedding service
- Data access repositories

#### 3. **Agent Layer** (`src/agents/`)
- **Planner**: Creates research plans and identifies subtopics
- **Searcher**: Parallel agents for web/papers/documents
- **Writer**: Generates research report drafts
- **Fact Checker**: Verifies claims and evidence
- **Reviewer**: Quality checks and refinement
- **Orchestrator**: Coordinates agent workflows

#### 4. **Retrieval Layer** (`src/retrieval/`)
- RAG retriever with vector similarity search
- GraphRAG for semantic relationship traversal
- Result fusion and ranking
- Reranking for improved relevance

#### 5. **Integration Layer** (`src/integration/`)
- LLM provider abstraction (OpenAI, Anthropic, Google, Cohere)
- Web search APIs (Google, Serper, Brave)
- Document processors (PDF, DOCX, Markdown)
- Citation engine (APA, MLA, Chicago)

#### 6. **API Layer** (`src/api/`)
- FastAPI application with async/await
- RESTful endpoints for research operations
- WebSocket support for streaming
- Authentication and rate limiting
- Comprehensive error handling

## 🔧 Configuration

All configuration is managed through:
1. **Environment variables** (`.env`)
2. **YAML files** (`config/`)
3. **Python dataclasses** (typed config objects)

See [Configuration Guide](docs/configuration.md) for details.

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test suite
pytest tests/unit/
pytest tests/integration/

# Run with markers
pytest -m "not slow"
```

## 📚 Documentation

- [Architecture Guide](docs/architecture.md)
- [API Documentation](docs/api.md)
- [Development Guide](docs/development.md)
- [Deployment Guide](docs/deployment.md)
- [Contributing Guidelines](CONTRIBUTING.md)

## 🔐 Security

- API key management via environment variables
- Request validation and sanitization
- Rate limiting and throttling
- Audit logging for all operations
- CORS and CSRF protection

## 📊 Performance

- Parallel research execution
- Async/await for I/O operations
- Caching of embeddings and graphs
- Batch processing of documents
- Result reranking for relevance

## 🚢 Deployment

Supported deployment platforms:
- Docker / Docker Compose
- Kubernetes
- AWS (Lambda, ECS, SageMaker)
- Google Cloud (Cloud Run, Vertex AI)
- Azure (Functions, App Service)

See [Deployment Guide](docs/deployment.md) for detailed instructions.

## 📝 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📧 Support

- **Issues**: [GitHub Issues](https://github.com/your-org/deep-research-agent/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/deep-research-agent/discussions)
- **Email**: team@example.com

## 🙏 Acknowledgments

Built with inspiration from:
- OpenAI Deep Research
- Perplexity Research Mode
- Enterprise Research Copilots

---

**Made with ❤️ by the Research Agent Team**
