from pydantic import BaseModel
from typing import Optional


class ToolCard(BaseModel):
    """Self-describing metadata for a tool (OctoTools-style tool card)."""
    name: str                            # e.g. "graph_search"
    description: str                     # Human-readable purpose
    version: str = "1.0.0"

    # Schema for inputs / outputs
    input_schema: dict                   # JSON-Schema dict for execute() kwargs
    output_type: str                     # Human-readable output type description

    # Usage hints (fed to the planner LLM)
    demo_commands: list[dict] = []       # Example invocations
    limitations: Optional[str] = None
    best_practice: Optional[str] = None

    # Runtime flags
    requires_llm: bool = False           # Does this tool need an LLM engine internally?
    requires_vectorlink: bool = False    # Needs VectorLink client?
    requires_db: bool = False            # Needs TerminusDB client?
