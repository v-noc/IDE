"""
Language driver URLs — read via :func:`app.config.settings.get_settings` so values
from ``.env`` are picked up the same way as other app settings (raw ``os.environ``
does not include entries that only exist in the env file).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from app.config.settings import get_settings


@dataclass(frozen=True)
class DriverSettings:
    """How the backend reaches remote LSP driver processes."""

    # e.g. http://127.0.0.1:9100/rpc — Python LSP (vnoc_lsp_python).
    python_rpc_url: Optional[str] = None
    # e.g. http://127.0.0.1:9200/rpc — Bun ts_js driver (src/lsp/ts_js).
    ts_js_rpc_url: Optional[str] = None


def load_driver_settings() -> DriverSettings:
    s = get_settings()
    py = (s.VNOC_LSP_PYTHON_URL or "").strip() or None
    ts = (s.VNOC_LSP_TS_JS_URL or "").strip() or None
    return DriverSettings(python_rpc_url=py, ts_js_rpc_url=ts)


def python_file_extensions() -> List[str]:
    return [".py"]


def ts_js_file_extensions() -> List[str]:
    return [
        ".ts",
        ".tsx",
        ".js",
        ".jsx",
        ".mjs",
        ".cjs",
        ".mts",
        ".cts",
    ]


def tracked_file_extensions(settings: Optional[DriverSettings] = None) -> List[str]:
    """Extensions scanned on disk: Python always; TS/JS when ``VNOC_LSP_TS_JS_URL`` is set."""
    s = settings or load_driver_settings()
    exts = list(python_file_extensions())
    if s.ts_js_rpc_url:
        exts.extend(ts_js_file_extensions())
    return exts
