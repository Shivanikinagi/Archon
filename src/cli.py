"""
Command-line interface for the Deep Research Agent.
"""

import asyncio
import typer
from typing import Optional
from pathlib import Path

from src.core.config import get_config
from src.core.logger import setup_logging, get_logger
from src.core.types import ResearchDepth, SourceType, CitationStyle
from src.agents.planner import PlannerAgent

logger = get_logger(__name__)

app = typer.Typer(
    name="deep-research-agent",
    help="Production-grade autonomous research platform",
)


@app.command()
def research(
    query: str = typer.Argument(..., help="Research query"),
    depth: str = typer.Option(
        "moderate",
        help="Research depth: shallow, moderate, deep, exhaustive",
    ),
    sources: str = typer.Option(
        "web,academic",
        help="Source types: web, academic, news, docs, books, uploaded",
    ),
    output: Optional[str] = typer.Option(
        None,
        help="Output file path for report",
    ),
    max_results: int = typer.Option(
        50,
        help="Maximum number of results",
    ),
):
    """Start a research session."""
    try:
        config = get_config()
        setup_logging(
            log_level=config.logging.level,
            log_file=config.logging.file,
        )

        typer.echo("🔬 Starting research session...")

        # Validate depth
        try:
            research_depth = ResearchDepth(depth)
        except ValueError:
            typer.echo(
                typer.style(
                    f"❌ Invalid depth: {depth}. Must be one of: "
                    f"shallow, moderate, deep, exhaustive",
                    fg=typer.colors.RED,
                ),
            )
            raise typer.Exit(1)

        # Create research plan
        planner = PlannerAgent(
            llm_provider="ollama" if config.ollama.enabled else "openai"
        )

        typer.echo(f"📋 Creating research plan for: {query}")

        # Run async function
        result = asyncio.run(
            planner.run(query=query, depth=research_depth)
        )

        if result.success:
            plan = result.data
            typer.echo(typer.style("✓ Research plan created!", fg=typer.colors.GREEN))
            typer.echo(f"\n📑 Main Query: {plan.main_query}")
            typer.echo(f"🎯 Subtopics ({len(plan.subtopics)}):")
            for i, subtopic in enumerate(plan.subtopics, 1):
                typer.echo(f"  {i}. {subtopic}")
            typer.echo(f"\n⏱️ Estimated time: {plan.timeline_minutes} minutes")
            typer.echo(f"📊 Estimated sources: {plan.estimated_sources}")
        else:
            typer.echo(typer.style(f"❌ Error: {result.error}", fg=typer.colors.RED))
            raise typer.Exit(1)

    except Exception as e:
        logger.error(f"Research command failed: {str(e)}")
        typer.echo(typer.style(f"❌ Error: {str(e)}", fg=typer.colors.RED))
        raise typer.Exit(1)


@app.command()
def ollama_status():
    """Check Ollama service status."""
    try:
        config = get_config()
        setup_logging(log_level=config.logging.level)

        if not config.ollama.enabled:
            typer.echo(
                typer.style("⚠️ Ollama is not enabled in configuration", fg=typer.colors.YELLOW)
            )
            raise typer.Exit(1)

        from src.integration.ollama import OllamaClient

        client = OllamaClient(config.ollama)

        typer.echo("🔍 Checking Ollama service...")

        is_running = asyncio.run(client.is_running())

        if is_running:
            typer.echo(typer.style("✓ Ollama is running!", fg=typer.colors.GREEN))

            # List available models
            models = asyncio.run(client.list_models())
            typer.echo(f"\n📦 Available models ({len(models)}):")
            for model in models:
                typer.echo(f"  • {model['name']}")
        else:
            typer.echo(
                typer.style(
                    f"❌ Ollama not accessible at {config.ollama.base_url}",
                    fg=typer.colors.RED,
                )
            )
            raise typer.Exit(1)

    except Exception as e:
        logger.error(f"Ollama status check failed: {str(e)}")
        typer.echo(typer.style(f"❌ Error: {str(e)}", fg=typer.colors.RED))
        raise typer.Exit(1)


@app.command()
def config_show():
    """Display current configuration."""
    try:
        config = get_config()

        typer.echo("⚙️  Configuration:\n")
        typer.echo(f"Environment: {config.environment}")
        typer.echo(f"Debug: {config.debug}\n")

        typer.echo("LLM Configuration:")
        typer.echo(f"  Provider: {config.llm.provider}")
        typer.echo(f"  Model: {config.llm.model}\n")

        typer.echo("Ollama Configuration:")
        typer.echo(f"  Enabled: {config.ollama.enabled}")
        typer.echo(f"  Base URL: {config.ollama.base_url}")
        typer.echo(f"  Model: {config.ollama.model}")
        typer.echo(f"  Embedding Model: {config.ollama.embedding_model}\n")

        typer.echo("Vector Store Configuration:")
        typer.echo(f"  Backend: {config.vector_store.backend}")
        typer.echo(f"  Collection: {config.vector_store.collection_name}\n")

        typer.echo("API Configuration:")
        typer.echo(f"  Host: {config.api.host}:{config.api.port}\n")

    except Exception as e:
        logger.error(f"Config show failed: {str(e)}")
        typer.echo(typer.style(f"❌ Error: {str(e)}", fg=typer.colors.RED))
        raise typer.Exit(1)


@app.command()
def api_run(
    host: str = typer.Option("0.0.0.0", help="API host"),
    port: int = typer.Option(8000, help="API port"),
    workers: int = typer.Option(1, help="Number of workers"),
    reload: bool = typer.Option(False, help="Auto-reload on changes"),
):
    """Run the API server."""
    try:
        import uvicorn

        typer.echo("🚀 Starting API server...")
        typer.echo(f"📍 Listening on http://{host}:{port}")
        typer.echo("📚 Docs available at http://localhost:8000/docs\n")

        uvicorn.run(
            "src.api.server:app",
            host=host,
            port=port,
            workers=workers,
            reload=reload,
        )

    except Exception as e:
        logger.error(f"API server failed: {str(e)}")
        typer.echo(typer.style(f"❌ Error: {str(e)}", fg=typer.colors.RED))
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
