"""
This module contains custom exception handlers for FastAPI.
"""

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.status import (
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from schemas import OutResponseBaseModel


async def http_exception_handler(_: Request, exc: HTTPException):
    """
    Custom handler for HTTPException.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content=OutResponseBaseModel(
            success=False, message=exc.detail, data=[]
        ).model_dump(exclude_none=True),
    )


async def validation_exception_handler(_: Request, exc: RequestValidationError):
    """
    Custom handler for RequestValidationError.
    """
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content=OutResponseBaseModel(
            success=False, message='Validation Error', data=exc.errors()
        ).model_dump(exclude_none=True),
    )


async def generic_exception_handler(_: Request, exc: Exception):
    """
    Custom handler for generic exceptions.
    """
    return JSONResponse(
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        content=OutResponseBaseModel(
            success=False, message=str(exc), data=[]
        ).model_dump(exclude_none=True),
    )
