"""Constructs and caches language drivers (Python in-process or remote; TS/JS via Bun LSP)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from app.core.parser.drivers.config import (
    load_driver_settings,
    python_file_extensions,
    ts_js_file_extensions,
)
from app.core.parser.drivers.json_rpc_client import JsonRpcLanguageDriver
from app.core.parser.drivers.local_python import LocalPythonDriver
from app.core.parser.drivers.protocol import LanguageDriver

logger = logging.getLogger(__name__)

PYTHON_EXTS = frozenset(python_file_extensions())
TS_JS_EXTS = frozenset(ts_js_file_extensions())
TS_JS_INDEX_FILES = (
    "index.ts",
    "index.tsx",
    "index.js",
    "index.jsx",
    "index.mjs",
    "index.cjs",
    "index.mts",
    "index.cts",
)


class DriverManager:
    """
    One entry point for graph_builder: caches a Python driver and optionally a TS/JS driver.

    Python remote: set ``VNOC_LSP_PYTHON_URL`` to the driver's ``/rpc`` URL.
    Default Python: in-process :class:`LocalPythonDriver` (no HTTP).

    TS/JS: set ``VNOC_LSP_TS_JS_URL`` to the Bun ts_js server (e.g. ``src/lsp/ts_js``) ``/rpc`` URL.
    There is no in-process TS/JS driver in the backend.
    """

    def __init__(self, project_path: Path):
        self._project_path = project_path
        self._python: Optional[LanguageDriver] = None
        self._ts_js: Optional[LanguageDriver] = None

    async def warmup_drivers(self) -> None:
        """Initialize configured drivers so connection errors surface early."""
        await self._ensure_python()
        settings = load_driver_settings()
        if settings.ts_js_rpc_url:
            await self._ensure_ts_js()

    async def get_driver(self, file_path: str) -> LanguageDriver:
        """Return the language driver for ``file_path`` based on its suffix."""
        ext = Path(file_path).suffix.lower()
        if ext in TS_JS_EXTS:
            return await self._ensure_ts_js()
        if ext in PYTHON_EXTS:
            return await self._ensure_python()
        # Unknown extension: default to Python (legacy single-language behavior).
        return await self._ensure_python()

    async def get_driver_for_folder(self, folder_path: str) -> LanguageDriver:
        """
        Choose folder ID injection: ``__init__.py`` (Python) vs ``index.*`` (TS/JS).
        """
        p = Path(folder_path)
        if (p / "__init__.py").is_file():
            return await self._ensure_python()
        if any((p / name).is_file() for name in TS_JS_INDEX_FILES):
            return await self._ensure_ts_js()
        settings = load_driver_settings()
        if settings.ts_js_rpc_url:
            return await self._ensure_ts_js()
        return await self._ensure_python()

    async def _ensure_python(self) -> LanguageDriver:
        if self._python is not None:
            return self._python
        settings = load_driver_settings()
        if settings.python_rpc_url:
            logger.info(
                "Using remote Python LSP driver at %s", settings.python_rpc_url
            )
            client = JsonRpcLanguageDriver(
                settings.python_rpc_url, language="python"
            )
            await client.initialize(str(self._project_path))
            self._python = client
        else:
            logger.debug("Using in-process LocalPythonDriver")
            local = LocalPythonDriver(self._project_path)
            await local.initialize(str(self._project_path))
            self._python = local
        return self._python

    async def _ensure_ts_js(self) -> LanguageDriver:
        if self._ts_js is not None:
            return self._ts_js
        settings = load_driver_settings()
        if not settings.ts_js_rpc_url:
            raise RuntimeError(
                "TS/JS file or folder requires VNOC_LSP_TS_JS_URL "
                "(Bun server from src/lsp/ts_js, POST /rpc)."
            )
        logger.info("Using remote TS/JS LSP driver at %s", settings.ts_js_rpc_url)
        client = JsonRpcLanguageDriver(
            settings.ts_js_rpc_url, language="typescript"
        )
        await client.initialize(str(self._project_path))
        self._ts_js = client
        return self._ts_js

    async def shutdown(self) -> None:
        for name, driver in (("python", self._python), ("ts_js", self._ts_js)):
            if driver is None:
                continue
            try:
                await driver.shutdown()
            except Exception:
                logger.exception("Driver shutdown failed (%s)", name)
        self._python = None
        self._ts_js = None
