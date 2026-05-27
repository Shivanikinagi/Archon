"""
Main API router aggregator.

NOTE: This module dynamically loads route submodules from the routes/
directory to avoid namespace conflicts between api/routes.py (this file)
and api/routes/ (the package directory). Both exist per project requirements.
"""

import sys
import importlib.util
from pathlib import Path
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1")


def _load_route_module(name: str):
    """Load a route module from the routes/ directory and register it."""
    module_name = f"api.routes.{name}"
    if module_name in sys.modules:
        return sys.modules[module_name]
    file_path = Path(__file__).parent / "routes" / f"{name}.py"
    if not file_path.exists():
        raise FileNotFoundError(f"Route module not found: {file_path}")
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


# Load and include all route modules
_route_names = ["auth", "research", "reports", "documents", "graphs", "admin"]
for _name in _route_names:
    _mod = _load_route_module(_name)
    if hasattr(_mod, "router"):
        router.include_router(_mod.router)
