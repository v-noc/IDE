"""
Registry and environment-driven settings for language drivers.

Only the Python driver is implemented; JS/TS will add another entry later.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class PythonDriverSettings:
    """How the backend reaches the Python LSP process."""

    # If set, connect to this JSON-RPC URL (e.g. http://127.0.0.1:9100/rpc).
    rpc_url: Optional[str] = None


def load_python_driver_settings() -> PythonDriverSettings:
    url = os.environ.get("VNOC_LSP_PYTHON_URL", "").strip() or None
    return PythonDriverSettings(rpc_url=url)


def python_file_extensions() -> List[str]:
    return [".py"]
