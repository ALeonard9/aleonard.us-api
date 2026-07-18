"""
This module contains custom exception handlers for FastAPI.
"""

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.status import (
    HTTP_422_UNPROCESSABLE_CONTENT,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from app.log.logging_config import logger
from app.schemas.model_schemas import OutResponseBaseModel


async def http_exception_handler(_: Request, exc: HTTPException):
    """
    Custom handler for HTTPException.

    Forwards ``exc.headers`` — auth challenges (WWW-Authenticate) and rate
    limits (Retry-After) are meaningless without them.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content=OutResponseBaseModel(
            success=False, message=exc.detail, data=[]
        ).model_dump(exclude_none=True),
        headers=getattr(exc, 'headers', None),
    )


async def validation_exception_handler(_: Request, exc: RequestValidationError):
    """
    Custom handler for RequestValidationError.
    """
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_CONTENT,
        content=OutResponseBaseModel(
            success=False, message='Validation Error', data=exc.errors()
        ).model_dump(exclude_none=True),
    )


async def generic_exception_handler(request: Request, exc: Exception):
    """
    Custom handler for generic exceptions.

    Logs the full traceback (severity ERROR) before responding — without this
    a 500 leaves no trace in the logs, so alerting and Error Reporting
    grouping would never see it.
    """
    # scope.get keeps the logging path safe even for malformed/partial scopes
    logger.error(
        'Unhandled exception on %s %s: %s',
        request.scope.get('method', '-'),
        request.scope.get('path', '-'),
        exc,
        exc_info=exc,
    )
    return JSONResponse(
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        content=OutResponseBaseModel(
            success=False, message=str(exc), data=[]
        ).model_dump(exclude_none=True),
    )
