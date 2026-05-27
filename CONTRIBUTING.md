# Contributing to Deep Research Agent

We welcome contributions! This document provides guidelines for contributing.

## Code of Conduct

- Be respectful and inclusive
- Focus on the code, not the person
- Assume good intent
- Report violations to team@example.com

## Getting Started

### Fork & Clone

```bash
git clone https://github.com/your-fork/deep-research-agent.git
cd deep_research_agent
```

### Setup Development Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Run Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_planner.py

# Run with coverage
pytest --cov=src

# Run only fast tests
pytest -m "not slow"
```

## Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

- Write clean, well-documented code
- Follow the existing code style
- Add tests for new functionality
- Update docstrings

### 3. Format Code

```bash
# Format with Black
black src/ tests/

# Sort imports with isort
isort src/ tests/

# Check with Flake8
flake8 src/ tests/

# Type check with mypy
mypy src/
```

### 4. Run Tests

```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# All tests
pytest
```

### 5. Commit Changes

```bash
# Follow conventional commits
git commit -m "feat: add new research agent"
git commit -m "fix: resolve RAG retrieval bug"
git commit -m "docs: update API documentation"
git commit -m "test: add integration tests for Ollama"
```

### 6. Push & Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a PR on GitHub with:
- Clear title and description
- Reference to related issues
- Screenshots if UI changes

## Code Guidelines

### Python Style

- Follow PEP 8
- Use type hints
- Docstrings for all public functions
- Maximum line length: 100 characters

### Example Function

```python
async def retrieve_documents(
    query: ResearchQuery,
    top_k: int = 10,
) -> list[RetrievalResult]:
    """
    Retrieve relevant documents for a research query.
    
    This function performs semantic search using embeddings
    and returns the top K most relevant documents.
    
    Args:
        query: The research query
        top_k: Number of documents to retrieve (default: 10)
        
    Returns:
        List of retrieval results ranked by similarity
        
    Raises:
        RetrievalError: If retrieval fails
    """
    # Implementation
```

### File Organization

```
src/
├── module/
│   ├── __init__.py      # Public API
│   ├── implementation.py # Core logic
│   ├── utils.py         # Helper functions
│   └── types.py         # Type definitions
└── module_test.py       # Tests (in tests/)
```

## Testing

### Unit Tests

- Test single functions/methods
- Mock external dependencies
- Fast execution (< 100ms)

```python
import pytest
from src.agents.planner import PlannerAgent

@pytest.mark.asyncio
async def test_planner_creates_plan():
    planner = PlannerAgent()
    result = await planner.run(query="test query")
    assert result.success
    assert result.data is not None
```

### Integration Tests

- Test component interactions
- Use test databases/services
- Medium execution (< 5s)

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_research_with_ollama():
    # Test actual Ollama integration
```

### End-to-End Tests

- Test full workflows
- Slow but comprehensive
- Run before releases

```python
@pytest.mark.slow
@pytest.mark.asyncio
async def test_full_research_session():
    # Test complete research pipeline
```

## Documentation

### Docstrings

- Use Google style docstrings
- Document all parameters
- Include return types
- Add examples for complex functions

### README Updates

- Document new features
- Update API examples
- Add troubleshooting sections

### API Documentation

- Update OpenAPI schemas
- Document new endpoints
- Add usage examples

## Architecture Guidelines

### Adding New Agents

1. Create class inheriting from `BaseAgent`
2. Implement `execute()` and `validate_inputs()`
3. Add to agent orchestrator
4. Document in architecture.md

### Adding New Retrieval Methods

1. Create class inheriting from `BaseRetriever`
2. Implement `retrieve()` method
3. Add to retrieval factory
4. Add tests

### Adding New Integrations

1. Create module in `src/integration/`
2. Use factory pattern for instantiation
3. Add configuration to `Config`
4. Document usage

## Pull Request Process

1. **Update main branch**: `git pull origin main`
2. **Run full test suite**: `pytest`
3. **Run linters**: `black`, `isort`, `flake8`, `mypy`
4. **Create PR with clear title and description**
5. **Respond to review feedback**
6. **Get approval from maintainers**
7. **Squash and merge**

## Release Process

### Version Numbers

We follow Semantic Versioning (MAJOR.MINOR.PATCH)

- MAJOR: Breaking changes
- MINOR: New features
- PATCH: Bug fixes

### Release Checklist

- [ ] Update version in `pyproject.toml`
- [ ] Update CHANGELOG.md
- [ ] Run full test suite
- [ ] Create GitHub release with notes
- [ ] Publish to PyPI
- [ ] Update documentation

## Performance Guidelines

- Use async/await for I/O operations
- Minimize database queries
- Cache expensive computations
- Profile before optimizing
- Benchmark new implementations

## Security Guidelines

- Never commit secrets or API keys
- Validate all inputs
- Use parameterized queries
- Keep dependencies updated
- Report security issues privately

## Questions?

- **Issues**: Create a GitHub issue
- **Discussions**: Use GitHub Discussions
- **Email**: team@example.com
- **Docs**: Check documentation first

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing! 🙏
