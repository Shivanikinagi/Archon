"""
Prometheus metrics and monitoring utilities.
"""

from prometheus_client import Counter, Histogram, Gauge, Info
from functools import wraps
import time

# Application info
app_info = Info("research_agent", "Deep Research Agent application info")

# Request metrics
request_count = Counter(
    "research_agent_requests_total",
    "Total requests",
    ["method", "endpoint", "status"]
)

request_duration = Histogram(
    "research_agent_request_duration_seconds",
    "Request duration in seconds",
    ["method", "endpoint"]
)

# Research metrics
research_sessions = Counter(
    "research_agent_sessions_total",
    "Total research sessions",
    ["status", "depth"]
)

research_duration = Histogram(
    "research_agent_research_duration_seconds",
    "Research session duration"
)

# LLM metrics
llm_requests = Counter(
    "research_agent_llm_requests_total",
    "Total LLM requests",
    ["model", "status"]
)

llm_tokens = Counter(
    "research_agent_llm_tokens_total",
    "Total LLM tokens used",
    ["model", "type"]
)

# Vector store metrics
vector_search_duration = Histogram(
    "research_agent_vector_search_duration_seconds",
    "Vector search duration"
)

# Graph metrics
graph_query_duration = Histogram(
    "research_agent_graph_query_duration_seconds",
    "Graph query duration"
)

# Active sessions gauge
active_sessions = Gauge(
    "research_agent_active_sessions",
    "Number of active research sessions"
)


def track_request(func):
    """Decorator to track request metrics."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        try:
            result = await func(*args, **kwargs)
            status = "success"
            return result
        except Exception:
            status = "error"
            raise
        finally:
            duration = time.time() - start
            # Note: endpoint info would need to be extracted from request context
    return wrapper


def track_research(func):
    """Decorator to track research session metrics."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        active_sessions.inc()
        start = time.time()
        try:
            result = await func(*args, **kwargs)
            research_sessions.labels(status="completed", depth="unknown").inc()
            return result
        except Exception:
            research_sessions.labels(status="failed", depth="unknown").inc()
            raise
        finally:
            research_duration.observe(time.time() - start)
            active_sessions.dec()
    return wrapper
