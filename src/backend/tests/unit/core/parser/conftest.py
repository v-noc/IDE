# src/backend/tests/unit/core/parser/conftest.py
import pytest
import os
from pathlib import Path
from app.db import collections

@pytest.fixture(scope="function")
def clear_db():
    """Fixture to clear all node and edge collections before and after a test."""
    collections.nodes.truncate()
    collections.belongs_to_edges.truncate()
    collections.contains_edges.truncate()
    collections.calls_edges.truncate()
    collections.uses_import_edges.truncate()
    collections.implements_edges.truncate()
    yield
    collections.nodes.truncate()
    collections.belongs_to_edges.truncate()
    collections.contains_edges.truncate()
    collections.calls_edges.truncate()
    collections.uses_import_edges.truncate()
    collections.implements_edges.truncate()

@pytest.fixture(scope="session")
def sample_project_path() -> str:
    """Provides the path to the sample project directory."""
    return os.path.join(os.path.dirname(__file__), "sample_project")
