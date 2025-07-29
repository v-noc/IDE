from fastapi import Request
from fastapi.responses import JSONResponse
from loguru import logger

async def generic_exception_handler(request: Request, exc: Exception):
    """
    A generic exception handler for the FastAPI application.
    
    This handler catches any unhandled Exception, logs the error details,
    and returns a standardized JSON response with a 500 status code.
    """
    logger.exception(
        f"Unhandled exception for request {request.method} {request.url}: {exc}"
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred."},
    )
