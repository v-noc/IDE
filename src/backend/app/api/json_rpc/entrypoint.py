import logging
from contextlib import asynccontextmanager

import fastapi_jsonrpc as jsonrpc
from fastapi import Depends, Body

from .schemas import RegisterLogsBatchParams, RegisterLogsResult
from .dependencies import (
    get_project,
    get_log_service,
)
from .error import (
    CodeElementNotFoundError,
    ProjectNotFoundError,
    FunctionNotFoundError,
)

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
async def register_logs_batch(
    params: RegisterLogsBatchParams = Body(...),
    project=Depends(get_project),
    log_service=Depends(get_log_service),
) -> RegisterLogsResult:

    # For now, simply acknowledge receipt. Integrations can be added later.
    if project is None:
        raise ProjectNotFoundError

    try:

        _ = await log_service.create_batch(params.logs)
    except Exception as ex:
        print(ex)

    return RegisterLogsResult(ok=True)
