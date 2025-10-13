import logging
from contextlib import asynccontextmanager

import fastapi_jsonrpc as jsonrpc
from fastapi import Depends, Body

from .schemas import RegisterLogsParams, RegisterLogsResult
from .dependencies import get_project, get_element_services
from .error import CodeElementNotFoundError

logger = logging.getLogger(__name__)


@asynccontextmanager
async def logging_middleware(ctx: jsonrpc.JsonRpcContext):
    logger.info("Request: %r", ctx.raw_request)
    try:
        yield
    finally:
        logger.info("Response: %r", ctx.raw_response)


common_errors = [CodeElementNotFoundError]
common_errors.extend(jsonrpc.Entrypoint.default_errors)


api_v1_logs = jsonrpc.Entrypoint(
    "/api/v1/jsonrpc",
    errors=common_errors,
    middlewares=[logging_middleware],
)


@api_v1_logs.method()
def register_logs(
    params: RegisterLogsParams = Body(...),
    project=Depends(get_project),
    element_services=Depends(get_element_services),
) -> RegisterLogsResult:
    file_service, class_service, function_service, call_service = element_services

    element_id = params.element_id

    # Resolve by key across node types
    node = (
        file_service.repos.node_repo.get_raw_by_key(element_id)
        if hasattr(file_service.repos, "node_repo")
        else None
    )
    if not node:
        # Fallback using existing API logic (code endpoint uses node_repo)
        try:
            node = file_service.repos.nodes.get_raw_by_key(element_id)
        except Exception:
            node = None

    if not node:
        raise CodeElementNotFoundError

    # For now, just acknowledge; later we will record structured logs
    return RegisterLogsResult(ok=True)
