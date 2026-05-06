from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logger import logger


def _message_from_detail(detail: object) -> str:
    if isinstance(detail, str):
        return detail
    return "Request validation failed"


async def http_exception_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": "http_error",
            "detail": _message_from_detail(exc.detail),
        },
    )


async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    errors = []
    for error in exc.errors():
        item = dict(error)
        if "ctx" in item:
            item["ctx"] = {key: str(value) for key, value in item["ctx"].items()}
        errors.append(item)

    return JSONResponse(
        status_code=422,
        content={
            "code": "validation_error",
            "detail": "Request validation failed",
            "errors": errors,
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled_request_error", path=str(request.url.path), error=str(exc))
    return JSONResponse(
        status_code=500,
        content={
            "code": "internal_server_error",
            "detail": "Internal server error",
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
