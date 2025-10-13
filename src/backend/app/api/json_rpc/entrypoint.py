import logging
from contextlib import asynccontextmanager

import fastapi_jsonrpc as jsonrpc
from fastapi import Depends, Body

from .schemas import RegisterLogsParams, RegisterLogsResult
from .dependencies import get_function, get_project, get_parent_function, get_log_service
from .error import CodeElementNotFoundError, ProjectNotFoundError, FunctionNotFoundError

logger = logging.getLogger(__name__)


@asynccontextmanager
async def logging_middleware(ctx: jsonrpc.JsonRpcContext):
    logger.info("Request: %r", ctx.raw_request)
    try:
        yield
    finally:
        logger.info("Response: %r", ctx.raw_response)


common_errors = [CodeElementNotFoundError,
                 ProjectNotFoundError, FunctionNotFoundError]
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
    parent_function=Depends(get_parent_function),
    function=Depends(get_function),
    log_service=Depends(get_log_service),
) -> RegisterLogsResult:

    # For now, simply acknowledge receipt. Integrations can be added later.

    if project is None:
        raise ProjectNotFoundError
    if function is None:
        raise FunctionNotFoundError

    # Persist log and edges (derive parent via parent_function + chain_id)
    parent_function_id = parent_function.id if parent_function else None
    log_service.create(function.id, params, parent_function_id)

    return RegisterLogsResult(ok=True)
