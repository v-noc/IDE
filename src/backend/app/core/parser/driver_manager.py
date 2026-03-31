"""Constructs and caches the Python language driver for a project workspace."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from app.core.parser.driver_client import JsonRpcLanguageDriver
from app.core.parser.driver_config import load_python_driver_settings
from app.core.parser.driver_local import LocalPythonDriver
from app.core.parser.driver_protocol import LanguageDriver

logger = logging.getLogger(__name__)


class DriverManager:
    """
    Single entry point for graph_builder: one Python driver per orchestrator run.
    Remote mode: set VNOC_LSP_PYTHON_URL to the driver's /rpc URL.
    Default: in-process LocalPythonDriver (no HTTP).
    """

    def __init__(self, project_path: Path):
        self._project_path = project_path
        self._driver: Optional[LanguageDriver] = None
        self._owns_remote_client = False

    async def get_driver(self) -> LanguageDriver:
        if self._driver is not None:
            return self._driver
        settings = load_python_driver_settings()

        if settings.rpc_url:
            logger.info("Using remote Python LSP driver at %s",
                        settings.rpc_url)
            client = JsonRpcLanguageDriver(settings.rpc_url)
            await client.initialize(str(self._project_path))
            self._driver = client
            self._owns_remote_client = True
        else:
            logger.debug("Using in-process LocalPythonDriver")
            local = LocalPythonDriver(self._project_path)
            await local.initialize(str(self._project_path))
            self._driver = local
            self._owns_remote_client = False

        return self._driver

    async def shutdown(self) -> None:
        if self._driver is None:
            return
        try:
            await self._driver.shutdown()
        except Exception:
            logger.exception("Driver shutdown failed")
        if self._owns_remote_client and isinstance(
            self._driver, JsonRpcLanguageDriver
        ):
            await self._driver.aclose()
        self._driver = None
